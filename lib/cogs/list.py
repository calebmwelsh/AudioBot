import os

import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *


class List(Cog):
    """
	Cog that manages list command
	"""
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name='list', help='Lists all available sound files.')
    async def list_sounds(self, ctx, expand: str = None):
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
            tree_structure = generate_tree(self.bot.data_dir, expand_all)

            if not tree_structure:
                await send_basic_message(self.bot.logger, ctx, "No sound files found in the `data/audio/sounds` directory.")
                return
            # Format the tree structure as a string
            tree_output = "\n".join(tree_structure)
            await send_basic_message(self.bot.logger, ctx, f"Available sound files:\n```\n{tree_output}\n```")

        except Exception as e:
            await send_basic_message(self.bot.logger, ctx, f"An error occurred while listing sound files: {e}")
            self.bot.logger.error(f"An error occurred while listing sound files: {e}")
            
            
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
	await bot.add_cog(List(bot))