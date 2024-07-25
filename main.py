import discord
from discord import app_commands
import asyncio
import tempfile
import os
import subprocess
import private
import base64

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
@app_commands.describe(video="The video file to interpolate")
async def interpolate(interaction: discord.Interaction, video: discord.Attachment):
    await interaction.response.defer()

    if not video.filename.lower().endswith(('.gif', '.mp4')):
        await interaction.followup.send("Please attach a GIF or MP4 file.")
        return

    # Download the video
    video_data = await video.read()
    
    # Save the video to a temporary file
    with tempfile.NamedTemporaryFile(suffix='_input' + os.path.splitext(video.filename)[1], delete=False) as tmp_file:
        tmp_file.write(video_data)
        input_path = tmp_file.name

    # Set output path
    output_path = os.path.splitext(input_path)[0] + '_interpolated.mp4'

    # Call the interpolate script
    interpolate_command = [
        'python', 'interpolate.py',
        '--input_video', input_path,
        '--output_video', output_path,
        '--factor', '4',
        '--output_ext', '.mp4',
        '--load_model', 'D:/FLAVR_4x.pth',
        '--input_ext', os.path.splitext(video.filename)[1]
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *interpolate_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode()
            await interaction.followup.send(f"Error during interpolation: {error_message}")
            return

        # Check if the output file exists
        if not os.path.exists(output_path):
            await interaction.followup.send("Interpolation completed, but the output file was not created. Please check the interpolate.py script.")
            return

        # Send the interpolated MP4
        await interaction.followup.send(file=discord.File(output_path, filename='interpolated.mp4'))

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

    finally:
        # Clean up temporary files
        os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

client.run(private.token)