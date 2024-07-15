# Frontend for comment length requirments
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import discord
from discord import app_commands
from discord.ext import commands

from plugins.lib.verbosity import verbosity_manager
from lib.FancyDiscordPrompt import make_UserActionOptionPrompt


class VerbosityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verbosity_checker = verbosity_manager(bot)

    async def cog_load(self):
        await self.verbosity_checker.init()
        self.verbosity_checker.check_verbosityexpiry.start()

    async def cog_unload(self):
        self.verbosity_checker.check_verbosityexpiry.cancel()

    @app_commands.command(description="Make a user post longer or shorter comments.")
    async def verbosity_enforcer(self, interaction: discord.Interaction):
        sender = interaction.user
        target, option, duration  = await make_UserActionOptionPrompt(interaction,
                                                    title = 'Verbosity enforcer', description= 'Messages by the selected user will be deleted if either too long or short.',
                                                    action_placeholder = 'Select an action', actions = verbosity_manager.modifiers,
                                                    option_placeholder = 'Select a duration', options = verbosity_manager.durations)
        if not all((target, option, duration)):
            return
        if target.bot:
            await interaction.followup.send(f'{target.display_name} is a bot and cannot be targeted by this feature.', ephemeral = True)
        else:
            await self.verbosity_checker.add_entry(target.id, interaction.guild.id, int(duration.value), option.label)
            if duration.label.lower() == 'remove':
                await interaction.followup.send(f'{sender.display_name} has removed length restrictions on {target.display_name}.')
            else:
                await interaction.followup.send(f'{sender.display_name} has {option.label} restricted {target.display_name} for {duration.label} unless they their comments are {option.value}.')

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, msg: discord.Message):
        if msg.guild and not msg.author.bot:
            await self.verbosity_checker.process_message(msg.author.display_name, msg.author.id, msg.guild.id, msg.content, msg)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.on_message(after)

async def setup(bot):
    await bot.add_cog(VerbosityCog(bot = bot))
