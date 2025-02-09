import os

import discord
from discord import FFmpegPCMAudio
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *


class Voice(Cog):
    """
	Cog that manages voice commands
	"""
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name='join', help='Joins the voice channel')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await send_basic_message(self.bot.logger, ctx, f"{ctx.message.author.name} is not connected to a voice channel")
            return
        
        channel = ctx.message.author.voice.channel
        await channel.connect()

    @command(name='leave', help='Leaves the voice channel')
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.guild.voice_client.disconnect()
        # Delete the command message after 15 seconds
        await delete_messages(self.bot.logger, ctx.message, wait=15)

    @command(name='stop', help='Stops the current sound')
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            await send_basic_message(self.bot.logger, ctx, "Stopped playback.")

    @command(name='play', help='Plays a sound file from a directory.')
    async def play(self, ctx, directory: str, track_number: int = 1):
        if not ctx.message.author.voice:
            await send_basic_message(ctx, f"{ctx.message.author.name} is not connected to a voice channel")
            return

        if not ctx.voice_client:
            await ctx.message.author.voice.channel.connect()

        # Convert input to lowercase
        directory = directory.lower()
        dir_path = os.path.join(self.bot.data_dir, directory)

        if os.path.isdir(dir_path):
            sound_files = [f for f in os.listdir(dir_path) if f.lower().startswith(directory) and f.endswith('.mp3')]
            if not sound_files:
                await send_basic_message(self.bot.logger, ctx, f"No sound files found in the directory '{directory}'.")
                return

            sound_files.sort(key=lambda x: int(x.split('_')[-1].replace('.mp3', '')))

            if track_number < 1 or track_number > len(sound_files):
                await send_basic_message(self.bot.logger, ctx, f"Invalid track number. Please choose a number between 1 and {len(sound_files)}.")
                return

            selected_track = sound_files[track_number - 1]
            audio_file_name = os.path.join(dir_path, selected_track)
            
        else:
            # Handle top-level files case-insensitively
            all_files = {f.lower(): f for f in os.listdir(self.bot.data_dir) if f.endswith('.mp3')}
            if directory + ".mp3" not in all_files:
                await send_basic_message(self.bot.logger, ctx, f"Sound file `{directory}` not found")
                self.bot.logger.error(f"Sound file `{directory}` not found")
                return

            selected_track = all_files[directory + ".mp3"]
            audio_file_name = os.path.join(self.bot.data_dir, selected_track)

        self.bot.logger.info(f"Playing: {audio_file_name}")

        try:
            source = discord.FFmpegPCMAudio(audio_file_name)
            playing_message = await ctx.send(f"Playing: {selected_track.replace('.mp3', '')}")
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(delete_messages(self.bot.logger, ctx.message, playing_message, wait=1), self.bot.loop))
            
        except Exception as e:
            await send_basic_message(self.bot.logger, ctx, f"An error occurred: {e}")
            try:
                await delete_messages(self.bot.logger, playing_message, wait=1)
            except Exception as e:
                self.bot.logger.error(f"Error with playing message deletion: {e}")
                
            self.bot.logger.error(f"Error during playback: {e}")
            
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
	await bot.add_cog(Voice(bot))