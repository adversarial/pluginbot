# Config.ini parser for discord modular bot
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from configparser import ConfigParser
import json

import argparse
parser = argparse.ArgumentParser(prog='Discord bot skeleton',
                                 description='Module based python bot.')
parser.add_argument('configfilename', nargs = '?', default = 'config.ini', help = 'Specify an optional config file.')
args = parser.parse_args()

config = { }
configfile = ConfigParser()
configfile.read(args.configfilename)

config['filename'] = args.configfilename
# constants
config['command_prefix'] = configfile['constants']['command_prefix']
config['bot_name'] = configfile['constants']['bot_name']
config['log_file_name'] = configfile['constants']['log_file']

# privileged command access
config['owner_ids'] = json.loads(configfile['settings']['owner_ids'])
config['mod_ids'] = json.loads(configfile['settings']['mod_ids'])

# plugin loading settings
config['plugin_directory'] = configfile['plugins']['plugin_directory']
config['plugin_whitelist_only'] = configfile.getboolean('plugins', 'whitelist_only')
config['plugin_whitelist'] = json.loads(configfile['plugins']['plugin_whitelist'])

# whitelists
config['guild_whitelist'] = json.loads(configfile['whitelists']['guild_ids'])
config['user_whitelist'] = json.loads(configfile['whitelists']['user_ids'])

# blacklists
config['guild_blacklist'] = json.loads(configfile['blacklists']['guild_ids'])
config['user_blacklist'] = json.loads(configfile['blacklists']['user_ids'])

# bans
config['guild_banlist'] = json.loads(configfile['banlists']['guild_ids'])
config['user_banlist'] = json.loads(configfile['banlists']['user_ids'])