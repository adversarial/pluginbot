# Dev commands for modular discord bot
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

import datetime
import json
from config import config, configfile
from lib.FancyDiscordPrompt import make_OptionPrompt


class DevCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    async def cog_unload(self):
        pass


    async def _status_string(self):
        def format_time(td):
            return f'{td.days}d:{td.seconds // 3600}h:{(td.seconds // 60)%60}m:{(td.seconds % 60)}s'        
        uptime = format_time(datetime.datetime.now() - self.bot.launch_time)
        msg =  f'Initialized as {self.bot.user} for {uptime} in {len(self.bot.guilds)} guilds:\n'
        for s in self.bot.guilds:
            msg += f'- {s.name} ({s.member_count}) id: {s.id}\n'
        return msg
    
    # status ( )
    # print servers and status
    @commands.command(name='status', hidden = True)
    @commands.is_owner()
    async def status(self, ctx):
        await ctx.channel.send(self._status_string())

    # globalsync ( )
    # sync all slash commands (may take up to 24 hours to propogate)
    @commands.command(name='globalsync', hidden = True)
    @commands.is_owner()
    async def globalsync(self, ctx):
        await self.bot.tree.sync()
        print(f'Sync with global scope requested by {ctx.author} in {ctx.guild.name} id: {ctx.guild.id}.')

    # localsync ( )
    # sync all slash commands in server
    @commands.command(name='localsync', hidden = True)
    @commands.is_owner()
    async def localsync(self, ctx):
        await self.bot.tree.sync(guild = ctx.guild)
        print(f'Sync with guild scope requested by {ctx.author} in {ctx.guild.name} id: {ctx.guild.id}.')

    # leaveguild (id)
    # leave specified guild (does not ban)
    @commands.command(name='leaveguild', hidden = True)
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id):
        try:
            id = int(guild_id)
            for s in self.bot.guilds:
                if id == s.id:
                    await s.leave()
                    print(f'Left guild {s.name} ({s.member_count}) id: {id} requested by {ctx.author} in {ctx.guild.name} id: {ctx.guild.id}..')
        except ValueError:
             ctx.send(f'Invalid guild ID provided.', delete_after = 15.0)

    # reload (plugin_cog)
    # reloads a plugin for updates
    @commands.command(name='reload_plugin', hidden = True)
    @commands.is_owner()
    async def reload_plugin(self, ctx, plugin_cog):
        await self.bot.reload_cog(plugin_cog)

    async def _handle_enable_server(self, interaction: discord.Interaction):
        if await self.bot.is_owner(interaction.user):
            guild_options = [discord.SelectOption(label = g.name, value = str(g.id)) for g in self.bot.guilds]
        #elif interaction.user.id == interaction.guild.owner_id:
        #    guild_options = [ discord.SelectOption(label = interaction.guild.name, value = interaction.guild_id) ]
        else:
            await interaction.response.send_message(f'You must be the owner to use this function.', ephemeral = True)
            return
        
        guild = await make_OptionPrompt(interaction, 
                                        title = "Enable", 
                                        description = 'Add selected server to whitelist.', 
                                        option_placeholder = 'Select a guild',
                                        options = guild_options)
        if not guild:
            return
        guild_id = int(guild.value)

        if guild_id in config['guild_blacklist']:
            config['guild_blacklist'].remove(guild_id)
            configfile['blacklists']['guild_ids'] = json.dumps(config['guild_blacklist'])
            with open(config['filename'], 'w') as cfgfile:
                configfile.write(cfgfile)
            await interaction.followup.send(f'Removed guild {guild.label} from chatbot blacklist.', ephemeral = True)
        if config['whitelist_servers_only'] is True:
            config['guild_whitelist'].append(guild_id)
            configfile['whitelists']['guild_ids'] = json.dumps(config['guild_whitelist'])
            with open(config['filename'], 'w') as cfgfile:
                configfile.write(cfgfile)
            await interaction.followup.send(f'Added guild {guild.label} to chatbot whitelist.', ephemeral = True)

    async def _handle_disable_server(self, interaction: discord.Interaction):
        if await self.bot.is_owner(interaction.user):
            guild_options = [discord.SelectOption(label = g.name, value = str(g.id)) for g in self.bot.guilds]
        #elif interaction.user.id == interaction.guild.owner_id:
        #    guild_options = [ discord.SelectOption(label = interaction.guild.name, value = interaction.guild_id) ]
        else:
            await interaction.response.send_message(f'You must be the owner to use this function.', ephemeral = True)
            return
        
        guild = await make_OptionPrompt(interaction, 
                                        title = "Disable", 
                                        description= 'Add selected server to guild blacklist.', 
                                        option_placeholder = 'Select a guild',
                                        options = guild_options)
        if not guild:
            return
        guild_id = int(guild.value)
        guild_name = guild.label

        with open(config['filename'], 'w') as cfgfile:
            if guild_id in config['guild_blacklist']:
                config['guild_blacklist'].remove(guild_id)
                configfile['blacklists']['guild_ids'] = json.dumps(config['guild_blacklist'])
                await interaction.followup.send(f'Removed guild {guild_name} from chatbot blacklist.', ephemeral = True)
            if config['whitelist_servers_only'] is True:
                config['guild_whitelist'].append(guild_id)
                configfile['whitelists']['guild_ids'] = json.dumps(config['guild_whitelist'])
                await interaction.followup.send(f'Added guild {guild_name} to chatbot whitelist.', ephemeral = True)
            configfile.write(cfgfile)
        return guild_id, guild_name
    
    async def _handle_ban_guild(self, interaction: discord.Interaction):
        guild = await self._handle_disable_server(interaction)
        if not guild:
            return
        guild_name = guild.label
        guild_id = int(guild.value)

        with open(config['filename'], 'w') as cfgfile:
            config['guild_banlist'].append(guild.value)
            configfile['banlists']['guild_ids'] = json.dumps(config['guild_banlist'])
            
            configfile.write(cfgfile)

        if (g := next(filter(lambda g: g.id == guild_id, self.bot.guilds), None)):
            g.leave()
            await interaction.followup.send(f'Left guild {guild_name} ({g.member_count}) id: {guild_id}.', ephemeral = True)

    async def _handle_unban_guild(self, interaction: discord.Interaction):
        raise NotImplementedError
    
    async def _handle_ban_user(self, interaction: discord.Interaction):
        raise NotImplementedError
    
    async def _handle_unban_user(self, interaction: discord.Interaction):
        raise NotImplementedError
    
    async def _handle_status(self, interaction: discord.Interaction):
        interaction.response.send_message(self._status_string())

    snappy_group = app_commands.Group(name="snappy", description="Settings for snappy")

    @snappy_group.command(description="Settings for snappy")
    @app_commands.choices(option = [ app_commands.Choice(name = "enable", value = "enable"),
							        app_commands.Choice(name = "disable", value = "disable"),
                                    app_commands.Choice(name = "ban guild", value = "ban guild"),
                                    app_commands.Choice(name = "ban user", value = "ban user"),
                                    app_commands.Choice(name = "unban guild", value = "unban guild"),
                                    app_commands.Choice(name = "unban user", value = "unban user"),
                                    app_commands.Choice(name = "status", value = "status") ])
    async def settings(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        settings_handlers = {
            "enable"            : self._handle_enable_server,
            "disable"           : self._handle_disable_server,
            "ban guild"         : self._handle_ban_guild,
            "unban guild"       : self._handle_unban_guild,
            "ban user"          : self._handle_ban_user,
            "unban user"        : self._handle_unban_user,
            "status"            : self._handle_status
        }  

async def setup(bot):
    await bot.add_cog(DevCog(bot = bot))
