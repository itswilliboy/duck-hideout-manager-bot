from __future__ import annotations

import asyncio
from typing import Any, DefaultDict
from collections import defaultdict

import discord
from discord.ext import commands, tasks
from bot import HideoutManager

from utils import HideoutCog, JOINED, LEFT, DEAF, MUTE, SELF_DEAF, SELF_MUTE, NO_DEAF, NO_MUTE


class VoiceChatLogs(HideoutCog):
    def __init__(self, bot: HideoutManager, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.queues: DefaultDict[discord.abc.MessageableChannel, commands.Paginator] = defaultdict(
            lambda: commands.Paginator(prefix='', suffix='')
        )
        self.lock = asyncio.Lock()
        self.send_messages.start()

    async def cog_unload(self) -> None:
        self.send_messages.cancel()
        return await super().cog_unload()

    @tasks.loop(seconds=5)
    async def send_messages(self):
        async with self.lock:
            for channel, paginator in self.queues.items():
                for page in paginator.pages:
                    await channel.send(page)
                paginator.clear()

    async def enqueue_message(self, message: str, channel: discord.abc.MessageableChannel):
        async with self.lock:
            self.queues[channel].add_line(message)

    @commands.Cog.listener('on_voice_state_update')
    async def voice_channel_notifications(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        ts = discord.utils.format_dt(discord.utils.utcnow(), 'T')
        if before.channel != after.channel:
            if before.channel:
                await self.enqueue_message(
                    f"[{ts}] {LEFT} **{discord.utils.escape_markdown(member.display_name)}** left.", before.channel
                )
            if after.channel:
                await self.enqueue_message(
                    f"[{ts}] {JOINED} **{discord.utils.escape_markdown(member.display_name)}** joined.", after.channel
                )

        channel = after.channel or before.channel
        if not channel:
            return

        if before.deaf != after.deaf:
            if before.deaf:
                await self.enqueue_message(
                    f"[{ts}] {NO_DEAF} **{discord.utils.escape_markdown(member.display_name)}** got undeafened.", channel
                )
            if after.deaf:
                await self.enqueue_message(
                    f"[{ts}] {DEAF} **{discord.utils.escape_markdown(member.display_name)}** got deafened.", channel
                )

        if before.mute != after.mute:
            if before.mute:
                await self.enqueue_message(
                    f"[{ts}] {NO_MUTE} **{discord.utils.escape_markdown(member.display_name)}** got unmuted.", channel
                )
            if after.mute:
                await self.enqueue_message(
                    f"[{ts}] {MUTE} **{discord.utils.escape_markdown(member.display_name)}** got muted.", channel
                )

        if before.self_deaf != after.self_deaf:
            if before.self_deaf:
                await self.enqueue_message(
                    f"[{ts}] {NO_DEAF} **{discord.utils.escape_markdown(member.display_name)}** undeafened themselves.",
                    channel,
                )
            if after.self_deaf:
                await self.enqueue_message(
                    f"[{ts}] {SELF_DEAF} **{discord.utils.escape_markdown(member.display_name)}** deafened themselves.",
                    channel,
                )

        elif before.self_mute != after.self_mute:
            if before.self_mute:
                await self.enqueue_message(
                    f"[{ts}] {NO_MUTE} **{discord.utils.escape_markdown(member.display_name)}** unmuted themselves.", channel
                )
            if after.self_mute:
                await self.enqueue_message(
                    f"[{ts}] {SELF_MUTE} **{discord.utils.escape_markdown(member.display_name)}** muted themselves.", channel
                )
