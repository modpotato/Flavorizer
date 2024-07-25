import discord
from discord import app_commands
import asyncio
import os
import pathlib
import demucs.api
import zipfile
from mutagen.mp3 import MP3

@app_commands.command()
@app_commands.describe(audio="The audio file to split into stems")
async def split_audio(interaction: discord.Interaction, audio: discord.Attachment):
    print(f"Received split_audio command from {interaction.user.name} with file: {audio.filename}")
    await interaction.response.defer()

    if not audio.filename.lower().endswith('.mp3'):
        print(f"Invalid file type from {interaction.user.name}: {audio.filename}")
        await interaction.followup.send("Please attach an MP3 file.")
        return

    # Check file size (10 MB limit)
    if audio.size > 10 * 1024 * 1024:  # 10 MB in bytes
        print(f"File too large from {interaction.user.name}: {audio.filename} ({audio.size} bytes)")
        await interaction.followup.send("The audio file must be smaller than 10 MB.")
        return

    # Create the output directory if it doesn't exist
    output_dir = "./data/split_audio"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Download the audio file
    input_path = os.path.join(output_dir, audio.filename)
    await audio.save(input_path)
    
    print(f"Downloaded input file for {interaction.user.name}: {audio.filename}")

    # Check audio duration (4 minutes limit)
    try:
        audio = MP3(input_path)
        duration = audio.info.length
        if duration > 240:  # 4 minutes in seconds
            print(f"Audio too long from {interaction.user.name}: {audio.filename} ({duration} seconds)")
            await interaction.followup.send("The audio file must be shorter than 4 minutes.")
            os.remove(input_path)
            return
    except Exception as e:
        print(f"Error checking audio duration: {str(e)}")
        await interaction.followup.send("An error occurred while processing the audio file.")
        os.remove(input_path)
        return

    try:
        # Initialize the Separator
        separator = demucs.api.Separator(model="mdx_extra", segment=12)

        # Separate the audio file
        print(f"Starting audio splitting for {interaction.user.name}'s file: {audio.filename}")
        origin, separated = await asyncio.to_thread(separator.separate_audio_file, input_path)

        # Save all separated stems
        stem_files = {}
        for stem_name in separated.keys():
            stem_file = os.path.join(output_dir, f"{stem_name}.mp3")
            await asyncio.to_thread(demucs.api.save_audio, separated[stem_name], stem_file, samplerate=separator.samplerate)
            stem_files[stem_name] = stem_file

        # Create a zip file containing all stems
        zip_file_path = os.path.join(output_dir, "separated_stems.zip")
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for stem_name, stem_file in stem_files.items():
                zipf.write(stem_file, f"{stem_name}.mp3")

        # Send the zip file
        await interaction.followup.send("Audio split successfully. Here are the separated stems:")
        await interaction.followup.send(file=discord.File(zip_file_path, filename="separated_stems.zip"))

    except Exception as e:
        print(f"Error processing {interaction.user.name}'s file {audio.filename}: {str(e)}")
        await interaction.followup.send(f"An error occurred: {str(e)}")

    finally:
        # Clean up input, output, and zip files
        os.remove(input_path)
        for stem_file in stem_files.values():
            if os.path.exists(stem_file):
                os.remove(stem_file)
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)