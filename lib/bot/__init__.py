from asyncio import sleep
from glob import glob

import coloredlogs
from discord import Intents, Message
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Context, when_mentioned_or

from utils.funcs import *

# Enable intents
INTENTS = Intents.default()
INTENTS.messages = True
INTENTS.message_content = True
INTENTS.members = True

# List of cog names
COGS = [path.split(convert_path_os("\\"))[-1][:-3] for path in glob(convert_path_os("./lib/cogs/*.py"))]


def get_prefix(bot: BotBase, message: Message) -> list:
    """
    Gets command prefix from database
    """
    prefix = "<AudioBot> "
    return when_mentioned_or(prefix)(bot, message)


class Ready(object):
    """
    Used to prepare elements that have async aspects
    """
    def __init__(self, itr: list, name: str) -> None:
        # List var or iterate element
        self.itr = itr
        # Name of the type: example a list of cogs would be cog
        self.name = name
        # Create attributes
        for element in self.itr:
            setattr(self, element, False)

    def ready_up(self, element: str) -> None:
        # Set specific element to true
        setattr(self, element, True)
        # Log readiness
        bot.logger.info(f"{element} {self.name} ready")

    def all_ready(self) -> list:
        # If all elements in list are true
        return all([getattr(self, element) for element in self.itr])


class Bot(BotBase):
    """
    Bot instance used to interact with client
    """
    def __init__(self: BotBase) -> None:
        # Name of bot
        self.name = 'AudioBot'
        # Bot ready and cogs ready
        self.ready = False
        # Confirmation for cog init
        self.cogs_ready = Ready(COGS, 'cog')
        # Bot logger
        self.logger = load_logger()
        # Token used to run bot
        self.TOKEN = load_token(self.logger)
        # Bot data dir
        self.data_dir = "data/audio/sounds"

        # Call parent object init
        super().__init__(intents=INTENTS, command_prefix=get_prefix)

    async def setup(self: BotBase) -> None:
        """
        Initiates cogs before bot is ready
        """
        # remove default help cog
        self.remove_command("help")
        # Init cogs
        for cog in COGS:
            # Load cog
            await self.load_extension(f"lib.cogs.{cog}")
            # Log cog loading
            self.logger.info(f"{cog} cog loaded")
        # Log setup completion
        self.logger.info("Setup complete")

    """ ------------------------------------------ Events ------------------------------------------------ """
    async def on_connect(self: BotBase) -> None:
        """
        Actions to perform on connect
        """
        # Log setup start
        self.logger.info("Running setup...")
        # Attempt setup
        await self.setup()
        # Log connection
        self.logger.info("Bot connected")

    async def on_disconnect(self: BotBase) -> None:
        """
        Actions to perform on disconnect
        """
        # Log disconnection
        self.logger.info("Bot disconnected")

    async def on_error(self: BotBase, err, *args, **kwargs) -> None:
        """
        Actions to perform on any error
        """
        # If error is related to user input
        if err == "on_command_error":
            # Send message prompt
            await args[0].send("Something went wrong.")
        # Log error
        self.logger.error("An error occurred", exc_info=True)
        raise

    async def on_ready(self: BotBase) -> None:
        """
        Actions to perform once the bot is ready
        """
        if not self.ready:
            # Confirm all cogs are ready
            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            self.ready = True
            # Log readiness
            self.logger.info("Bot ready")
        else:
            # Log reconnection
            self.logger.info("Bot reconnected")

    """ ------------------------------------------ Other Functions ------------------------------------------------ """
    def run(self: BotBase, version: str) -> None:
        """
        Runs bot
        """
        # Bot version
        self.VERSION = version
        # Log bot startup
        self.logger.info("Running bot...")
        # Run bot
        super().run(self.TOKEN, reconnect=True)

    async def process_commands(self: BotBase, message: Message) -> None:
        """
        Actions to perform when a message doesn't have a proper channel
        """
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if not self.ready:
                await ctx.send("I'm not ready to receive commands. Please wait a few seconds.")
            else:
                await self.invoke(ctx)

# Bot instance
bot = Bot()