# Entrypoint for modular discord bot
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from bot import bot
from bot import config

import logging
import logging.handlers

def init_log_file():
    logging.getLogger('discord').setLevel(logging.INFO)
    logging.getLogger('discord.http').setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
        filename = config['log_file_name'],
        encoding ='utf-8',
        maxBytes = 0xFFFFF,
        backupCount = 1
    )
    handler.setFormatter(logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', '%Y-%m-%d %H:%M:%S', style='{'))
    logging.getLogger('discord').addHandler(handler)
    return logging.FileHandler(filename = config['log_file_name'], encoding='utf-8', mode='a')

if __name__ == '__main__':
    with open('.secret', 'r') as secrets:
        secret = secrets.readline()
    bot.run(secret, log_handler = init_log_file(), root_logger = True)
