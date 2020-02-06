CREATE TABLE IF NOT EXISTS "game_settings" (
    "id"             INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "height"         INTEGER NOT NULL,
    "width"          INTEGER NOT NULL,
    "size"           INTEGER NOT NULL,
    "snake_speed"    INTEGER NOT NULL,
    "frames"         INTEGER NOT NULL,
    "reward_limit"   INTEGER NOT NULL,
    "auto_tick"      BOOLEAN NOT NULL,
    PRIMARY KEY ("height", "width", "size", "snake_speed", "frames", "reward_limit", "auto_tick")
);
CREATE TABLE IF NOT EXISTS "agents" (
-- the DQN agents trained with specific settings
    "id"             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "weights"        BLOB NOT NULL,
    "gamma"          REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS "players" (
-- the DQN agents and human players
    "id"             INTEGER NOT NULL,
    "name"           TEXT NOT NULL UNIQUE,
    "agent"          INTEGER,
    FOREIGN KEY("agent") REFERENCES "agents"("id"),
    PRIMARY KEY ("id")
);
CREATE TABLE IF NOT EXISTS "games" (
-- A specific configuration of game and player to create game instances
    "id"            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "settings"      INTEGER NOT NULL,
    "player"        INTEGER NOT NULL,
    "version"       TEXT NOT NULL,
    FOREIGN KEY("settings") REFERENCES "game_settings"("id"),
    FOREIGN KEY("player") REFERENCES "players"("id")
    PRIMARY KEY ("settings", "player", "version")
);
CREATE TABLE IF NOT EXISTS "game_instances" (
-- A single game played by someone/something
    "id"       INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "game"     INTEGER NOT NULL,
    "start"    DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
    "end"      DATETIME,
    FOREIGN KEY("game") REFERENCES "games"("id")
);
CREATE TABLE IF NOT EXISTS "commands" (
-- Available commands to pass to the game
    "id"        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "key"       INTEGER NOT NULL,
    "name"      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "commands_executed" (
-- Commands a player passed to a game instance
    "id"        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "timestamp" DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
    "command"   INTEGER NOT NULL,
    "game"      INTEGER NOT NULL,
    FOREIGN KEY("command") REFERENCES "commands"("id"),
    FOREIGN KEY("game") REFERENCES "game_instances"("id")
);
CREATE TABLE IF NOT EXISTS "fruits" (
-- the kinds of fruits available to be spawned
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "name"       TEXT NOT NULL,
    "value"      INTEGER NOT NULL,
    "frequency"  REAL NOT NULL,
    "color"      RGB NOT NULL,
    PRIMARY KEY ("name", "value", "frequency")
);
CREATE TABLE IF NOT EXISTS "obstacles" (
-- Immovable objects that snakes should never hit
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "x"          INTEGER NOT NULL,
    "y"          INTEGER NOT NULL,
    "w"          INTEGER NOT NULL,
    "h"          INTEGER NOT NULL,
    PRIMARY KEY ("x", "y", "w", "h")
);
CREATE TABLE IF NOT EXISTS "segments" (
-- Parts of a snake body
/*
Note, Segment objects in the game change dimensions, 
but the entries here will remain unchanged. Instead, 
two sequential states from the same game would represent
a segment object as two separate entries in segments. 

So, entries in segments represent a single rectangle that was
drawn onto the board in a specific location; this rectangle 
may have been drawn again later in the same game, or other games, 
but it's size and location never changes. 
*/
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "x"          INTEGER NOT NULL,
    "y"          INTEGER NOT NULL,
    "w"          INTEGER NOT NULL,
    "h"          INTEGER NOT NULL,
    "heading"    INTEGER NOT NULL,
    PRIMARY KEY ("x", "y", "w", "h", "heading")
);
CREATE TABLE IF NOT EXISTS "fruit_instances" (
-- the fruits that were spawned
/*
Note, similar to segments, this entries should not change values, 
but they can exist in multiple game instances.
*/
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "x"          INTEGER NOT NULL,
    "y"          INTEGER NOT NULL,
    "species"    INTEGER NOT NULL,
    PRIMARY KEY ("x", "y", "species"),
    FOREIGN KEY("species") REFERENCES "fruits"("id"),
);
CREATE TABLE IF NOT EXISTS "states" (
-- A snapshot of the state of a game instance in a particular point in time
/*
Note that a state contains several lists of things; 
they'll be defined in later tables.
*/
    "id"           INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "game"         INTEGER NOT NULL,
    "timestamp"    DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
    "score"        INTEGER NOT NULL,
    FOREIGN KEY("game") REFERENCES "game_instances"("id")
);
CREATE TABLE IF NOT EXISTS "states_fruits" (
-- create an entry showing that a state used an instance of a fruit
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "fruit"      INTEGER NOT NULL,
    "state"      INTEGER NOT NULL,
    PRIMARY KEY ("fruit", "state"),
    FOREIGN KEY("fruit") REFERENCES "fruit_instances"("id"),
    FOREIGN KEY("state") REFERENCES "states"("id")
);
CREATE TABLE IF NOT EXISTS "states_obstacles" (
-- create an entry showing that a state used an instance of an obstacle
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "obstacle"   INTEGER NOT NULL,
    "state"      INTEGER NOT NULL,
    PRIMARY KEY ("obstacle", "state"),
    FOREIGN KEY("obstacle") REFERENCES "obstacles"("id"),
    FOREIGN KEY("state") REFERENCES "states"("id")
);
CREATE TABLE IF NOT EXISTS "states_snakes" (
-- the state a snake was in at a moment in time
    "id"         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "state"      INTEGER NOT NULL,
    "belly"      INTEGER NOT NULL,
    "length"     INTEGER NOT NULL,
    FOREIGN KEY("state") REFERENCES "states"("id"),
);
CREATE TABLE IF NOT EXISTS "snake_body_parts" (
-- entries here associate one segment to one state the snake was in
/*
Note, segment entries can be reused here, across multiple snakes (and multiple states), 
but body_index for the segment could change from snake to snake.
*/
    "id"         INTEGER NOT NULL AUTOINCREMENT UNIQUE,
    "snake"      INTEGER NOT NULL,
    "segment"    INTEGER NOT NULL,
    "body_index" INTEGER NOT NULL,
    FOREIGN KEY("snake") REFERENCES "states_snakes"("id"),
    FOREIGN KEY("segment") REFERENCES "segments"("id"),
    PRIMARY KEY ("snake", "segment", "body_index")
);


DROP VIEW IF EXISTS [HIGH_SCORES];
CREATE VIEW IF NOT EXISTS [HIGH_SCORES] AS SELECT 
    players.id,
    players.name,
    players.agent is not NULL AS is_agent,
    states.timestamp,
    max(states.score) as highest_score
FROM (((states INNER JOIN game_instances
            ON states.game=game_instances.id
        ) INNER JOIN games
        ON game_instances.game=games.id
    ) INNER JOIN players
    ON games.player=players.id
);

DROP VIEW IF EXISTS [LOW_SCORES];
CREATE VIEW IF NOT EXISTS [LOW_SCORES] AS SELECT 
    players.id,
    players.name,
    players.agent is not NULL AS is_agent,
    states.timestamp,
    min(states.score) as lowest_score
FROM (((states INNER JOIN game_instances
            ON states.game=game_instances.id
        ) INNER JOIN games
        ON game_instances.game=games.id
    ) INNER JOIN players
    ON games.player=players.id
);
