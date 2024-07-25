import discord
from discord import app_commands
import asyncio
import tempfile
import os
import private
import pathlib

# Create the output directory if it doesn't exist
pathlib.Path("./data/flavorized").mkdir(parents=True, exist_ok=True)

class InterpolateClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync commands to a specific server
        guild = discord.Object(id=1158539552911274014)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = InterpolateClient()

@client.tree.command()
@app_commands.describe(video="The video file to flavorize")
async def flavorize(interaction: discord.Interaction, video: discord.Attachment):
    print(f"Received flavorize command from {interaction.user.name} with file: {video.filename}")
    await interaction.response.defer()

    if not video.filename.lower().endswith(('.gif', '.mp4')):
        print(f"Invalid file type from {interaction.user.name}: {video.filename}")
        await interaction.followup.send("Please attach a GIF or MP4 file.")
        return

    # Download the video to a temporary file
    with tempfile.NamedTemporaryFile(suffix='_input' + os.path.splitext(video.filename)[1], delete=False) as tmp_file:
        await video.save(tmp_file.name)
        input_path = tmp_file.name
    
    print(f"Downloaded input file for {interaction.user.name}: {video.filename}")

    # Set output path in ./data/flavorized
    output_filename = f"flavorized_{os.path.splitext(video.filename)[0]}.avi"
    output_path = os.path.abspath(os.path.join("./data/flavorized", output_filename))

    # Call the interpolate script
    flavorize_command = [
        'python', 'interpolate.py',
        '--input_video', input_path,
        '--output_video', output_path,
        '--factor', '4',
        '--load_model', 'D:/FLAVR_4x.pth',
        '--input_ext', os.path.splitext(video.filename)[1]
    ]

    try:
        # Run the interpolate script asynchronously
        print(f"Starting flavorization for {interaction.user.name}'s file: {video.filename}")
        process = await asyncio.create_subprocess_exec(
            *flavorize_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"Flavorization error for {interaction.user.name}'s file: {video.filename}")
            await interaction.followup.send(f"Error during flavorization: {stderr.decode()}")
            return

        # Check if the output file exists
        if not os.path.exists(output_path):
            await interaction.followup.send("Flavorization completed, but the output file was not created. Please check the interpolate.py script.")
            return

        # Convert AVI to MP4
        mp4_output_filename = f"flavorized_{os.path.splitext(video.filename)[0]}.mp4"
        mp4_output_path = os.path.abspath(os.path.join("./data/flavorized", mp4_output_filename))
        ffmpeg_command = [
            'ffmpeg',
            '-i', output_path,
            '-c:v', 'libx264',
            '-crf', '23',
            '-preset', 'medium',
            '-c:a', 'aac',
            '-b:a', '128k',
            mp4_output_path
        ]

        print(f"Starting MP4 conversion for {interaction.user.name}'s file: {video.filename}")
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"MP4 conversion error for {interaction.user.name}'s file: {video.filename}")
            await interaction.followup.send(f"Error during MP4 conversion: {stderr.decode()}")
            return

        # Send the flavorized MP4
        print(f"Sending flavorized MP4 to {interaction.user.name}: {mp4_output_filename}")
        await interaction.followup.send(file=discord.File(mp4_output_path, filename=mp4_output_filename))

    except Exception as e:
        print(f"Error processing {interaction.user.name}'s file {video.filename}: {str(e)}")
        await interaction.followup.send(f"An error occurred: {str(e)}")

    finally:
        # Clean up temporary input file and AVI output
        print(f"Cleaning up files for {interaction.user.name}'s request: {video.filename}")
        os.remove(input_path)
        os.remove(output_path)
        os.remove(mp4_output_path)

client.run(private.token)