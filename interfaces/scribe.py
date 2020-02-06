import os
import argparse
import datetime
import time
import sqlite3
import logging
import threading
import uuid
import traceback
import sys
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit

try:
    logr = logging.getLogger("IfaceScribe")
    # get a logger
    log = logr.log
    crit = logr.critical
    error = logr.error
    warn = logr.warning
    info = logr.info
    debug = logr.debug
    # take the logger methods that record messages and 
    # convert them into simple one word functions
except Exception as err:
    logging.critical("Failed to configure logging IfaceScribe.")
    logging.exception(err)
    # print the message to the root logger
    raise err

# def get_timestamp(form="%Y-%m-%d %H:%M:%S.%f"):
#     return datetime.datetime.now().strftime(form)

def get_uuid():
    return uuid.uuid4()

def get_timestamp():
    return datetime.datetime.now()

def row_factories(*args):
    """
    Function to wrap all factory functions, and add a parser to 
    pick and choose which to use at any given time.
    """
    row_factory = sqlite3.Row
    def tuple_factory(cur, row):
        return row
    def dict_factory(cur, row):
        d = {}
        # junk because they're always None 'https://docs.python.org/2/library/sqlite3.html#sqlite3.Cursor.description'
        for idx, (header,junk1,junk2,junk3,junk4,junk5,junk6) in enumerate(cur.description):
            d[header] = row[idx]
        return d
    def obj_factory(cur, row):
        obj = argparse.Namespace()
        for idx, (header,junk1,junk2,junk3,junk4,junk5,junk6) in enumerate(cur.description):
            setattr(obj, header, row[idx])
        return obj
    setattr(row_factories, "default", tuple_factory)
    # setting it as an attribute of the function lets us change the 
    # default later if we need this function in a different context
    factories_dict = {name.replace("_factory", ""):fnc for name,fnc in locals().items() if name.find("_factory") != -1}
    # create a dict mapping local names to functions
    factories_list = factories_dict.keys()
    # get a list of those local names
    parser = argparse.ArgumentParser(description="choose what data format sql commands return.")
    parser.add_argument("factory",
                        choices=factories_list,
                        help="What data type should be output.")
    args = parser.parse_args(args)
    return factories_dict.get(args.factory, row_factories.default)
    # this seemed better than a long if-else chain, and having 
    # to make sure 'choices' gets updated with every new function

def get_path(path):
    """
    Convert a full path
    """
    # print("Received {}".format(path))
    path = os.path.expandvars(path)
    # print("{}".format(path))
    path = os.path.expanduser(path)
    # print("{}".format(path))
    path = os.path.normpath(path)
    # print("{}".format(path))
    path = os.path.realpath(path)
    # print("{}".format(path))
    return path


def dir_path(d,suppress=False):
    """
    Convert a string into a full path to a folder, 
    ensuring the folder exists.
    """
    d = get_path(d)
    if not os.path.isdir(d) and not (suppress is True):
        raise ValueError("{} does not appear to be a proper path to a folder.".format(d))
    return d

def file_path(f,suppress=False):
    """
    Convert a string into a full path to a file,
    ensuring the file exists.
    """
    f = get_path(f)
    if not os.path.isfile(f) and not (suppress is True):
        raise ValueError("{} does not appear to be a proper path to a file.".format(f))
    return f

