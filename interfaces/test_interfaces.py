import unittest
import multiprocessing
import json
from .player import Player
from .game import *
# from .DQN import DQN
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit
from .scribe import Scribe
import logging

try:
    if "logr" not in globals():
        logr = logging.getLogger("Iface")
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



def test_setting_next_cmd(self,value):
    self.next_cmd = value

data = {
    "testing": True,
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
            "testing": True,
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

    # @unittest.skip("skipping test_point_gen")
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

    # @unittest.skip("skipping test_germ")
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
        debug("TestSnakeGameCmdProcesses.setUp")
        global_game.playing = True
        global_game.crashed = False
        global_game.snake.segments = [Segment([9, 57, 1, 3], 2)]
        # headed south
        self.proc = multiprocessing.Process(target=test_setting_next_cmd, args=(global_game, ))
        
    # @unittest.skip("skipping test_cmd_null")
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

    # @unittest.skip("skipping test_cmd_move")
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

    # @unittest.skip("skipping test_state_change")
    def test_state_change(self):
        """
        Test if we can properly export the state of the game
        """
        import copy
        old_heading = global_game.snake.heading
        new_heading = (old_heading+1)%4
        # have the snake turn to it's relative right (west)
        self.assertNotEqual(old_heading, new_heading)

        self.assertEqual(global_game.snake.heading, old_heading)
        old_position = global_game.snake.segments
        test_setting_next_cmd(global_game, new_heading)
        self.assertEqual(global_game.next_cmd, new_heading)
        # show that the game received the command and has it cached
        initial_state = copy.deepcopy(global_game.game_state)
        # hold onto the current game state
        
        global_game.next_fruit = global_game.fruit_chances[0][0]
        # set the game to spawn a fruit of a given name
        global_game.spawn_next_fruit()
        # spawn it into the game's listed rewards
        fruit_state = copy.deepcopy(global_game.game_state)
        # hold onto the current game state
        fruit = global_game.rewards[0]
        fruit.value = 1
        # set the value to 1 so we can test snake belly, length, and movement
        global_game.snake.interact(fruit)
        # declare that the snake should interact with this new fruit
        ate_state = copy.deepcopy(global_game.game_state)
        # hold onto the game state after the snake ate the fruit
        global_game.rewards = global_game.rewards[1:]
        # remove the "eaten" fruit
        no_fruit_state = copy.deepcopy(global_game.game_state)
        # hold onto the game state after we've removed the fruit
        # debug("BEFORE TURN")
        global_game.update()
        # progress the game to the next state, presumably using next_cmd
        # debug("AFTER TURN")
        turn_state = copy.deepcopy(global_game.game_state)
        # hold onto the game state now that the snake has "turned" right 

        self.assertEqual(global_game.next_cmd, None)
        # show that the game has consumed the command
        self.assertNotEqual(global_game.snake.heading, old_heading)
        # the snake is no longer using the old heading
        self.assertEqual(global_game.snake.heading, new_heading)
        # the snake is using the new heading

        self.assertEqual(global_game.next_cmd, None)
        test_setting_next_cmd(global_game, new_heading)
        self.assertEqual(global_game.next_cmd, new_heading)
        # show that the game received the command and has it cached
        self.assertNotEqual(global_game.next_cmd, None)
        # debug("BEFORE RUN")
        global_game.update()
        # debug("AFTER RUN")
        # progress the game to the next state, presumably using next_cmd
        run_state = copy.deepcopy(global_game.game_state)
        # hold onto the game state now that the snake has "run" forward
        pretty_state = lambda st: json.dumps(SnakeGame.label_state(st),indent=4,separators=(",",": "))
        # debug(f"initial_state: {initial_state}")
        # debug(f"initial_state: {pretty_state(list(initial_state))}")
        # debug(f"fruit_state: {pretty_state(list(fruit_state))}")
        # debug(f"ate_state: {pretty_state(list(ate_state))}")
        # debug(f"no_fruit_state: {pretty_state(list(no_fruit_state))}")
        # debug(f"run_state: {pretty_state(list(run_state))}")
        # debug(f"turn_state: {pretty_state(list(turn_state))}")
        states = {
            "initial_state":initial_state,
            "fruit_state":fruit_state,
            "ate_state":ate_state,
            "no_fruit_state":no_fruit_state,
            "turn_state":turn_state,
            "run_state":run_state,
        }
        for name,state in states.items():
            # for each intermediary state
            for nm,st in states.items():
                # compare it to all the other intermediary states
                if nm == name:
                    # if its the same name 
                    self.assertTrue(SnakeGame.compare_states(state,st), f"{name} did not match {nm}!")
                    # it should be the same state
                else:
                    # otherwise,
                    self.assertFalse(SnakeGame.compare_states(state,st), f"{name} matched {nm}!")
                    # something should have always changed between these states
        self.assertTrue(SnakeGame.compare_states(run_state, global_game.game_state))
        self.assertListEqual(run_state, global_game.game_state)

class TestScribe(unittest.TestCase):
    """
    Test that the SnakeGame object behaves as 
    expected when acted upon by multiple processes.
    """
    def setUp(self):
        debug("TestScribe.setUp")
        self.scribe = Scribe("data.db")

    def test_get_commands(self):
        """
        Test if we can use the Scribe object to get available commands from the database
        """
        result = self.scribe.db.tables
        info(result)
        result = self.scribe.db.get_columns("games")
        info(result)
        # result = self.scribe.get("commands",None)
        # info(result)
        # result = self.scribe.get("commands","name LIKE '%Move the snake%'")
        # info(result)
        # result = self.scribe.exc("SELECT key FROM commands WHERE name LIKE '%Move the snake%'",row_factory="tuple")
        # info(result)
        # self.scribe.exc("INSERT INTO 'commands_executed' ('command', 'game') VALUES (0,0)")
        result = self.scribe.exc("SELECT * FROM commands_executed")
        info(result)
        
if __name__ == '__main__':
    unittest.main()