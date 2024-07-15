# Backend for comment length enforcer
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
       
#   SQLite database with columns sha3_256(f'{user id}:{guild id}) as (unassigned) PK
#                                 user id: int
#                                 guild id: int
#                                 endtime: datetime (Python implemented SQLite feature)
#                                 modifier: str
#  Loop runs every minute to remove old entries
#   - .add_entry()
#   - 

import discord
from discord.ext import tasks, commands
import datetime
import aiosqlite, hashlib, contextlib


class verbosity_manager:

    AWARD_NAME_LONG = 'verbosify'
    AWARD_NAME_SHORT = 'tweetify'
    VERBOSIFY_LENGTH = 255
    TWEETIFY_LENGTH = 256

    DATABASE_FILE = 'punishments.db'
    TABLE_NAME = 'verbosity'

    modifiers = [
        discord.SelectOption(label = AWARD_NAME_LONG, value = f'over {VERBOSIFY_LENGTH} characters'),
        discord.SelectOption(label = AWARD_NAME_SHORT, value = f'under {TWEETIFY_LENGTH} characters')
    ]
    durations = [
        discord.SelectOption(label = 'Remove', value = '0'),
        discord.SelectOption(label = '1 minute', value = '1'),
        discord.SelectOption(label = '5 minutes', value = '5'),
        discord.SelectOption(label = '10 minutes', value = '10'),
        discord.SelectOption(label = '15 minutes', value = '15'),
        discord.SelectOption(label = '30 minutes', value = '30'),
        discord.SelectOption(label = '1 hour', value = '60'),
        discord.SelectOption(label = '2 hours', value = '120'),
        discord.SelectOption(label = '3 hours', value = '180'),
        discord.SelectOption(label = '6 hours', value = '360'),
        discord.SelectOption(label = '12 hours', value = '720'),
        discord.SelectOption(label = '1 day', value = '1440'),
        discord.SelectOption(label = '2 days', value = '2880'),
        discord.SelectOption(label = '3 days', value = '4320'),
        discord.SelectOption(label = '1 week', value = '10080'),
        discord.SelectOption(label = '2 weeks', value = '20160'),
        discord.SelectOption(label = '1 month', value = '43200')
    ]

    VERBOSITY_REMINDER = (
        "Hi {}, Your comment has been automatically removed. "
        "While you are under the effect of {}, your comment must be {}. " 
    )
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def init(self):
        await self._create_table()

    async def _create_table(self):

        QUERY_CREATE_TABLE = (
           f'CREATE TABLE IF NOT EXISTS "{verbosity_manager.TABLE_NAME}" ('
            'rowid INTEGER PRIMARY KEY AUTOINCREMENT,'
            'hash TEXT UNIQUE, '
            'user_id INTEGER, '
            'guild_id INTEGER, '
            'endtime TIMESTAMP, ' # python-implemented SQLite feature
            'option TEXT '
            ');'
        ) #.format(table_name)

        async with aiosqlite.connect(verbosity_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_CREATE_TABLE):
                await database.commit()

    def id_hash(self, user_id, guild_id) -> str:
        return hashlib.sha3_256(bytes(f"{user_id}:{guild_id}", encoding='utf8'), usedforsecurity = False).hexdigest()
    
    @tasks.loop(minutes = 1.0)
    async def check_verbosityexpiry(self):

        QUERY_REMOVE_EXPIRED = (
            f'DELETE FROM "{verbosity_manager.TABLE_NAME}" WHERE ? > endtime;'
        ) # end datetime()

        async with aiosqlite.connect(verbosity_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_REMOVE_EXPIRED, (datetime.datetime.now(),)):
                await database.commit()

    async def add_entry(self, user_id: int, guild_id: int, duration: int, option: str):

        QUERY_ADD_USER = (
            f'INSERT INTO "{verbosity_manager.TABLE_NAME}" (hash, user_id, guild_id, endtime, option)  VALUES (?, ?, ?, ?, ?) '
             'ON CONFLICT(hash) DO UPDATE SET endtime = ?, option = ?;'
        ) # (hash, user id, guild id, end datetime(), phrase, end datetime(), phrase)

        QUERY_REMOVE_USER = (
            f'DELETE FROM "{verbosity_manager.TABLE_NAME}" WHERE hash = ?;'
        ) # (hash,)

        endtime = datetime.datetime.now() + datetime.timedelta(minutes = float(duration))
        async with aiosqlite.connect(verbosity_manager.DATABASE_FILE) as database:
            if duration == 0:
                async with database.execute(QUERY_REMOVE_USER, (self.id_hash(user_id, guild_id),)):
                    pass
            else:
                async with database.execute(QUERY_ADD_USER, (self.id_hash(user_id, guild_id), user_id, guild_id, endtime, option, endtime, option)):
                    pass
            await database.commit()

    async def remove_all(self):

        QUERY_REMOVE_ALL = (
            'DELETE FROM "{}";'
        )

        async with aiosqlite.connect(verbosity_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_REMOVE_ALL.format(verbosity_manager.TABLE_NAME)):
                await database.commit()

    async def process_message(self, user: str, user_id: int, guild_id: int, text: str, msg: discord.Message):

        QUERY_GET_USER = (
            f'SELECT option FROM "{verbosity_manager.TABLE_NAME}" WHERE hash = ?;'
        )

        if guild_id is None:
            return
        async with aiosqlite.connect(verbosity_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_GET_USER.format(verbosity_manager.TABLE_NAME), (self.id_hash(user_id, guild_id,),)) as cursor:
                option = await cursor.fetchall()
        if option:
            option = option[0][0]
            addtl_text = next(filter(lambda p: p.label == option, verbosity_manager.modifiers)).value
            if option == verbosity_manager.AWARD_NAME_LONG:
                if len(text) > verbosity_manager.VERBOSIFY_LENGTH:
                    return
            elif option == verbosity_manager.AWARD_NAME_SHORT:
                if len(text) < verbosity_manager.TWEETIFY_LENGTH:
                    return
            
            await msg.reply(verbosity_manager.VERBOSITY_REMINDER.format(user, option, addtl_text))
            try:
                await msg.delete()
            except discord.errors.Forbidden as e:
                await msg.channel.send(f'Please grant {self.bot.user.display_name} "manage messages" permissions for this feature to function correctly.', delete_after = 30.0)