class SQLiteInterface(object):
    """docstring for SQLiteInterface"""
    # schema = "./SCHEMA_email_data.sql"
    # fixtures = "./FIXTURES_email_data.sql"
    def __init__(self, database, schema=None, fixtures=None, row_factory=None):
        super(SQLiteInterface, self).__init__()
        # self._row_factory = getattr(row_factories,"default")
        self._sql_functions = [ ("GET_UUID", 0, get_uuid, ) ]
        self._row_factory = row_factories("dict")
        try:
            if row_factory != None:
                self._row_factory = row_factories(row_factory)
        except Exception as err:
            logging.exception(err)
        self.__schema = None
        self.__fixtures = None
        if schema:
            self.__schema = file_path(schema)
        if fixtures:
            self.__fixtures = file_path(fixtures)
        self.database = database
        self.create_lock()

    @property
    def database(self):
        # getter for database path
        return self._database

    @property
    def db_name(self):
        # get basename for database file
        file = os.path.basename(self.database)
        name, ext = os.path.splitext(file)
        return name
    
    @database.setter
    def database(self, value):
        def read_sql_file_into_db(sql_file, db_file):
            with sqlite3.connect(db_file) as db:
                # connect to the database file
                cur = db.cursor()
                with open(sql_file,"r") as f:
                    # read the sqlite instructions line by line
                    command = ""
                    line = f.readline()
                    while line:
                        command += line
                        # add the line to the variable command as a buffer
                        if line.find(");") != -1:
                            # when we reach the end of a command statement
                            try:
                                cur.executescript(command)
                                # execute the command
                            except Exception as err:
                                # print(command)
                                logging.info(command)
                                logging.exception(err)
                                raise err
                            command = ""
                            # clear the buffer
                        line = f.readline()
                        # read the next line
                    # now it'll execute each command individually, and print the command if it fails
        new_file = False
        try:
            db_path = file_path(value)
            # confirm its a file

            # os.remove(value)
            # new_file = True

        except Exception as err:
            db_path = file_path(value, suppress=True)
            # get the full path to where we want it to be
            new_file = True
            # note that we'll need to make the file
            
        self._database = db_path
        if self.__schema == None:
            try:
                self.__schema = file_path(os.path.join(os.path.dirname(db_path),"SCHEMA_"+self.db_name+".sql"))
                # Check if a schema exists in the same directory
            except Exception as err:
                # aux_debug("Failed to find schema for {}:{}".format(value,err))
                logging.exception(err)
                self.__schema = None
        if self.__fixtures == None:
            try:
                self.__fixtures = file_path(os.path.join(os.path.dirname(db_path),"FIXTURES_"+self.db_name+".sql"))
                # Check if a fixtures exists in the same directory
            except Exception as err:
                # aux_debug("Failed to find fixtures for {}:{}".format(value,err))
                logging.exception(err)
                self.__fixtures = None
        if new_file:
            with sqlite3.connect(self._database) as db:
                # connect/create the db file
                cur = db.cursor()
                # if self.schema:
                #     # aux_debug("Using schema")
                #     aux_debug("Using schema:'''{}'''".format(self.schema))
                # cur.executemany(self.schema)
                result = read_sql_file_into_db(self._schema, self.database)
                # aux_debug(result)
                # execute the sql commands found in the file
                # if self.fixtures:
                #     # aux_debug("Using fixtures")
                #     aux_debug("Using fixtures:'''{}'''".format(self.fixtures))
                # cur.executemany(self.fixtures)
                result = read_sql_file_into_db(self._fixtures, self.database)
                # aux_debug(result)
                # execute the sql commands found in the file

    @property
    def _schema(self):
        # read only
        return self.__schema
        # path to a sql file that holds the schema

    @property
    def _fixtures(self):
        # read only
        return self.__fixtures
        # path to a sql file that holds the fixtures

    @property
    def schema(self):
        # read only;
        # contents of the schema file
        result = ""
        if self._schema != None:
            with open(self._schema,"r") as f:
                result = f.read()
        return result

    @property
    def fixtures(self):
        # read only;
        # contents of the fixtures file
        result = ""
        if self._fixtures != None:
            with open(self._fixtures,"r") as f:
                result = f.read()
        return result

    @property
    def row_factory(self):
        # get the prefered row_factory to use after connecting to the database
        return self._row_factory

    @row_factory.setter
    def row_factory(self, value):
        # set the prefered row_factory to use after connecting to the database;
        # accepts a function, or a string to pass to row_factories
        if isinstance(value, str):
            value = row_factories(value)
        self._row_factory = value

    @property
    def _connection(self):
        # connect to the sql database
        return self.__connection
        # sqlite3.connect(self.database)
    
    @_connection.setter
    def _connection(self, value):
        # set values i?, n the database
        self.__connection = value
        for (name, num_params, func) in self._sql_functions:
            info(f"adding {name} function to connection")
            self.__connection.create_function(name, num_params, func)


    @property
    def _cursor(self):
        # cursor for the sql database
        return self.__cursor        

    def create_lock(self):
        self.lock = threading.RLock()

    def commit(self):
        self._connection.commit()

    def acquire(self):
        self.__lastrowid = None
        self.lock.acquire()
        self._connection = sqlite3.connect(self.database)
        self.__cursor = self.__connection.cursor()
        # get and store the sqlite3 connection in the hidden attribute

    def release(self):
        self.__lastrowid = self._cursor.lastrowid
        self._connection.close()
        self.lock.release()

    def __enter__(self):
        self.acquire()
        self._connection.row_factory = self.row_factory
        self.__cursor = self.__connection.cursor()
        return self._cursor
        # return a sqlite cursor to the database

    def __exit__(self, type, value, traceback):
        self.__lastrowid = self._cursor.lastrowid
        self._connection.commit()
        self.release()

    @property
    def lastrowid(self):
        # get the last row id the cursor set
        if not hasattr(self, "__lastrowid"):
            return None
        return self.__lastrowid

    @property
    def tables(self):
        if not hasattr(self,"_tables"):
            self.acquire()
            self._connection.row_factory = self.row_factory
            self.__cursor = self.__connection.cursor()
            self.__cursor.execute("SELECT name,tbl_name FROM sqlite_master WHERE type='table'")
            rows = [ row.get("name") for row in self.__cursor.fetchall() if row.get("name") != "sqlite_sequence" ]
            self.release()
            self._tables = rows
        return self._tables

    def get_columns(self, table):
        if table not in self.tables:
            raise KeyError(f"table '{table}' not found in database")
        if not hasattr(self,"_columns"):
            self._columns = {}
        if self._columns.get(table) is None:
            self.acquire()
            self._connection.row_factory = self.row_factory
            self.__cursor = self.__connection.cursor()
            self.__cursor.execute(f"SELECT * FROM {table}")
            self._columns[table] = [ row for row,val in self.__cursor.fetchone().items() ]
            self.release()
        return self._columns[table]

    def update_view(self, view_name):
        # drop and create a view again
        success = False
        view = None
        initial_factory = self.row_factory
        self.row_factory = "dict"
        self.acquire()
        self._connection.row_factory = self.row_factory
        db = self.__connection.cursor()
        rows = db.execute("SELECT name,tbl_name,sql FROM sqlite_master WHERE type='view'")
        result = [row for row in rows.fetchall()]
        for v in result:
            if v.get("name") == view_name or v.get("tbl_name") == view_name:
                # we've confirmed that the table exists in our db
                view = v
                # hold onto its config
        if view != None and view.get("sql",None) != None:
            # DROP VIEW IF EXISTS [Contacts];
            # CREATE VIEW IF NOT EXISTS [Contacts] AS SELECT users.role, users.name, users.username, emails.data as address FROM ((emails INNER JOIN users_emails ON emails.id=users_emails.email_id) INNER JOIN users ON users.id==users_emails.user_id);
            query = "DROP VIEW IF EXISTS [{}];".format(view_name)
            rows = db.execute(query)
            # drop the old view
            query = view.get("sql")
            if query.upper().find("IF NOT EXISTS") == -1:
                query = query.replace("CREATE VIEW","CREATE VIEW IF NOT EXISTS")
            rows = db.execute(query)
            # create the view again
            success = True
        self.release()
        self.row_factory = initial_factory
        return success

