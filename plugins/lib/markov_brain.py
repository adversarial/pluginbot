# markov chain SQLite backend
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

###################################################################################
# SQL implementation
###################################################################################
import aiosqlite
import typing
import contextlib
import json
import hashlib
import random

class markov_table:
    TABLE_BASE_NAME = 'markov'
    def __init__(self, 
                 id,
                 name,
                 database: aiosqlite.Connection,
                 database_filename: str):
        self.name = str(id) + markov_table.TABLE_BASE_NAME + name
        self.database = database
        self.database_filename = database_filename

    async def _create_table(self):
        raise NotImplementedError
    
    async def _drop_table_statement(self):
        async with aiosqlite.connect(self.database_filename) as database:
            async with database.execute(f'DROP TABLE "{self.name}";'):
                await self.database.commit()

    async def _reset_table(self):
        async with aiosqlite.connect(self.database_filename) as database:
            async with database.execute(f'DELETE FROM "{self.name}";'):
                await self.database.commit()
        
class seed_table(markov_table):
    def __init__(self, 
                 id,
                 database: aiosqlite.Connection,
                 database_filename: str):
        super().__init__(id, 'seed', database, database_filename)


    async def contains(self, seed, database):
        QUERY_CONTAINS_SEED = (
            f'SELECT EXISTS(SELECT rowid FROM "{self.name}" WHERE seed = ?);'
        ) # (seed,)

        async with database.execute(QUERY_CONTAINS_SEED, (seed,)) as cursor:
            return bool((await cursor.fetchone())[0])

    async def _create_table(self):

        QUERY_CREATE_SEED_TABLE = (
            f'CREATE TABLE IF NOT EXISTS "{self.name}" ('
            'rowid INTEGER PRIMARY KEY AUTOINCREMENT, ' 
            'seed TEXT UNIQUE'
            ');'
        )

        async with aiosqlite.connect(self.database_filename) as database:
            async with database.execute(QUERY_CREATE_SEED_TABLE):
                await self.database.commit()

class next_state_table(markov_table):
    def __init__(self, id, database, database_filename, seed_table: markov_table):
        self.seed_table = seed_table
        super().__init__(id, 'next_states', database, database_filename)
    
    # value should be a tuple ('key', 'value')
    # def __contains__(self, value):
    async def contains(self, value, database):
        QUERY_CONTAINS_NEXT_STATE = (
            f'SELECT EXISTS(SELECT rowid FROM "{self.name}" '
             'WHERE next_state = ? '
            f'AND seed_id = (SELECT DISTINCT rowid FROM "{self.seed_table.name}" WHERE seed = ?));'
        ) # (seed,)

        seed, next_state = value
        async with database.execute(QUERY_CONTAINS_NEXT_STATE, (next_state, seed)) as cursor:
            return bool((await cursor.fetchone())[0])
        
    async def _create_table(self):

        QUERY_CREATE_NEXT_STATE_TABLE = (
            f'CREATE TABLE IF NOT EXISTS "{self.name}" ('
             'rowid INTEGER PRIMARY KEY AUTOINCREMENT, '
             'hash TEXT UNIQUE, '
             'next_state TEXT, '
             'count INTEGER, '
             'seed_id INTEGER, '
            f'FOREIGN KEY (seed_id) REFERENCES "{self.seed_table.name}" (rowid)'
            ');'
        ) # .format(next_state_table, seed_table)

        async with aiosqlite.connect(self.database_filename) as database:
            async with database.execute(QUERY_CREATE_NEXT_STATE_TABLE):
                await database.commit()

