import unittest
import multiprocessing
from .player import Player
from .game import *
from .DQN import DQN
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit

# import pprint
# _pp = pprint.PrettyPrinter(
#                         indent=4,
#                         depth=7,
#                         width=100,
#                     )
# pp = _pp.pprint
# print(pp.pformat(game.game_state))

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

class TestSnakeGameInitObject(unittest.TestCase):
    """
    Test that the SnakeGame object behaves as expected.
    """
    def test_init(self):
        """
        Test if we can create a SnakeGame object.
        """
        data = {
            "height": 640,
            "width": 640,
            "frames": 30,
            "score": 10,
            "snake_speed": 5,
            "size": 10,
            "starting_length": 2,
            "auto_tick": False,
            "fruits":{
                "apple": lambda dimensions: Fruit("apple", dimensions, 1, color=(200,0,0), frequency=0.05 ),
                # 1 in 20 chance of an apple appearing each second, worth 1 point
                "orange": lambda dimensions: Fruit("orange", dimensions, 10, color=(128,128,0), frequency=0.01 ),
                # 1 in 100 chance of an orange appearing each second, worth 10 points
                "bananna": lambda dimensions: Fruit("bananna", dimensions, 20, color=(255,255,0), frequency=0.005 ),
                # 1 in 200 chance of an bananna appearing each second, worth 20 points
            }
        }
        game = SnakeGame(**data)
        self.assertFalse(game.auto_tick)
        self.assertEqual(game.height, data.get("height"))
        self.assertEqual(game.width, data.get("width"))
        self.assertEqual(game.frames, data.get("frames"))
        self.assertEqual(game.score, data.get("score"))
        self.assertEqual(game.snake_speed, data.get("snake_speed"))
        self.assertEqual(game.size, data.get("size"))
        self.assertEqual(game.starting_length, data.get("starting_length"))
        self.assertEqual(game.crashed, False)
        self.assertEqual(game.playing, False)
        self.assertEqual(game.next_fruit, None)
        # self.assertEqual(game.obstacles, [])
        self.assertEqual(len(game.obstacles), 4)
        self.assertEqual(game.rewards, [])
        apple = game.fruits.get("apple")([ 45, 67, game.size])
        self.assertIsInstance(apple, Fruit)
        self.assertEqual(apple.frequency, 0.05)
        self.assertEqual(apple.color, (200,0,0))
        self.assertEqual(apple.x, 45)
        self.assertEqual(apple.y, 67)
        self.assertEqual(apple.value, 1)
        self.assertEqual(apple.size, game.size)
        game.rewards += [ apple ]

        self.assertEqual(game.next_cmd, None)

        # self.assertEqual(game.game_state, None)

        self.assertNotEqual(game.game_state, None)
        self.assertEqual(len(game.game_state), 4)
        game_state, obstacles, rewards, (snake_segs, snake_belly) = game.game_state

        self.assertEqual(game.playing, game_state[0])
        self.assertEqual(game.crashed, game_state[1])
        self.assertEqual(game.score, game_state[2])
        self.assertEqual(game.size, game_state[3])
        self.assertEqual(game.height, game_state[4])
        self.assertEqual(game.width, game_state[5])
        self.assertEqual(game.snake_speed, game_state[6])
        self.assertEqual(game.auto_tick, game_state[7])

        self.assertEqual(len(game.obstacles), len(obstacles))
        self.assertEqual([ob.dimensions for ob in game.obstacles], obstacles)

        self.assertEqual(len(game.rewards), len(rewards))
        self.assertEqual([[rw.dimensions, rw.value] for rw in game.rewards], rewards)

        self.assertEqual(game.snake.belly, snake_belly)
        self.assertEqual([[sg.dimensions, sg.heading] for sg in game.snake.segments], snake_segs)
        self.assertEqual(game.next_cmd, None)
        # game._spawn_next_cmd_tester()
        # game._spawn_game_state_tester()
        # spawn_next_cmd_tester(game,0)

        # game.next_cmd = 0
        # self.assertEqual(str(game.next_cmd), "0")

        # debug(vars(game))
        # debug(dir(game))
        # debug(game.__dict__)
        # debug(game.__getattribute__("next_cmd"))

        # _SnakeGame__next_cmd
        # debug(f"input {game._SnakeGame__input.poll()}")
        # debug(f"output {game._SnakeGame__output.poll()}")
        # pp("TESTING")
        # pp(game.next_cmd)
        # game.next_cmd = 0
        # pp(game.next_cmd)
        # # self.assertEqual(str(game.next_cmd), "0")

def test_setting_next_cmd(self,value):
    self.next_cmd = value

def test_getting_game_state(self):
    game_state, obstacles, rewards, (snake_segs, snake_belly) = self.game_state
    # assert