class Scribe(object):
    """
    An object to handle recording (and retrieving) game states to a sqlite database
    """
    __rowids = {
        # create a hidden dictionary that will hold the rowids 
        # for the different things used in this particular game
        "game_settings": None,
        # is INT for the rowid for the set of game settings used
        "agent": None,
        # After a dqn is created, is INT for the rowid for the DQN agent used
        "player": None,
        # is INT for the rowid for the player for the current game
        "game_type": None,
        # is INT for the rowid for this game/'type of game'; 
        # different from game instance, this represents settings AND player AND version;
        # a game can have may instances, but a game instance only occurs once
        "game_instance": None,
        # is INT for the rowid for the current game instance
        "command": None,
        # After a command is executed, is created;
        # is INT for the rowid for last command to be executed
        "fruit_species": {},
        # is a dict mapping fruit names to their rowids
        "obstacles": [],
        # a list of INT for the rowids for obstacles created (ordered by creation)
        "fruits": [],
        # a list of INT for the rowids 
        # for fruits created and currently existing (ordered by creation)
        "segments": [],
        # is a list of INT for the rowids
        # for segments created and currently existing (ordered by creation)
        "state": None,
        # is INT for the rowid of the last state entered
        # game_settings
        # agents
        # players
        # games
        # game_instances
        # commands
        # commands_executed
        # fruits
        # obstacles
        # segments
        # fruit_instances
        # states
        # states_fruits
        # states_obstacles
        # states_snakes
        # snake_body_parts
    }
    def __init__(self, db):
        super(Scribe, self).__init__()
        self.db = db
        self.db.acquire()

    def __del__(self):
        if hasattr(self, "_db"):
            self.db.commit()
            self.db.release()

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, value):
        # SQLiteInterface(database, schema=None, fixtures=None, row_factory=None)
        if isinstance(value, str):
            value = SQLiteInterface(value)
        elif isinstance(value, SQLiteInterface):
            pass
        else:
            raise TypeError(f"Expected str for a database, or a SQLiteInterface object, not {type(value)}")
        self._db = value
        db = value.database

    @property
    def db_name(self):
        return self.db.db_name

    @property
    def db_path(self):
        return self.db.database

    @property
    def lastrowid(self):
        # get the last row id the cursor set
        return self.db.lastrowid

    @property
    def cur(self):
        return self.db._cursor

    @property
    def get_game_settings(self):
        value = self.__rowids.get("game_settings", None)
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value
    
    @property
    def get_agent(self):
        value = self.__rowids.get("agent", None)
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value
    
    @property
    def get_player(self):
        value = self.__rowids.get("player", None)
        # debug(f"retrieving player_id = {value} {type(value)}")
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value
    
    @property
    def get_game_type(self):
        value = self.__rowids.get("game_type", None)
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value
    
    @property
    def get_game_instance(self):
        value = self.__rowids.get("game_instance", None)
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value
    
    @property
    def get_command(self):
        value = self.__rowids.get("command", None)
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value
    
    @property
    def get_state(self):
        value = self.__rowids.get("state", None)
        if value is None or isinstance(value, uuid.UUID):
            pass
        else:
            value = uuid.UUID(value)
        return value

    @property
    def get_obstacles(self):
        value = self.__rowids.get("obstacles", [])
        value = value if isinstance(value, list) else []
        if len(value) > 0 and not all([ isinstance(v, uuid.UUID) for v in value ]):
            raise ValueError(f"Expected a list of integers, not {value}")
        return value

    @property
    def get_fruits(self):
        value = self.__rowids.get("fruits", [])
        value = value if isinstance(value, list) else []
        if len(value) > 0 and not all([ isinstance(v, uuid.UUID) for v in value ]):
            raise ValueError(f"Expected a list of integers, not {value}")
        return value

    @property
    def get_segments(self):
        value = self.__rowids.get("segments", [])
        value = value if isinstance(value, list) else []
        if len(value) > 0 and not all([ isinstance(v, uuid.UUID) for v in value ]):
            raise ValueError(f"Expected a list of integers, not {value}")
        return value

    @property
    def get_fruit_species(self):
        value = self.__rowids.get("fruit_species", {})
        value = value if isinstance(value, dict) else {}
        if len(value) > 0 and not all([ (isinstance(k,str) and isinstance(v, uuid.UUID)) for k,v in value.items() ]):
            raise ValueError(f"Expected a dictionary mapping fruit species names to their ids, not {value}")
        return value

    def record_command(self, command):
        """
        Record a command to the sql database.
        """
        timestamp = get_timestamp()
        command_id = get_uuid()
        game_id = self.get_game_instance
        if game_id is not None:
            self.insert("INSERT OR REPLACE INTO 'commands_executed' ('id', 'timestamp', 'command', 'game') VALUES (?, ?, ?, ?) ",
                (command_id, timestamp, command, game_id, )
                )
            self.__rowids["command"] = command_id

    def record_agent(self, agent):
        """
        Record a agent to the sql database.
        """
        agent_id = get_uuid()
        self.insert("INSERT OR REPLACE INTO 'agents' ('id', 'weights', 'gamma') VALUES (?, ?, ?) ",
            (agent_id, agent.weights, agent.gamma, )
            )
        self.__rowids["agent"] = agent_id

    def record_player(self, player):
        """
        Record a player to the sql database.
        """
        debug(f"player is {player}")
        debug(f"self.get_agent is {self.get_agent}")
        agent = self.get_agent
        if agent:
            player_id = self.cur.execute("SELECT id FROM players WHERE name=? and agent=?",(player,agent,)).fetchall()
        else:
            player_id = self.cur.execute("SELECT id FROM players WHERE name=? and agent is NULL",(player,)).fetchall()
        if player_id:
            player_id = player_id[0][0]
            debug(f"player_id is {player_id}")
        else:
            player_id = get_uuid()
            debug(f"got player_id = {player_id}")
        self.insert("INSERT OR REPLACE INTO 'players' ('id', 'name', 'agent') VALUES (?, ?, ?) ",
            (player_id, player, self.get_agent, )
            )
        self.__rowids["player"] = player_id

    def record_game_settings(self, game_settings):
        """
        Record a set of game_settings to the sql database.
        """
        game_settings_id = get_uuid()
        settings = tuple([
                    game_settings_id,
                    game_settings["height"], 
                    game_settings["width"],
                    game_settings["size"],
                    game_settings["snake_speed"],
                    game_settings["frames"],
                    game_settings["reward_limit"],
                    game_settings["auto_tick"],
                    ])
        self.insert("INSERT OR REPLACE INTO 'game_settings' ('id', 'height', 'width', 'size', 'snake_speed', 'frames', 'reward_limit', 'auto_tick') VALUES (?, ?, ?, ?, ?, ?, ?, ?) ",
            settings
            )
        info(f"game_settings = {game_settings_id}")
        self.__rowids["game_settings"] = game_settings_id

    def record_game_type(self, version):
        """
        Record a type of a game to the sql database.
        """
        game_type_id = get_uuid()
        # info(f"game_type_id = {self.get_game_settings}")
        # info(f"game_type_id = {game_type_id}")
        self.insert("INSERT OR REPLACE INTO 'games' ('id', 'settings', 'player', 'version') VALUES (?, ?, ?, ?) ",
            (game_type_id, self.get_game_settings, self.get_player, version, )
            )
        self.__rowids["game_type"] = game_type_id

    def record_game_start(self, game):
        """
        Record a single game to the sql database.
        """
        settings = { k:v for k,v in game.__dict__.items() }
        version = "0.0.0" if "version" not in game.__dict__ else game.version
        self.record_game_settings(settings)

        if hasattr(game, "agent") and game.agent is not None:
            self.record_agent(game.agent)
        self.record_player(game.player)

        self.record_game_type(version)

        game_instance_id = get_uuid()
        self.insert("INSERT OR REPLACE INTO 'game_instances' ('id', 'game', 'start') VALUES (?, ?, ?) ",
            (game_instance_id, self.get_game_type, get_timestamp(), )
            )
        self.__rowids["game_instance"] = game_instance_id
        info(f"Recorded game start. game_instance_id = {game_instance_id}")
        info(f"Recorded game start. game_instance_id = {self.get_game_instance}")

    def record_game_end(self, end):
        """
        Update when the single game ended.
        """
        game_id = self.get_game_instance
        if not isinstance(game_id, uuid.UUID):
            raise RuntimeError("Don't have an id for the current game, so we can't update the end timestamp")
        self.exc("UPDATE 'game_instances' SET 'end'=? WHERE id=?",
            (end, game_id, )
            )
        self.__rowids["game_instance"] = None

    def record_state(self, state):
        """
        Record a game state to the sql database.
        """
        # state = {
        #         "score"
        #         "fruits"
        #         "obstacles"
        #         "snake"
        #     }
        timestamp = get_timestamp()
        game_id = self.get_game_instance
        if not isinstance(game_id, uuid.UUID):
            raise RuntimeError("Don't have an id for the current game, so we can't update the end timestamp")

        state_id = get_uuid()
        self.insert("INSERT OR REPLACE INTO 'states' ('id', 'game', 'timestamp', 'score') VALUES (?, ?, ?, ?) ",
             (state_id, game_id, timestamp, state.get("score"), )
            )
        self.__rowids["state"] = state_id
        # self.record_fruits(state.get("fruits")[-1])
        self.record_fruit_states(state.get("fruits"))
        if len(self.get_obstacles) == 0:
            self.record_obstacles(state.get("obstacles"))
        self.record_snake(state.get("snake"))

    def record_fruit_species(self, fruit_defs):
        """
        Record a set of fruit species to the sql database,
        based on a series of fruit definitions
        """
        debug("Recording fruit_species")
        self.__rowids["fruit_species"] = self.__rowids.get("fruit_species",{})
        for name, fnc in fruit_defs.items():
            # for each fruit definition
            fruit = fnc([0,0])
            # spawn a dummy fruit so we can access its properties

            species_id = get_uuid()
            self.insert("INSERT OR REPLACE INTO 'fruits' ('id', 'name', 'value', 'frequency', 'color') VALUES (?, ?, ?, ?, ?) ", 
                (species_id, fruit.name, fruit.value, fruit.frequency, fruit.color, )
                )
            self.__rowids["fruit_species"][name] = species_id

    def record_fruits(self, fruits):
        """
        Record a set of fruits to the sql database.
        """
        debug("Recording fruits")
        if isinstance(fruits,(list,set,tuple)):
            # several fruit need to be recorded
            pass
        elif(isinstance(fruits, Fruit)):
            # a single fruit needs to be recorded
            fruits = [ fruits ]
        else:
            raise TypeError(f"Expected fruits, but received {type(fruits)}")
        # self.__rowids["fruits"] = self.__rowids.get("fruits",[])
        # self.__rowids["fruits"] = []
        state_id = self.get_state
        for fruit in fruits:
            species_id = self.get_fruit_species.get(fruit.name, None)
            if species_id is None:
                self.record_fruit_species({fruit.name: lambda dimensions: fruit })
                species_id = self.get_fruit_species.get(fruit.name, None)

            fruit.id = get_uuid()
            self.insert("INSERT OR REPLACE INTO 'fruit_instances' ('id', 'x', 'y', 'species') VALUES (?, ?, ?, ?) ", 
                (fruit.id, fruit.x, fruit.y, species_id, )
                )

            # self.__rowids["fruits"] += [ fruit.id ]
            states_fruits_id = get_uuid()
            self.exc("INSERT OR REPLACE INTO 'states_fruits' ('id', 'fruit', 'state') VALUES (?, ?, ?) ",
                (states_fruits_id, fruit.id, state_id, )
                )

    def record_fruit_states(self, fruits):
        """
        Record associate a set of fruits to a state in the sql database.
        """
        debug("Recording fruit states")
        if isinstance(fruits,(list,set,tuple)):
            # several fruit need to be recorded
            pass
        elif(isinstance(fruits, Fruit)):
            # a single fruit needs to be recorded
            fruits = [ fruits ]
        else:
            raise TypeError(f"Expected fruits, but received {type(fruits)}")
        state_id = self.get_state
        for fruit in fruits:
            if fruit.id is None:
                debug("Getting fruit id")
                species_id = self.get_fruit_species.get(fruit.name, None)
                if species_id is None:
                    self.record_fruit_species({fruit.name: lambda dimensions: fruit })
                    species_id = self.get_fruit_species.get(fruit.name, None)
                fruit.id = get_uuid()
                self.insert("INSERT OR REPLACE INTO 'fruit_instances' ('id', 'x', 'y', 'species') VALUES (?, ?, ?, ?) ", 
                    (fruit.id, fruit.x, fruit.y, species_id, )
                    )
            states_fruits_id = get_uuid()
            debug("Insert fruit_state")
            self.exc("INSERT OR REPLACE INTO 'states_fruits' ('id', 'fruit', 'state') VALUES (?, ?, ?) ",
                (states_fruits_id, fruit.id, state_id, )
                )
            debug("Inserted fruit_state")

    def record_obstacles(self, obstacles):
        """
        Record a set of obstacles to the sql database.
        """
        if isinstance(obstacles,(list,set,tuple)):
            # several obstacles need to be recorded
            pass
        elif(isinstance(obstacles, Obstacle)):
            # a single obstacle needs to be recorded
            obstacles = [ obstacles ]
        else:
            raise TypeError(f"Expected obstacles, not {obstacles}")
        # self.__rowids["obstacles"] = self.__rowids.get("obstacles",[])
        self.__rowids["obstacles"] = []
        state_id = self.get_state
        for ob in obstacles:
            obstacle_id = get_uuid()
            self.insert("INSERT OR REPLACE INTO 'obstacles' ('id', 'x', 'y', 'w', 'h') VALUES (?, ?, ?, ?, ?) ", 
                (obstacle_id, ob.x, ob.y, ob.w, ob.h, ) 
                )
            self.__rowids["obstacles"] += [ obstacle_id ]
            states_obstacles_id = get_uuid()
            self.exc("INSERT OR REPLACE INTO 'states_obstacles' ('id', 'obstacle', 'state') VALUES (?, ?, ?) ",
                (states_obstacles_id, obstacle_id, state_id, )
                )

    def record_segments(self, segments):
        """
        Record a set of segments to the sql database.
        """
        if isinstance(segments,(list,set,tuple)):
            # several segments need to be recorded
            pass
        elif(isinstance(segments, Segment)):
            # a single segment needs to be recorded
            segments = [ segments ]
        else:
            raise TypeError(f"Expected segments, not {segments}")
        # self.__rowids["segments"] = self.__rowids.get("segments",[])
        self.__rowids["segments"] = []
        for sg in segments:
            segment_id = get_uuid()
            self.exc("INSERT OR REPLACE INTO 'segments' ('id', 'x', 'y', 'w', 'h', 'heading') VALUES (?, ?, ?, ?, ?, ?) ",
                (segment_id, sg.x, sg.y, sg.w, sg.h, sg.heading, )
                )
            self.__rowids["segments"] += [ segment_id ]

    def record_snake(self, snake):
        """
        Record a game snake to the sql database.
        """
        state_id = self.get_state

        snake_state_id = get_uuid()
        self.insert("INSERT OR REPLACE INTO 'states_snakes' ('id', 'state', 'belly', 'length') VALUES (?, ?, ?, ?) ",
            (snake_state_id, state_id, snake.belly, snake.length)
            )
        for idx,sg in enumerate(snake.segments):
            segment_id = get_uuid()
            self.insert("INSERT OR REPLACE INTO 'segments' ('id', 'x', 'y', 'w', 'h', 'heading') VALUES (?, ?, ?, ?, ?, ?) ",
                (segment_id, sg.x, sg.y, sg.w, sg.h, sg.heading, )
                )
            snake_body_parts_id = get_uuid()
            self.exc("INSERT OR REPLACE INTO 'snake_body_parts' ('id', 'snake', 'segment', 'body_index') VALUES (?, ?, ?, ?) ",
                (snake_body_parts_id, snake_state_id, segment_id, idx, )
                )

    def exc(self, query, args, row_factory=None):
        result = None
        uses_args = False
        try:
            if args:
                uses_args = True
                # args = args[0]
                # if not isinstance(args, tuple):
                #     if hasattr(args, __iter__):
                #         args = tuple([a for a in args])
                #     else:
                #         args = (args,)
            if row_factory:
                temp = self.db.row_factory
                self.db.row_factory = row_factory
            if uses_args:
                self.cur.execute(query, args)
            else:
                self.cur.execute(query)
            self.db.commit()
            result = [row for row in self.cur.fetchall()]
            if row_factory:
                self.db.row_factory = temp
        except Exception as err:
            streams = [h.stream for h in logr.handlers]
            for stream in streams:
                info((query, args))
                traceback.print_stack(file=stream)
                logging.exception(err)
                # traceback.print_exc(limit=4, file=stream)
        finally:
            return result

    def insert(self, query, args, row_factory=None):
        result = None
        try:
            if row_factory:
                temp = self.db.row_factory
                self.db.row_factory = row_factory
            self.cur.execute(query, args)
            self.db.commit()
            result = self.cur.lastrowid
            if row_factory:
                self.db.row_factory = temp
        except Exception as err:
            streams = [h.stream for h in logr.handlers]
            for stream in streams:
                info((query, args))
                info([t.name for t in threading.enumerate()])
                traceback.print_stack(file=stream)
                logging.exception(err)
                # traceback.print_exc(limit=4, file=stream)
        finally:
            return result

    def exc_many(self, query, row_factory=None, *args):
        result = None
        uses_args = False
        try:
            if args:
                uses_args = True
                args = args[0]
                if not isinstance(args, list):
                    raise TypeError("The next argument after 'query' should be a list of tuples containing the column values.")
                elif len(args) > 0 and not isinstance(args[0], list):
                    raise TypeError("The next argument after 'query' should be a list of tuples containing the column values.")
            if row_factory:
                temp = self.db.row_factory
                self.db.row_factory = row_factory
            if uses_args:
                db.executemany(query, args)
            else:
                db.executemany(query)
            result = [row for row in db.fetchall()]
            self.db.commit()
            if row_factory:
                self.db.row_factory = temp
        except Exception as err:
            logging.exception(err)
        finally:
            return result

