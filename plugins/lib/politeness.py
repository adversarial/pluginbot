# Backend for polite_cog - reminds a user to say a specified phrase or their message is removed
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
#                                 phrase: str 
#  Loop runs every minute to remove old entries
#   - .add_entry()
#   - 

import discord, discord.ui
from discord.ext import commands, tasks

import aiosqlite, datetime, hashlib

class politeness_manager:
    DATABASE_FILE = 'punishments.db'
    TABLE_NAME    = 'politeness'

    phrases = [
        discord.SelectOption(label = 'I will not plagiarize', value = 'educational community'),
        discord.SelectOption(label = 'I respect your identity', value = 'intersectional community'),
        discord.SelectOption(label = "Custom", value = "custom")
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

    POLITENESS_REMINDER = (
        "Hello {}, your comment has been automatically removed. "
        "You've been noticed by our moderators as problematic, so your messages need to show "
        "love and acceptance towards the {}. You can resubmit your comment with '{}' included."
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def init(self):
        await self._create_table()
        
    async def _create_table(self):

        QUERY_CREATE_TABLE = (
           f'CREATE TABLE IF NOT EXISTS "{politeness_manager.TABLE_NAME}" ('
            'rowid INTEGER PRIMARY KEY AUTOINCREMENT,'
            'hash TEXT UNIQUE, '
            'user_id INTEGER, '
            'guild_id INTEGER, '
            'endtime TIMESTAMP, ' # python-implemented SQLite feature
            'phrase TEXT '
            ');'
        ) #.format(table_name)

        async with aiosqlite.connect(politeness_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_CREATE_TABLE):
                await database.commit()        

    def id_hash(self, user_id, guild_id) -> str:
        return hashlib.sha3_256(bytes(f"{user_id}:{guild_id}", encoding='utf8'), usedforsecurity = False).hexdigest()
    
    @tasks.loop(minutes = 1.0)
    async def check_politeexpiry(self):

        QUERY_REMOVE_EXPIRED = (
            f'DELETE FROM "{politeness_manager.TABLE_NAME}" WHERE ? > endtime;'
        ) # end datetime()

        async with aiosqlite.connect(politeness_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_REMOVE_EXPIRED, (datetime.datetime.now(),)):
                await database.commit()

    async def add_entry(self, user_id: int, guild_id: int, duration: int, phrase: str):

        QUERY_ADD_USER = (
            f'INSERT INTO "{politeness_manager.TABLE_NAME}" (hash, user_id, guild_id, endtime, phrase)  VALUES (?, ?, ?, ?, ?) '
             'ON CONFLICT(hash) DO UPDATE SET endtime = ?, phrase = ?;'
        ) # (hash, user id, guild id, end datetime(), phrase, end datetime(), phrase)

        QUERY_REMOVE_USER = (
            f'DELETE FROM "{politeness_manager.TABLE_NAME}" WHERE hash = ?;'
        ) # (hash,)

        endtime = datetime.datetime.now() + datetime.timedelta(minutes = float(duration))
        async with aiosqlite.connect(politeness_manager.DATABASE_FILE) as database:
            if duration == 0:
                async with database.execute(QUERY_REMOVE_USER, (self.id_hash(user_id, guild_id),)):
                    pass
            else:
                async with database.execute(QUERY_ADD_USER, (self.id_hash(user_id, guild_id), user_id, guild_id, endtime, phrase, endtime, phrase)):
                    pass
            await database.commit()

    async def remove_all(self):

        QUERY_REMOVE_ALL = (
            'DELETE FROM "{}";'
        )

        async with aiosqlite.connect(politeness_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_REMOVE_ALL.format(politeness_manager.TABLE_NAME)):
                await database.commit()

    # returns true if the message needs to be "fixed"
    # returns false if can be ignored
    async def process_message(self, user: str, user_id: int, guild_id: int, text: str, msg: discord.Message):

        QUERY_GET_USER = (
            f'SELECT phrase FROM "{politeness_manager.TABLE_NAME}" WHERE hash = ?;'
        )

        if guild_id is None:
            return
        async with aiosqlite.connect(politeness_manager.DATABASE_FILE) as database:
            async with database.execute(QUERY_GET_USER.format(politeness_manager.TABLE_NAME), (self.id_hash(user_id, guild_id,),)) as cursor:
                phrase = await cursor.fetchall()
        if phrase:
            phrase = phrase[0][0]
            if phrase.lower() not in text.lower():
                if phrase.lower() in [ p.label.lower() for p in politeness_manager.phrases ]:
                    addtl_text = next(filter(lambda p: p.label == phrase, politeness_manager.phrases)).value
                else:
                    addtl_text = 'community'
                await msg.reply(politeness_manager.POLITENESS_REMINDER.format(user, phrase, addtl_text, phrase), mention_author = False)
                try:
                    await msg.delete()
                except discord.errors.Forbidden as e:
                    await msg.channel.send(f'Please grant {self.bot.user.display_name} "manage messages" permissions for this feature to function correctly', delete_after = 30.0)