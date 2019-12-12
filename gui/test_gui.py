import contextlib
with contextlib.redirect_stdout(None):
    import pygame as pg
del contextlib
import unittest
import multiprocessing
from .gameboard import Gameboard
from interfaces.game import SnakeGame
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit
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


def translate_sequence(seq):
    lexicon = {
        273: "U",
        274: "R",
        275: "D",
        276: "L",
        "273": "U",
        "274": "R",
        "275": "D",
        "276": "L",
    }
    sequence = [ s for s in seq ]
    for idx,(key,direction) in enumerate(sequence):
        direction = "v" if direction == pg.KEYDOWN else "^"
        sequence[idx] = f"{lexicon.get(key)}{direction}"
    return sequence

class TestGuiObjectKeySequencing(unittest.TestCase):
    """
    Test methods used to clean and maintain key_sequence attribute
    """
    def setUp(self):
        debug("TestGuiObjectKeySequencing.setUp")
        data = {
            # "height": 352,
            # "width": 352,
            "height": 640,
            "width": 640,
            # "frames": 60,
            "frames": 30,
            "score": 10,
            "snake_speed": 10,
            # "size": 11,
            "size": 10,
            "starting_length": 5,
            # "auto_tick": False,
            "auto_tick": True,
            "fruits":{
                "apple": lambda dimensions: Fruit("apple", dimensions, 1, color=(200,0,0), frequency=0.05 ),
                # 1 in 20 chance of an apple appearing each second, worth 1 point
                "orange": lambda dimensions: Fruit("orange", dimensions, 1, color=(128,128,0), frequency=0.01 ),
                # 1 in 100 chance of an orange appearing each second, worth 10 points
                "bananna": lambda dimensions: Fruit("bananna", dimensions, 1, color=(255,255,0), frequency=0.005 ),
                # 1 in 200 chance of an bananna appearing each second, worth 10 points
            },
            "reward_limit": 3,
        }
        starting_length = data.get("size")*data.get("starting_length")
        ourboros = Snake([ data.get("width")/2, starting_length, data.get("size"), starting_length], 2)
        self.game = SnakeGame(**data)
        self.game.snake = None
        self.game.snake = ourboros
        self.board = Gameboard(self.game)
        debug("TestGuiObjectKeySequencing.setUp complete")
    def quitGame(self):
        self.board.simulate_keys("qv, q^", action="set")
        # debug("quitGame")
        time.sleep(1)
    def tearDown(self):
        debug("TestGuiObjectKeySequencing.tearDown")
        self.game = None
        self.board = None
        time.sleep(1)
        debug("TestGuiObjectKeySequencing.tearDown complete")
    # @unittest.skip("skipping test_simplification")
    def test_simplification(self):
        """
        Test the Gameboard._simplify_pattern method.
        """
        debug("start test_simplification")
        # debug("initial_state")
        initial_state = self.board.simulate_keys("UPv, UP^, UPv")
        final_state = self.board.simulate_keys("UPv")
        key_sequence = initial_state
        # self.assertTrue(False)
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._simplify_pattern(key_sequence)
        self.assertListEqual(key_sequence, final_state)
        # debug(initial_state)
        # debug(final_state)

        initial_state = self.board.simulate_keys("UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, UP^, UPv")
        final_state = self.board.simulate_keys("UPv, LEFTv, LEFT^, RIGHTv, RIGHT^")
        key_sequence = initial_state
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._simplify_pattern(key_sequence)
        self.assertListEqual(key_sequence, final_state)

        initial_state = self.board.simulate_keys("UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, LEFTv, UP^, UPv")
        final_state = self.board.simulate_keys("UPv, LEFTv, RIGHTv, RIGHT^")
        key_sequence = initial_state
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._simplify_pattern(key_sequence)
        self.assertListEqual(key_sequence, final_state)

    # @unittest.skip("skipping test_removal")
    def test_removal(self):
        """
        Test the Gameboard._remove_duplicates method.
        """
        debug("start test_removal")
        initial_state = self.board.simulate_keys("UPv,UPv,UPv,UPv,UPv,UPv,UP^")
        final_state = self.board.simulate_keys("UPv,UP^")
        key_sequence = initial_state
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._remove_duplicates(key_sequence)
        self.assertListEqual(key_sequence, final_state)

        initial_state = self.board.simulate_keys("UPv,UPv,UPv,UP^,UPv,UPv,UPv,UP^")
        final_state = self.board.simulate_keys("UPv,UP^,UPv,UP^")
        key_sequence = initial_state
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._remove_duplicates(key_sequence)
        self.assertListEqual(key_sequence, final_state)

        initial_state = self.board.simulate_keys("UPv,UPv,UPv,UP^,UPv,UPv,UPv,UP^")
        final_state = self.board.simulate_keys("UPv,UP^,UPv,UP^")
        key_sequence = initial_state
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._remove_duplicates(key_sequence)
        self.assertListEqual(key_sequence, final_state)
        
        initial_state = self.board.simulate_keys("UPv, UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, LEFTv, UP^, UPv")
        final_state = self.board.simulate_keys("UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, LEFTv, UP^, UPv")
        key_sequence = initial_state
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._remove_duplicates(key_sequence)
        self.assertListEqual(key_sequence, final_state)

        # self.assertListEqual(key_sequence, initial_state)
    # @unittest.skip("skipping test_persistence")
    def test_persistence(self):
        """
        Test the Gameboard._ensure_persistance method.
        """
        debug("start test_persistence")
        initial_state = self.board.simulate_keys("UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, DOWNv, DOWN^, LEFTv, LEFT^, RIGHTv, RIGHT^, DOWNv, DOWN^, LEFTv, LEFT^, RIGHTv, RIGHT^, DOWNv, DOWN^, UP^")
        final_state = self.board.simulate_keys("UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, DOWNv, DOWN^, UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, DOWNv, DOWN^, UPv, LEFTv, LEFT^, RIGHTv, RIGHT^, DOWNv,  DOWN^, UP^")
        # debug(f"initial_state({len(initial_state)}) {Gameboard.translate_sequence(initial_state)}")
        # debug(f"final_state  ({len(final_state)}) {Gameboard.translate_sequence(final_state)}")

        key_sequence = [item for item in initial_state]
        self.assertListEqual(key_sequence, initial_state)
        key_sequence = self.board._ensure_persistance(key_sequence)
        # debug(f"key_sequence ({len(key_sequence)}) {Gameboard.translate_sequence(key_sequence)}")
        self.assertListEqual(final_state, key_sequence)
        self.assertEqual(len(final_state), len(key_sequence))
    # # @unittest.skip("skipping test_handle")
    # def test_handle(self):
    #     """
    #     Test the Gameboard.handle_keys method.
    #     """
    #     debug("start test_handle")
    #     pass
    # @unittest.skip("skipping test_self_intersect")
    def test_self_intersect(self):
        """
        Test ability to move the snake into itself
        """
        debug("start test_self_intersect")
        # self.proc.start()
        self.board.key_sequence = [ (pg.K_SPACE, pg.KEYDOWN) ]
        # debug("board starting")
        self.assertTrue(self.board.game.snake.is_alive)
        self.board.start()
        time.sleep(1)
        self.assertTrue(self.board.game.snake.is_alive)
        self.board.simulate_keys("RIGHTv, RIGHT^, DOWNv, DOWN^, LEFTv, LEFT^, UPv, UP^, RIGHTv, RIGHT^", action="set")
        time.sleep(1)
        self.assertTrue(self.board.game.snake is None)
        self.assertTrue(self.board.game.playing is False)
        self.quitGame()
        debug("finished test_self_intersect")
    # @unittest.skip("skipping test_pause")
    def test_pause(self):
        """
        Test the ability to pause and resume the game
        """
        # self.proc.start()
        debug("start test_pause")
        self.assertEqual(self.game.playing, False)
        self.board.simulate_keys("rv, r^", action="set")
        self.board.start()
        # self.assertEqual(self.game.playing, True)
        # while self.board.game.playing is False:
        #     time.sleep(0.5)
        time.sleep(0.5)
        self.assertEqual(self.game.playing, True)

        self.board.simulate_keys("SPACEv, SPACE^", action="set")
        time.sleep(0.5)
        self.assertEqual(self.game.playing, False)

        self.board.simulate_keys("SPACEv, SPACE^", action="set")
        time.sleep(0.5)
        self.assertEqual(self.game.playing, True)

        self.board.simulate_keys("SPACEv, SPACE^", action="set")
        time.sleep(0.5)
        self.assertEqual(self.game.playing, False)

        self.board.simulate_keys("SPACEv, SPACE^", action="set")
        time.sleep(0.5)
        self.assertEqual(self.game.playing, True)
        self.quitGame()
        debug("finished test_pause")
        # self.assertTrue(False)
    # @unittest.skip("skipping test_restart")
    def test_restart(self):
        """
        Test the ability to restart the game
        """
        debug("start test_restart")
        self.board.start()
        time.sleep(1)
        if self.game.playing:
            self.board.simulate_keys("RIGHTv, RIGHT^, DOWNv, DOWN^, LEFTv, LEFT^, UPv, UP^, RIGHTv, RIGHT^", action="set")
            time.sleep(1)
        self.assertEqual(self.game.playing, False)
        self.board.simulate_keys("rv, r^", action="set")
        time.sleep(0.5)
        self.assertEqual(self.game.playing, True)
        self.quitGame()
        debug("finished test_restart")