class markov_brain:
    def __init__(self,
                 id,
                 database: aiosqlite.Connection,
                 database_filename = None,
                 max_entries = None,
                 copy_seed_table_name = None,
                 copy_next_state_table_name = None):
        self._id = id
        self.database = database
        self.database_filename = database_filename
        self.max_entries = max_entries
        self._lock = contextlib.nullcontext()

        self.copy_seed_table_name = copy_seed_table_name
        self.copy_next_state_table_name = copy_next_state_table_name

        self.seed_table = seed_table(id, database, database_filename)
        self.next_state_table = next_state_table(id, database, database_filename, self.seed_table)

    async def init(self):
        await self.seed_table._create_table()
        await self.next_state_table._create_table()
        if self.copy_seed_table_name and self.copy_next_state_table_name:
            await self._copy(self.copy_seed_table_name, self.copy_next_state_table_name)       
    
    #def __contains__(self, seed):
    #    return seed in self.seed_table
    async def contains(self, seed):
        return await self.seed_table.contains(seed, self.database)

    # multiple threads can use a read connection
    async def _execute_read(self, connection: aiosqlite.Connection, statement, args: typing.Optional[tuple] = None):
        async with connection.execute(statement, parameters = args) as cursor:
            return await cursor.fetchall()
    
    # only one thread can use a write connection though
    # open a connection in the top level function and pass to here
    # call commit at end of procedure that uses this
    async def _execute_write(self, connection: aiosqlite.Connection, statement, args: typing.Optional[tuple] = None):
        async with connection.execute(statement, parameters = args):
            pass
    
    async def _copy(self, source_seed_table_name, source_next_states_table_name):
        QUERY_COPY_SEEDS = (
            f'INSERT INTO "{self.seed_table.name}" (seed) '
            f'SELECT seed FROM "{source_seed_table_name}";'
        ) 

        QUERY_COPY_NEXT_STATES = (
            f'INSERT INTO "{self.next_state_table.name}" (hash, next_state, count, seed_id) '
            f'SELECT hash, next_state, count, seed_id FROM "{source_next_states_table_name}";'
        )

        async with aiosqlite.connect(self.database_filename) as database:
            async with database.executescript(f'DELETE FROM {self.seed_table.name}; DELETE FROM {self.next_state_table.name};'):
                pass
            await database.commit()
            async with database.executescript(QUERY_COPY_SEEDS + QUERY_COPY_NEXT_STATES):
                pass
            await database.commit()
            
    async def _dbg(self):
        print(await self._execute_read(self.database, f'SELECT rowid, seed FROM "{self.seed_table.name}";'))
        print(await self._execute_read(self.database, f'SELECT next_state, count, seed_id FROM "{self.next_state_table.name}";'))

    def id(self):
        return self._id
    
    def kv_hash(self, key, value):
        return hashlib.sha3_256(bytes(f"{key}:{value}", encoding='utf8'), usedforsecurity = False).hexdigest()

    # doesn't commit to allow optimization of entering lists
    async def _internal_add_next_state(self, connection: aiosqlite.Connection, key: str, value: str, count: int = 1):
        QUERY_ADD_SEED = (
            f'INSERT OR IGNORE INTO "{self.seed_table.name}" (seed) VALUES (?);'
        ) # (seed,)
                
        QUERY_INSERT_OR_INCREMENT_NEXT_STATE = (
            f'INSERT INTO "{self.next_state_table.name}" (hash, next_state, count, seed_id) '
            f'VALUES (?, ?, ?, (SELECT DISTINCT rowid FROM "{self.seed_table.name}" WHERE seed = ?)) '
            'ON CONFLICT(hash) '
            'DO UPDATE SET count = count + ?;'
        ) # (hash, value, count, key, count)
        
        await self._execute_write(connection, QUERY_ADD_SEED, args = (key,))
        await self._execute_write(connection, QUERY_INSERT_OR_INCREMENT_NEXT_STATE, args = (self.kv_hash(key, value), value, count, key, count))

    async def add_next_state(self, key: str, value: str, count: int = 1):
        with aiosqlite.connect(self.database_filename) as database:
            await self._internal_add_next_state(database, key, value, count)
            await database.commit()
    
    async def get_next_states(self, key):

        QUERY_GET_NEXT_STATES = (
            f'SELECT next_state, count FROM "{self.next_state_table.name}" '
            f'WHERE seed_id = (SELECT DISTINCT rowid FROM "{self.seed_table.name}" WHERE seed = ?)'
        ) # (seed,)

        return await self._execute_read(self.database, QUERY_GET_NEXT_STATES, (key,))
  

    # import old version that used in-memory dictionary
    async def import_json(self, filename):
        with open(filename, 'r') as file:
            await self.import_chain(json.load(file))
            
    # import old version that used in-memory dictionary
    async def import_chain(self, chain):
        async with aiosqlite.connect(self.database_filename) as connection:
            for key in chain:
                # todo: batch add
                for value, count in chain[key]:
                    await self._internal_add_next_state(connection, key, value, count)
            await connection.commit()

    # export old version that used in-memory dictionary
    async def export_json(self, filename):

        QUERY_GET_ALL_KEYS = f'SELECT seed FROM "{self.seed_table.name}";'

        chain = { }
        keys = await self._execute_read(self.database, QUERY_GET_ALL_KEYS)
        for key in keys:
            values = await self.get_next_states(key[0])
            chain[key[0]] = values
        with open(filename, 'w+') as file:
            json.dump(chain, file)

    async def load(self):
        await self.database.rollback()

    async def dump(self):
        await self.database.commit()

    async def remove(self):
        async with aiosqlite.connect(self.database_filename) as database:
            async with database.executescript(f'DROP TABLE "{self.next_state_table.name}"; DROP TABLE "{self.seed_table.name}";'):
                await database.commit()

    async def reset(self):
        await self.seed_table._reset_table()
        await self.next_state_table._reset_table()

    async def get_random_seed(self):

        QUERY_GET_RANDOM_SEED = (
            f'SELECT seed FROM "{self.seed_table.name}" ORDER BY random() LIMIT 1;'
        )

        result = await self._execute_read(self.database, QUERY_GET_RANDOM_SEED)
        if result is not None:
            return result[0][0]
    
    async def get_fuzzy_seed(self, seed, seperator, is_prefix_only = False):

        QUERY_GET_FUZZY_SEED = (
            f'SELECT seed FROM "{self.seed_table.name}" WHERE seed LIKE ? ORDER BY random() LIMIT 1;'
        )

        if random.randint(0, 1) > 0:
            search_str1 = seed + seperator + '_%'
            search_str2 = '%_' + seperator + seed
        else:
            search_str1 = '%_' + seperator + seed
            search_str2 = seed + seperator + '_%'
    
        result = await self._execute_read(self.database, QUERY_GET_FUZZY_SEED, (search_str1,))
        if not result:
            result = await self._execute_read(self.database, QUERY_GET_FUZZY_SEED, (search_str2,))
            if not result:
                raise KeyError
        return result[0][0]
    
    async def get_previous_state(self, seed, forward_seed, seperator):

        QUERY_GUESS_PREVIOUS_SEED = (
           f'SELECT rowid, seed FROM "{self.seed_table.name}" '
            'WHERE seed LIKE ? '
            'AND EXISTS(SELECT next_state '
                       f'FROM "{self.next_state_table.name}" '
                        'WHERE next_state = ? '
                        'AND seed_id = rowid) '
            'ORDER BY random() '
            'LIMIT 1;'
        )
        #QUERY_FILTER_PREVIOUS_SEEDS = (
        #    f'SELECT EXISTS(SELECT seed FROM "{self.seed_table.name}" '
        #    f'WHERE EXISTS(SELECT next_state FROM "{self.next_state_table.name}" '
        ##                  'WHERE next_state = ? '
        #                 f'AND seed_id = (SELECT DISTINCT rowid FROM "{self.seed_table.name}" WHERE seed = ?)));' 
        #)

        results = await self._execute_read(self.database, QUERY_GUESS_PREVIOUS_SEED, ('%_' + seperator + seed, forward_seed))
        if not results:
            raise KeyError
        return results[0][1]
        #if results:
        #    for item in results:
        #        if (await self._execute_read(self.database, QUERY_FILTER_PREVIOUS_SEEDS, (forward_seed, item[0])))[0][0]:
        #            return item[0]
        #raise KeyError
    