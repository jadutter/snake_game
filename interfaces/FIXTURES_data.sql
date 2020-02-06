BEGIN TRANSACTION;
INSERT OR REPLACE INTO "commands" ("id", "key", "name") VALUES (1,0,"Move the snake North"),
 (2,1,"Move the snake East"),
 (3,2,"Move the snake South"),
 (4,3,"Move the snake West"),
 (5,4,"pause the game"),
 (6,5,"restart the game"),
 (7,6,"quit the game"),
 (8,7,"force fruit to spawn"),
 (9,8,"force fruit to spawn"),
 (10,9,"force fruit to spawn"),
 (11,10,"force fruit to spawn"),
 (12,11,"force fruit to spawn"),
 (13,12,"force fruit to spawn"),
 (14,13,"force fruit to spawn");
INSERT OR REPLACE INTO "game_settings" ("id", "height", "width", "size", "snake_speed", "frames", "reward_limit", "auto_tick") VALUES (0,320,320,10,10,60,5,1),
    (1,320,320,10,10,60,5,0),
    (2,64,64,1,1,60,5,0);
INSERT OR REPLACE INTO "players" ("id", "name", "agent") VALUES (0, "ANON", NULL),
	(1, "JAD", NULL);
INSERT OR REPLACE INTO "obstacles" ("id", "x", "y", "w", "h") VALUES (0, 0, -10, 320, 10),
    (1, 320, 0, 10, 320), 
    (2, 0, 320, 320, 10), 
    (3, -10, 0, 10, 320);
INSERT OR REPLACE INTO "games" ("id" ,"settings" ,"player" ,"version") VALUES (0, 0, 0, "0.0.0");
INSERT OR REPLACE INTO "states" ("id", "game", "timestamp", "snake", "score") VALUES (0, 0, "2019-08-28 12:47:51.000", 0, 100),
	(0, 0, "2019-08-28 12:47:52.000", 0, 110);
INSERT OR REPLACE INTO "snakes" ("id", "belly") VALUES (0, 18);
INSERT OR REPLACE INTO "segments" ("id", "x", "y", "w", "h", "heading", "snake", "body_index") VALUES (0, 260, 170, 60, 10, 1, 0, 0);
COMMIT;