# class TestGuiKeySeqWithInit(unittest.TestCase):
#     """
#     Test 
#     """
#     def setUp(self):
#         data = {
#             "height": 640,
#             "width": 640,
#             "size": 10,
#             "snake_speed": 10,
#             "starting_length": 5,
#             "auto_tick": True,
#             "frames": 60,
#         }
#         starting_length = data.get("size")*data.get("starting_length")
#         ourboros = Snake([ data.get("width")/2, starting_length, data.get("size"), starting_length], 2)
#         self.game = SnakeGame(**data)
#         self.game.snake = None
#         self.game.snake = ourboros
#         self.board = Gameboard(self.game)
#         # import threading
#         # self.proc = multiprocessing.Process(target=Gameboard.start, args=(self, ))
#         # self.proc = threading.Thread(target=Gameboard.start, args=(self.board, ))
#     def tearDown(self):
#         debug("TestGuiKeySeqWithInit.tearDown")
#         self.game = None
#         self.board = None
#         time.sleep(2)
#     # def test_init(self):
#     #     # self.proc.start()
#     #     # self.board.start()
#     #     # time.sleep(1)
#     #     self.assertTrue(True)
#     #     # self.assertEqual(self.board.game.playing,True)
#     def test_self_intersect(self):
#         """
#         Test ability to move the snake into itself
#         """
#         # self.proc.start()
#         self.board.key_sequence = [ (pg.K_SPACE, pg.KEYDOWN) ]
#         # debug("board starting")
#         self.assertTrue(self.board.game.snake.is_alive)
#         self.board.start()
#         # debug("board started")
#         time.sleep(1)
#         self.assertTrue(self.board.game.snake.is_alive)
#         debug("setting keys")
#         self.board.simulate_keys("RIGHTv, RIGHT^, DOWNv, DOWN^, LEFTv, LEFT^, UPv, UP^, RIGHTv, RIGHT^", action="set")
#         debug("keys set")
#         time.sleep(1)
#         self.assertTrue(self.board.game.snake is None)
#         self.assertTrue(self.board.game.playing is False)
#         time.sleep(3)
#         debug("quiting")
#         self.board.simulate_keys("qv, q^", action="set")
#         time.sleep(1)
#         debug("finished test_self_intersect")
#     def test_pause(self):
#         """
#         Test the ability to pause and resume the game
#         """
#         # self.proc.start()
#         debug("start test_pause")
#         self.assertEqual(self.game.playing, False)
#         self.board.start()
#         # self.assertEqual(self.game.playing, True)
#         time.sleep(0.5)
#         debug(f"SPACE {self.game.playing}")

#         self.board.simulate_keys("SPACEv, SPACE^", action="set")
#         self.assertEqual(self.game.playing, False)
#         time.sleep(0.5)
#         debug(f"SPACE {self.game.playing}")

#         self.board.simulate_keys("SPACEv, SPACE^", action="set")
#         self.assertEqual(self.game.playing, True)
#         time.sleep(0.5)
#         debug(f"SPACE {self.game.playing}")

#         self.board.simulate_keys("SPACEv, SPACE^", action="set")
#         self.assertEqual(self.game.playing, False)
#         time.sleep(0.5)
#         debug(f"SPACE {self.game.playing}")

#         self.board.simulate_keys("SPACEv, SPACE^", action="set")
#         self.assertEqual(self.game.playing, True)
#         time.sleep(0.5)
#         debug(f"SPACE {self.game.playing}")

#         debug("finished test_pause")
#         # self.assertTrue(False)

# if __name__ == '__main__':
#     unittest.main()