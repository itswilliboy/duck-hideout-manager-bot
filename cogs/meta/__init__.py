import discord
from bot import DuckBot
from utils.errors import DuckBotNotStarted
from .embed import EmbedMaker


class Meta(EmbedMaker):
    """All commands about the bot itself."""

    @discord.utils.cached_property
    def brief(self):
        if not self.bot.user:
            raise DuckBotNotStarted('Somehow, the bot has not logged in yet')
        return f"Commands related to {self.bot.user.name}"


async def setup(bot: DuckBot):
    await bot.add_cog(Meta(bot))
