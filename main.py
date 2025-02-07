import asyncio
import logging
import os

import coloredlogs
import discord
from discord.ext import commands

# Create logger
logger = logging.getLogger("AudioBot")

# Define custom styles for log levels
level_styles = {
    'debug': {'color': 'blue'},
    'info': {'color': 'white'},
    'warning': {'color': 'yellow'},
    'error': {'color': 'red'},
    'critical': {'color': 'red', 'bold': True},
}

# Define custom styles for fields (like the timestamp and logger name)
field_styles = {
    'asctime': {'color': 'white'},
    'name': {'color': 'magenta', 'bold': False},
    'levelname': {'color': 'cyan', 'bold': False},
}

# Install coloredlogs with custom styles
coloredlogs.install(
    level='INFO',
    logger=logger,
    fmt="%(asctime)s %(levelname)s     %(name)s  %(message)s",
    level_styles=level_styles,
    field_styles=field_styles
)

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
    intents=intents,
    case_insensitive=True 
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
    if not ctx.message.author.voice:
        await send_basic_message(ctx, f"{ctx.message.author.name} is not connected to a voice channel")
        return

    if not ctx.voice_client:
        await ctx.message.author.voice.channel.connect()

    # Convert input to lowercase
    directory = directory.lower()
    dir_path = os.path.join(DATA_DIR, directory)

    if os.path.isdir(dir_path):
        sound_files = [f for f in os.listdir(dir_path) if f.lower().startswith(directory) and f.endswith('.mp3')]
        if not sound_files:
            await send_basic_message(ctx, f"No sound files found in the directory '{directory}'.")
            return

        sound_files.sort(key=lambda x: int(x.split('_')[-1].replace('.mp3', '')))

        if track_number < 1 or track_number > len(sound_files):
            await send_basic_message(ctx, f"Invalid track number. Please choose a number between 1 and {len(sound_files)}.")
            return

        selected_track = sound_files[track_number - 1]
        audio_file_name = os.path.join(dir_path, selected_track)
        
    else:
        # Handle top-level files case-insensitively
        all_files = {f.lower(): f for f in os.listdir(DATA_DIR) if f.endswith('.mp3')}
        if directory + ".mp3" not in all_files:
            await send_basic_message(ctx, f"Sound file `{directory}` not found")
            return

        selected_track = all_files[directory + ".mp3"]
        audio_file_name = os.path.join(DATA_DIR, selected_track)

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
            seen_dirs = {}  # Store lowercase directory names for case-insensitive matching
            
            for root, dirs, files in os.walk(directory):
                # Normalize directory paths to lowercase
                normalized_root = root.lower()
                
                # Store actual directory names for proper output
                real_dirname = os.path.basename(root)
                
                # Track directories in lowercase for case-insensitive matching
                seen_dirs[normalized_root] = real_dirname
                
                # Calculate the level of indentation
                level = normalized_root.replace(directory.lower(), '').count(os.sep)
                
                # Skip the root directory line
                if root == directory:
                    level = -1  # Top-level files and directories should not be indented
                
                indent = ' ' * 4 * (level) if level > 1 else ''
                
                # Add the directory name (if not the root)
                if root != directory:
                    tree.append(f"{indent}{real_dirname}/")
                
                # Add files (only if expand_all is True or we're at the top level)
                sub_indent = ' ' * 4 * (level) if level >= 0 else '' 
                if expand_all or level == -1:
                    for file in files:
                        if file.endswith('.mp3'):
                            tree.append(f"{sub_indent}{file.replace('.mp3', '')}")
            
            return tree

        # Generate the tree structure for the DATA_DIR
        expand_all = expand and expand.lower() == "expand"  # Check case-insensitively
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
