import asyncio

import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import send_basic_message


class Help(Cog):
    """
	Cog that manages help command 
	"""
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot
        
    @command(name="help", help="Shows this help message")
    async def custom_help(self, ctx, *, command_name: str = None):
        # If no specific command is provided, show the general help message.
        if command_name is None:
            help_message = "📜 **Available Commands:**\n"
            for command in self.bot.commands:
                # Omit usage details in the general help.
                help_message += f"**{command.name}** - {command.help}\n"
            # add final prompt
            help_message += "\nType `@AudioBot help <command>` for more details on a specific command."
            
            await send_basic_message(self.bot.logger, ctx, help_message, wait=30)
        else:
            # Try to retrieve the command by its name (case-insensitive).
            command = self.bot.get_command(command_name.lower())
            if command is None:
                await send_basic_message(self.bot.logger, ctx, f"Command `{command_name}` not found.", wait=30)
            else:
                # Build the help message for this command.
                help_message = f"📜 **{command.name}**\n\n**Description:** {command.help}\n"
                # Append usage details for specific commands if necessary.
                if command.name.lower() == "play":
                    help_message += "    *Usage*: @AudioBot play <directory> <track_number> or @AudioBot play <track_name>\n"
                elif command.name.lower() == "list":
                    help_message += "    *Usage*: @AudioBot list <expand>\n"
                await send_basic_message(self.bot.logger, ctx, help_message, wait=30)

            
    @Cog.listener()
    async def on_ready(self: Cog) -> None:
        # if bot is ready 
        if not self.bot.ready:
            # ready up cog
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])


async def setup(bot: BotBase) -> None:
	"""
	Adds cog to bot
	"""
	await bot.add_cog(Help(bot))