data = {
    "height": 100,
    "width": 100,
    "frames": 1,
    "score": 10,
    "snake_speed": 1,
    "size": 1,
    "starting_length": 3,
    "auto_tick": False,
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
global_game = SnakeGame(**data)


class TestSnakeGameObject(unittest.TestCase):
    """
    Test that the SnakeGame object behaves as expected.
    """
    def setUp(self):
        data = {
            "height": 352,
            "width": 352,
            "frames": 30,
            "score": 10,
            "snake_speed": 5,
            "size": 11,
            "starting_length": 2,
            "auto_tick": False,
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
        self.game = SnakeGame(**data)

    def test_point_gen(self):
        """
        Test SnakeGame object ability to generate a random point safely.
        """
        # for x in range(1):
        for x in range(1000):
            point = self.game.get_point()
            # debug(f" {point} ")
            self.assertEqual(len(point), 2)
            self.assertTrue(0 < point[0])
            self.assertTrue(0 < point[1])
            self.assertTrue(point[0] < self.game.width)
            self.assertTrue(point[1] < self.game.height)
            self.assertTrue(point[0]%self.game.size == 0)
            self.assertTrue(point[1]%self.game.size == 0)

    def test_germ(self):
        """
        Test SnakeGame object ability to limit the number of rewards.
        """
        self.assertEqual(self.game.reward_limit, 3)
        self.assertEqual(len(self.game.rewards), 0)
        self.game.next_fruit = "apple"
        self.game.spawn_next_fruit()
        self.assertEqual(len(self.game.rewards), 1)
        self.game.next_fruit = "apple"
        self.game.spawn_next_fruit()
        self.assertEqual(len(self.game.rewards), 2)
        self.game.next_fruit = "apple"
        self.game.spawn_next_fruit()
        self.assertEqual(len(self.game.rewards), 3)
        self.game.next_fruit = "apple"
        self.game.spawn_next_fruit()
        self.assertEqual(len(self.game.rewards), 3)
        


class TestSnakeGameCmdProcesses(unittest.TestCase):
    """
    Test that the SnakeGame object behaves as 
    expected when acted upon by multiple processes.
    """
    def setUp(self):
        global_game.playing = True
        global_game.crashed = False
        global_game.snake.segments = [Segment([9, 57, 1, 3], 2)]
        # headed south
        self.proc = multiprocessing.Process(target=test_setting_next_cmd, args=(global_game, ))
        
    def test_cmd_null(self):
        """
        Test command is None initially.
        """
        self.assertEqual(global_game.next_cmd, None)
        # args = [a for a in self.proc._args]
        # self.proc._args = tuple([ ])
        global_game.update()
        # progress the game to the next state
        self.assertEqual(global_game.next_cmd, None)

    def test_cmd_move(self):
        """
        Test if we can share a SnakeGame object between processes.
        """
        old_heading = global_game.snake.heading
        new_heading = (old_heading+1)%4
        # have the snake turn to it's relative right (west)
        self.assertNotEqual(old_heading, new_heading)

        self.assertEqual(global_game.snake.heading, old_heading)
        old_position = global_game.snake.segments
        # args = [ a for a in self.proc._args ]+[new_heading]
        # self.proc._args = tuple(args)
        # # set the new command
        # self.proc.start()
        # self.proc.join()
        # # execute the new command
        test_setting_next_cmd(global_game, new_heading)
        self.assertEqual(global_game.next_cmd, new_heading)
        # show that the game received the command and has it cached
        global_game.update()
        # progress the game to the next state
        self.assertEqual(global_game.next_cmd, None)
        # show that the game has consumed the command
        self.assertNotEqual(global_game.snake.heading, old_heading)
        # the snake is no longer using the old heading
        self.assertEqual(global_game.snake.heading, new_heading)
        # the snake is using the new heading
        # self.assertNotEqual(global_game.snake.head.dimensions, old_position)
        new_position = global_game.snake.segments
        # debug(old_position)
        # debug(new_position)
        self.assertEqual(new_position[-1].x, old_position[0].x)
        self.assertEqual(new_position[-1].y, old_position[0].y)
        self.assertEqual(new_position[-1].w, old_position[0].w)
        self.assertEqual(new_position[0].h, global_game.snake.size)
        # self.assertEqual(new_position[0].h, global_game.snake.size)
        # self.assertEqual(new_position[0].h, old_position[0].h)
# old_position
# new_position


    # def test_cmd_quit(self):
    #     """
    #     Test if we can share a SnakeGame object between processes.
    #     """
    #     global_game.playing = True
    #     self.assertEqual(global_game.next_cmd, None)
    #     old_heading = global_game.snake.heading
    #     new_heading = (old_heading+1)%4
    #     # have the snake turn to it's relative right
    #     proc = multiprocessing.Process(target=test_setting_next_cmd, args=(global_game, new_heading, ))
    #     # create a separate process that will set the new command
    #     self.assertEqual(global_game.next_cmd, None)
    #     self.assertEqual(global_game.snake.heading, old_heading)
    #     proc.start()
    #     proc.join()
    #     # execute the new command
    #     self.assertFalse(global_game.playing)
    #     self.assertTrue(global_game.crashed)

if __name__ == '__main__':
    unittest.main()