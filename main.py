import asyncio
import logging
import os

import discord
from discord.ext import commands

# Create logger
logger = logging.getLogger("AudioBot")

if not logger.hasHandlers():  # Prevent duplicate handlers
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Remove duplicate handlers from discord logger
discord_logger = logging.getLogger("discord")
discord_logger.handlers.clear()
discord_logger.propagate = False

# Load bot token
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN', None)

if DISCORD_TOKEN is None:
    from utils import settings
    try:
        logger.info("Checking TOML configuration...")
        DISCORD_TOKEN = settings.config["General"]["DiscordBotToken"]
        logger.info(f"Bot token loaded: {DISCORD_TOKEN[:5]}...{DISCORD_TOKEN[-5:]}")
    except (TypeError, AttributeError) as e:
        logger.error("Failed to load bot token. Check your environment variable or .toml file.", exc_info=True)
        raise

# Enable intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

# Bot initialization
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("<AudioBot> "),
    description="An audio bot that plays audio.",
    intents=intents
)

# Ensure data directory exists
DATA_DIR = "data/audio/sounds"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info(f"Created data directory: {DATA_DIR}")

@bot.event
async def on_ready():
    logger.info(f"Bot is online as {bot.user.name}!")

@bot.command(name='join', help='Joins the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await send_basic_message(ctx, f"{ctx.message.author.name} is not connected to a voice channel")
        return
    
    channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='Leaves the voice channel')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()

    # Delete the command message after 15 seconds
    await delete_messages(ctx.message, wait=15)
    
@bot.command(name='stop', help='Stops the current sound')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await send_basic_message(ctx, "Stopped playback.")
        
    # Delete the command message after 15 seconds
    await delete_messages(ctx.message, wait=15)

@bot.command(name='play', help='Plays a sound file from a directory. Usage: @AudioBot play <directory> <track_number>')
async def play(ctx, directory: str, track_number: int = 1):
    # Attempt to join current voice channel
    if not ctx.message.author.voice:
        await send_basic_message(ctx, f"{ctx.message.author.name} is not connected to a voice channel")
        return
    
    if not ctx.voice_client:
        await ctx.message.author.voice.channel.connect()

    # Construct the directory path
    dir_path = os.path.join(DATA_DIR, directory)
    logger.info(dir_path)

    # Check if the path is a directory or a file
    if os.path.isdir(dir_path):
        # Get all files in the directory that match the schema "<track_name>_<number>.mp3"
        sound_files = [f for f in os.listdir(dir_path) if f.endswith('.mp3') and f.startswith(directory)]
        if not sound_files:
            await send_basic_message(ctx, f"No sound files found in the directory '{directory}'.")
            return

        # Sort files by track number (assuming filenames are like "Henchman_1.mp3", "Henchman_2.mp3", etc.)
        sound_files.sort(key=lambda x: int(x.split('_')[-1].replace('.mp3', '')))

        # Check if the requested track number is valid
        if track_number < 1 or track_number > len(sound_files):
            await send_basic_message(ctx, f"Invalid track number. Please choose a number between 1 and {len(sound_files)}.")
            return

        # Get the selected track
        selected_track = sound_files[track_number - 1]
        audio_file_name = os.path.join(dir_path, selected_track)
        
    else:
        # Handle top-level files
        audio_file_name = f'{dir_path}.mp3'
        logger.info(f"Looking for audio file: {audio_file_name}")
    
        if not os.path.isfile(audio_file_name):
            await send_basic_message(ctx, f"Sound file `{directory}` not found")
            return
        
        selected_track = os.path.basename(dir_path)

    logger.info(f"Playing: {audio_file_name}")

    try:
        source = discord.FFmpegPCMAudio(audio_file_name)
        playing_message = await ctx.send(f"Playing: {selected_track.replace('.mp3', '')}")
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(delete_messages(ctx.message, playing_message, wait=1), bot.loop))
        
    except Exception as e:
        await send_basic_message(ctx, f"An error occurred: {e}")
        logger.error(f"Error during playback: {e}")
        
@bot.command(name='list', help='Lists all available sound files. Use "list expand" to show subdirectories and files.')
async def list_sounds(ctx, expand: str = None):
    try:
        # Function to generate a tree-like structure of the directory
        def generate_tree(directory, expand_all=False):
            tree = []
            for root, dirs, files in os.walk(directory):
                # Calculate the level of indentation
                level = root.replace(directory, '').count(os.sep)
                # Skip the root directory line
                if root == directory:
                    level = -1  # Top-level files and directories should not be indented
                indent = ' ' * 4 * (level) if level > 1 else ''
                # Add the directory name (if not the root)
                if root != directory:
                    tree.append(f"{indent}{os.path.basename(root)}/")
                # Add files (only if expand_all is True or we're at the top level)
                sub_indent = ' ' * 4 * (level) if level >= 0 else '' 
                if expand_all or level == -1:
                    for file in files:
                        if file.endswith('.mp3'):
                            tree.append(f"{sub_indent}{file.replace('.mp3', '')}")
            return tree

        # Generate the tree structure for the DATA_DIR
        expand_all = expand == "expand"  # Check if the user wants the full expanded tree
        tree_structure = generate_tree(DATA_DIR, expand_all)
        if not tree_structure:
            await send_basic_message(ctx, "No sound files found in the `data/audio/sounds` directory.")
            return

        # Format the tree structure as a string
        tree_output = "\n".join(tree_structure)
        await send_basic_message(ctx, f"Available sound files:\n```\n{tree_output}\n```")

    except Exception as e:
        await send_basic_message(ctx, f"An error occurred while listing sound files: {e}")
        
async def delete_messages(*messages, wait: int = 1):
    """
    Deletes one or more messages after a specified delay.

    Args:
        *messages: One or more messages to delete.
        wait (int): The delay in seconds before deleting the messages. Default is 1 second.
    """
    # Check if the bot has the "Manage Messages" permission
    if messages and not messages[0].guild.me.guild_permissions.manage_messages:
        logger.error("Bot does not have permission to delete messages.")
        return

    # Wait for the specified delay
    await asyncio.sleep(wait)

    # Delete each message
    for message in messages:
        if message is None:
            continue  # Skip if the message is None

        try:
            await message.delete()
            # logger.info(f"Message deleted: {message.content}")
        except discord.NotFound:
            logger.error("Message already deleted.")
        except discord.Forbidden:
            logger.error("Bot does not have permission to delete the message.")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            
async def send_basic_message(ctx, message_content, wait: int = 15):
    # Send the message
    sent_message = await ctx.send(message_content)
    # Delete the command and sent message after 15 seconds
    await delete_messages(ctx.message, sent_message, wait=wait)
    
# Run the bot 
bot.run(DISCORD_TOKEN)
