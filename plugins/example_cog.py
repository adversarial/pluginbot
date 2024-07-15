# Empty cog file 
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from discord import app_commands, Message
from discord.ext import commands


class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    async def cog_unload(self):
        pass

    @commands.command(name='helloworld', hidden = False)
    async def helloworld(self, ctx):
        await ctx.channel.send('Hello world.')

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        pass

async def setup(bot):
    await bot.add_cog(ExampleCog(bot = bot))
