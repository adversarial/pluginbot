# Text modifier frontend
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
from discord.ext import commands, tasks

from lib.FancyDiscordPrompt import make_OptionPromptNoSubmit
from plugins.lib.ify import owoifier, sfwifier, vallifier
import random

###############################################################################
# slash commands
###############################################################################

ifiers = [
    discord.SelectOption(label = 'owoify', value = 'owoify'),
    discord.SelectOption(label = 'sfwify', value = 'sfwify'),
    discord.SelectOption(label = 'vallify', value = 'vallify')
]

class IfyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ify_ctx_menu = app_commands.ContextMenu(name='ify', callback=self.ify_ctx_callback)
        self.bot.tree.add_command(self.ify_ctx_menu)

    async def cog_load(self):
        pass

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ify_ctx_menu)

    async def ify_ctx_callback(self, interaction: discord.Interaction, msg: discord.Message):
        option = await make_OptionPromptNoSubmit(interaction, title = 'Modify text', description = f"Select a modifier for {msg.author.display_name}'s comment", options = ifiers)
        if not option:
            return
        
        ifier = None
        match option.label:
            case 'owoify':
                ifier = owoifier()
            case 'sfwify':
                ifier = sfwifier()
            case 'vallify':
                ifier = vallifier()

        await msg.reply(ifier.ify_text(msg.content, nsfw_flag = msg.channel.is_nsfw()), mention_author = False)
        await interaction.delete_original_response()

    ify_group = app_commands.Group(name="ify", description="Modify text.")

    @ify_group.command(name = "owoify", description = "OwOify text.")
    async def owoify(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(owoifier().ify_text(text, nsfw_flag = interaction.channel.is_nsfw()))

    @ify_group.command(name = "sfwify", description = "Make text safe for work.")
    async def sfwpost(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(sfwifier().ify_text(text))

    @ify_group.command(name='valleypost', description="e.g. 'Umm like totally that's the text sis'")
    async def queenpost(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(vallifier().ify_text(text, nsfw_flag = interaction.channel.is_nsfw()))

async def setup(bot: commands.Bot):
    await bot.add_cog(IfyCog(bot = bot))
