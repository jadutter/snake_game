import contextlib
with contextlib.redirect_stdout(None):
    import pygame as pg
del contextlib

import logging
import time

try:
    if "logr" not in globals():
        logr = logging.getLogger("MainApp")
        # get a logger
        log = logr.log
        crit = logr.critical
        error = logr.error
        warn = logr.warning
        info = logr.info
        debug = logr.debug
        # take the logger methods that record messages and 
        # convert them into simple one word functions
        assert debug == getattr(logr,"debug"), "Something went wrong with getting logging functions..."
        # the logger method called "debug", should now be the same as our function debug()
except Exception as err:
    logging.critical("Failed to configure logging for game.py")
    logging.exception(err)
    # print the message to the root logger
    raise err
finally:
    pass
class Gameboard(object):
    """
    Setup a pygame window to render the current state of the Snake Game
    """
    defaults = {
        "title": "Title",
        "frames": 60,
        "background": (0,0,0),
        "obstacle_color": (0,0,255),
        "snake_color": lambda i,t: (0,255-min(i/t*255, 10),0),
    }
    def __init__(self, game, *args, **kwargs):
        super(Gameboard, self).__init__()
        for k,v in self.defaults.items():
            # for each item in the default configuration
            setattr(self, k, kwargs.get(k,v))
            # try to get and use a keyword argument, else use default; 
            # set value for the attribute
        self.game = game
        self.app_surface = pg.display.set_mode((self.width, self.height))
        pg.display.set_caption(self.title)

    def handle_keys(self):
        #     0 = move the snake north
        #     1 = move the snake east
        #     2 = move the snake south
        #     3 = move the snake west
        #     4 = pause the game
        #     5 = restart the game
        #     6 = quit the game
        #     7 = force the lowest level fruit to spawn
        #     8 = force the next highest level fruit to spawn
        valid_keys = {
            "north":{
                "codes": [273],
                "direction":0,
                "cmd": 0
            },
            "east":{
                "codes": [275],
                "direction":1,
                "cmd": 1
            },
            "south":{
                "codes": [274],
                "direction":2,
                "cmd": 2
            },
            "west":{
                "codes": [276],
                "direction":3,
                "cmd": 3
            },
            "pause/play":{
                "codes": [32],
                "cmd": 4
            },
            "retry":{
                "codes": [114],
                "cmd": 5
            },
            "quit":{
                "codes": [27, 113],
                "cmd": 6
            },
            "apple":{
                "codes": [97],
                "cmd": 7
            },
            "orange":{
                "codes": [112],
                "cmd": 8
            },
            "bananna":{
                "codes": [98],
                "cmd": 9
            }
        }        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.game.crashed = True
            elif event.type == pg.KEYDOWN:
                # debug(event)
                for k,v in valid_keys.items():
                    if event.key in v.get("codes"):
                        debug(k)
                        self.game.next_cmd = v.get("cmd")
            # elif event.type == pg.KEYUP:
            #     # a key was released
            #     for k,v in valid_keys.items():
            #         direction = v.get("direction", None)
            #         if direction:
            #             # the key has a direction
            #             if event.key in v.get("codes"):
            #                 # the key matches
            #                 if direction == self.direction:
            #                     # if the released key was the last one to set the direction, 
            #                     self.has_key = False
    def play_game(self):
        counter = 0
        while self.game.snake.is_alive and counter < self.frames*3:
            self.handle_keys()
            self.game.update()
            self.app_surface.fill(self.background)
            for wall in self.game.obstacles:
                pg.draw.rect(self.app_surface, self.obstacle_color, wall.render())
            for fruit in self.game.rewards:
                pg.draw.rect(self.app_surface, fruit.color, fruit.render())
            for idx,seg in enumerate(self.game.snake.render()):
                color = self.snake_color(idx, self.game.snake.length)
                pg.draw.rect(self.app_surface, color, seg)
            self.update()
            counter += 1


    def update(self,frames=None):
        pg.display.flip()
        # Update the full display Surface to the screen
        if frames is None:
            frames = self.frames
        self.game.clock.tick(frames)
        

    @property
    def height(self):
        return self.game.height

    @property
    def width(self):
        return self.game.width

    @property
    def score(self):
        return self.game.score