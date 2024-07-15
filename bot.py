# Discord commands.Bot subclass that sets up from config.ini and loads plugins
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
from discord.ext import commands
import datetime
import os

from config import config

class ModuleBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.launch_time = datetime.datetime.now()

    async def setup_hook(self):
        for plugin in os.listdir(f'./{self.config["plugin_directory"]}'):
            if plugin.endswith('.py'):
                if self.config['plugin_whitelist_only'] and plugin[:-3] not in self.config['plugin_whitelist']:
                        continue
                await super().load_extension(f'{self.config["plugin_directory"]}.{plugin[:-3]}')
                print(f'Loaded plugin {plugin}')

    async def reload_cog(self, name):
         if self.config['plugin_whitelist_only'] and name not in self.config['plugin_whitelist']:
            return
         await super().reload_extension(f'{self.config["plugin_directory"]}.{name}')

    async def guild_select_options(self):
        guildoptions = [ ]
        for g in self.guilds:
              guildoptions.append(discord.SelectOption(label = g.name, value = str(g.id)))
        return guildoptions
    
    async def on_guild_join(self, ctx, guild):
         if (config['guild_whitelist_only'] and guild.id not in config['guild_whitelist'] 
         or guild.id in config['guild_banlist']):
            await guild.leave()
            print(f'Left guild {guild.name} ({guild.member_count}) id: {guild.id} on join due to banlist.')

intents = discord.Intents.default()
intents.message_content = True
bot = ModuleBot(command_prefix = config['command_prefix'], intents = intents, owner_ids = config['owner_ids'])

STARTUP_BANNER = r"""
 ▄· ▄▌ ▄▄▄·  ▄▄▄· ▄▄▄·▄▄▄ .▄▄▄  
▐█ ██▌▐█ ▀█ ▐█ ▄█▐█ ▄▌▀▄.▀·▀▄ █·
▐█▄██▪▄█▀▀█  ██▀· ██▀·▐▀▀▪ ▐▀▀▄ 
  █▀·.▐█ ▪▐▌▐█▪·•▐█▪·•▐█▄▄▌▐█•█▌
  ▀ •  ▀  ▀ .▀   .▀    ▀▀▀ .▀  ▀"""

@bot.event
async def on_ready():
    print(STARTUP_BANNER)
    msg = f'Initialized {config["bot_name"]} as {bot.user} with options:\n'\
          f'\t- command prefix "{config["command_prefix"]}"\n'\
          f'\t- plugin whitelist {"enabled" if config["plugin_whitelist_only"] else "disabled"}\n'\
          f'\t- logfile "{config["log_file_name"]}"\n'\
          f'in {len(bot.guilds)} guilds:\n'
    for s in bot.guilds:
        msg += f'\t- {s.name} ({s.member_count}) id: {s.id}\n'
    print(msg, end='')
    pass
