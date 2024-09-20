import discord
from discord.ext import commands
import aiohttp
import os
import json
from datetime import datetime
from discord import app_commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Directory to save images
IMAGE_SAVE_DIR = 'downloaded_images'
LAST_FETCH_FILE = 'last_fetch.json'
CHANNEL_ID = 1266517894683168789

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not os.path.exists(IMAGE_SAVE_DIR):
        os.makedirs(IMAGE_SAVE_DIR)
    if not os.path.exists(LAST_FETCH_FILE):
        with open(LAST_FETCH_FILE, 'w') as f:
            json.dump({'last_fetch': None}, f)

    # Sync commands with Discord
    try:
        await bot.tree.sync()
        print("Slash commands synchronized")
    except Exception as e:
        print(f"Error synchronizing commands: {e}")

@bot.tree.command(name="images", description="Download the most recent PNG images from #disc-drive-data.")
@app_commands.checks.has_role('nubda')
async def images(interaction: discord.Interaction):
    if interaction.channel_id != CHANNEL_ID:
        await interaction.response.send_message("Ehn-na... Nha-nah nhu-ne. (This command... can only be used in the specific channel.)")
        return
    try:
        await interaction.response.send_message("Ehn-ne... (Starting analysis...)")
        with open(LAST_FETCH_FILE, 'r') as f:
            last_fetch = json.load(f).get('last_fetch')
        last_fetch_time = datetime.fromisoformat(last_fetch) if last_fetch else None
        new_last_fetch_time = datetime.now().isoformat()

        for file in os.listdir(IMAGE_SAVE_DIR):
            file_path = os.path.join(IMAGE_SAVE_DIR, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        image_count = 0
        async for message in interaction.channel.history(limit=500, after=last_fetch_time, oldest_first=True):
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.endswith(('.png', '.jpg')):
                        await download_image(attachment, image_count)
                        image_count += 1

        with open(LAST_FETCH_FILE, 'w') as f:
            json.dump({'last_fetch': new_last_fetch_time}, f)

        await interaction.followup.send(f'Ehn-na en-na-ehn! (Fetched and downloaded {image_count} images!)')
    except Exception as e:
        print(f"Error fetching messages: {e}")
        await interaction.response.send_message("Ehn-nuh neh. (An error occurred while fetching previous messages.)")

async def download_image(attachment, index):
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as response:
            if response.status == 200:
                unique_filename = f"{index:04d}_{attachment.filename}"
                file_path = os.path.join(IMAGE_SAVE_DIR, unique_filename)
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
                print(f'Downloaded {unique_filename}')
            else:
                print(f'Failed to download {attachment.filename}, status code: {response.status}')

@images.error
async def images_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("Nu-ehn nah. (You do not have the required role to use this command.)")
    elif isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("En ehn-nu-ne. (You do not have the required permissions to use this command.)")
    else:
        await interaction.response.send_message("En-nah en. (An error occurred while executing the command.)")

bot.run('MTI3MDEwOTYxNTQwMDQxOTQ4MA.GMtW7o.3iFcg5L1OzDVzOoLH9FJG1mzoDD5pMGFkWGZjk')