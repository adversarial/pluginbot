# Frontend for politeness - reminds a user to say a specified phrase or their message is removed
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

from plugins.lib.politeness import politeness_manager
from lib.FancyDiscordPrompt import make_UserActionOptionPromptThenModal

class PolitenessCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.polite_checker = politeness_manager(bot)

    async def cog_load(self):
        await self.polite_checker.init()
        self.polite_checker.check_politeexpiry.start()

    async def cog_unload(self):
        self.polite_checker.check_politeexpiry.cancel()

    @app_commands.command(description="Forces a user to be more polite.")
    async def politeness_enforcer(self, interaction: discord.Interaction):
        sender = interaction.user
        target, phrase, duration, custom_phrase = await make_UserActionOptionPromptThenModal(
                                                    interaction,
                                                    title = 'Politeness enforcer', description= 'Messages by the selected user will be deleted unless they include the phrase.',
                                                    action_placeholder = 'Select a phrase', actions = politeness_manager.phrases,
                                                    option_placeholder = 'Select a duration', options = politeness_manager.durations,
                                                    modal_title = 'Custom phrase text', modal_input_label = 'Specify a phrase',
                                                    trigger_option = discord.SelectOption(label = 'Custom', value = 'custom')
                                                    )
        if not all((target, phrase, duration)):
            return
        if target.bot:
            await interaction.followup.send(f'{target.display_name} is a bot and cannot be targeted by this feature.', ephemeral = True)
        else:
            await self.polite_checker.add_entry(target.id, interaction.guild.id, int(duration.value), custom_phrase or phrase.label)
            if duration.label.lower() == 'remove':
                await interaction.followup.send(f'{sender.display_name} has removed the polite enforcer from {target.display_name}.')
            else:
                await interaction.followup.send(f"{sender.display_name} has has politely reminded {target.display_name}  to say '{custom_phrase or phrase.label}' for {duration.label}.")

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, msg: discord.Message):
        if msg.guild and not msg.author.bot:
            await self.polite_checker.process_message(msg.author.display_name, msg.author.id, msg.guild.id, msg.content, msg)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            await self.on_message(after)

async def setup(bot: commands.Bot):
    await bot.add_cog(PolitenessCog(bot = bot))