def adapt_bool(val):
    """
    From python bool type to sqlite 'BOOLEAN',
    an integer that's 1 or 0 (True or False)
    """
    if isinstance(val, str) and val.lower() in ["true","false"]:
        val = val.lower() == "true"
    if isinstance(val, bool):
        return int(val)
    else:
        return int(bool(val))

def convert_bool(val):
    """
    From sqlite 'BOOLEAN' to python bool
    """
    if val in [0,1]:
        return val == 1
    else:
        raise TypeError(f"Expected integer as a boolean:{val}")


def adapt_rgb(val):
    """
    From python tuple type (representing rgb values) ?, to sqlite 'RGB',
    a comma separated string with three numbers
    """
    is_tuple = isinstance(val, tuple)
    has_ints = all([isinstance(i, int) for i in val])
    has_bytes = all([(i >= 0 and i <= 255) for i in val])
    has_three = (len(val) == 3)
    if not (is_tuple and has_ints and has_bytes and has_three):
        if is_tuple:
            # necessary, since we're not creating a special class for rgb, 
            # and we're instead registering it as a tuple...
            return ",".join([str(i) for i in val])
        else:
            raise TypeError(f"Expected a tuple containing 3 integers between 0 and 255, not {val}")
    return ",".join([str(i) for i in val])

