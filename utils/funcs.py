import asyncio
import logging
import os
import platform

import coloredlogs
import discord
from discord.ext.commands import Bot as BotBase

# Get the operating system name
OS_NAME = platform.system().lower()

""" ------------------------------------------ File System Funcs ------------------------------------------------ """
	
def convert_path_os(path: str) -> str:
	"""
	Converts path to standard format based on os type
	"""
	return path.replace('\\','/') if OS_NAME == 'linux' or OS_NAME == 'darwin' else path.replace('/','\\')


""" ------------------------------------------ Message Handling Funcs ------------------------------------------------ """

async def delete_messages(logger, *messages, wait: int = 1):
    """
    Deletes one or more messages after a specified delay.
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
            
async def send_basic_message(logger, ctx, message_content, wait: int = 15):
    """
    Sends a message and deletes the command and sent message after a specified delay.
    """
    # Send the message
    sent_message = await ctx.send(message_content)
    # Delete the command and sent message after 15 seconds
    await delete_messages(logger, ctx.message, sent_message, wait=wait)
    

""" ------------------------------------------ Other Funcs ------------------------------------------------ """
def load_logger():
	"""
	Load logger with coloredlogs
	"""
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
		level='DEBUG',
		logger=logger,
		fmt="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
		level_styles=level_styles,
		field_styles=field_styles
	)

	# Remove duplicate handlers from discord logger
	discord_logger = logging.getLogger("discord")
	discord_logger.handlers.clear()
	discord_logger.propagate = False

	return logger


def load_token(logger):
	"""
	Load discord bot token from environment variable or .toml file
	"""
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

	return DISCORD_TOKEN