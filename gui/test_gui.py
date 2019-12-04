import unittest
import multiprocessing
from .gameboard import Gameboard
from interfaces.game import SnakeGame
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit
import logging

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

class TestGuiInitObject(unittest.TestCase):
    """
    Test 
    """
    def test_init(self):
        """
        Test 
        """
        data = {
            "height": 640,
            "width": 640,
            "size": 10,
        }
        game = SnakeGame(**data)
        board = Gameboard(game)
        board.play_game()
        self.assertTrue(True)
        # self.assertTrue(False)