def convert_rgb(val):
    """
    From sqlite 'RGB' to python tuple (representing rgb values)
?,     """
    try:
        value = [ int(v) for v in val.split(",") ]
        has_three = (len(value) == 3)
        has_bytes = all([(i >= 0 and i <= 255) for i in val])
        if not(has_three and has_bytes):
            raise TypeError()
    except Exception as err:
        raise TypeError(f"Expected a comma separated string containing 3 integers between 0 and 255, not {val}")
    return tuple([v for v in value])

def convert_tuple(val):
    """
    From sqlite 'TUPLE' to python tuple
    """
    return tuple([v for v in val.split(",")])

def adapt_timestamp(val):
    """
    From python datetime type to sqlite 'TIMESTAMP',
    a str containing %Y-%m-%d %H-%M-%S.%f
    """
    try:
        if isinstance(val,str):
            datetime.datetime.strptime(val,"%Y-%m-%d %H:%M:%S.%f")
        return val.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception as err:
        raise TypeError(f"Expected datetime object, not {val}")

def convert_timestamp(val):
    """
    From sqlite 'TIMESTAMP' to python datetime
    """
    try:
        return datetime.datetime.strptime(val,"%Y-%m-%d %H:%M:%S.%f")
    except Exception as err:
        raise TypeError(f"Expected datetime object, not {val}")

def adapt_uuid(val):
    """
    From python uuid type to sqlite 'UUID',
    a str containing uuid characters
    """
    return str(val)

def convert_uuid(val):
    """
    From sqlite 'UUID' to python uuid
    """
    return uuid.UUID(val)

sqlite3.register_adapter(bool, adapt_bool)
sqlite3.register_converter("BOOLEAN", convert_bool)
sqlite3.register_adapter(tuple, adapt_rgb)
sqlite3.register_converter("RGB", convert_rgb)
# sqlite3.register_converter("TUPLE", convert_tuple)
sqlite3.register_adapter(datetime.datetime, adapt_timestamp)
sqlite3.register_converter("DATETIME", convert_timestamp)

sqlite3.register_adapter(uuid.UUID, adapt_uuid)
sqlite3.register_converter("UUID", convert_uuid)

