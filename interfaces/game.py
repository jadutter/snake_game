import contextlib
with contextlib.redirect_stdout(None):
    import pygame.time as gtime
del contextlib
import random
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit
from interfaces.scribe import Scribe, get_timestamp
import multiprocessing
import logging
import copy
import math
from collections import OrderedDict

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



class SnakeGame(object):
    """
    Setup a game to create and track the current state of the game.
    """
    defaults = {
        "version": "0.0.0",
        # what version of the game is being played
        "player": "ANON",
        # who is playing the current game
        "agent": None,
        # the DQN agent if the player is not human
        "timeout": 100,
        # how long to wait for a response before timing out
        "height": 64,
        # vertical boundaries of the game
        "width": 64,
        # horizontal boundaries of the game
        "frames": 60,
        # frames per second
        "score": 0,
        # points for playing the game
        "snake_speed": 10,
        # moves per second
        "size": 1,
        # how big a virtual pixel is/ how many pixels are in a virtual pixel
        "starting_length": 3,
        # how long the snake should start out as
        "auto_tick": True,
        # Whether to wait for a move, or automatically progress the game clock
        "reward_limit": 5,
        # limit how many fruit can be simultaneously created
        "testing": False,
        # whether we're running unittests 
        "database": "data.db",
    }
    __valid_keys = {
            "0": 0,
            # up, north
            "1": 1,
            # right, east
            "2": 2,
            # down, south
            "3": 3,
            # left, west
            "4": 4,
            # escape/spacebar /pause/play
            "5": 5,
            # restart/start
            "6": 6,
            # quit
        }
    __still_alive_reward_fnc = (lambda x: ((-1*math.atan((x/0.5)-1))+1.7))
    def __init__(self, *args, **kwargs):
        self.__next_cmd = None
        self.__game_state = None
        self.crashed = False
        # whether the game should keep going
        self.playing = False
        # whether the game should keep updating the state
        for k,v in self.defaults.items():
            # for each item in the default configuration
            setattr(self, k, kwargs.get(k,v))
            # try to get and use a keyword argument, else use default; 
            # set value for the attribute
        self.clock = gtime.Clock()
        # create a clock that will limit how often we can loop to update state
        # self.next_cmd = None
        # None, or an integer indicating what an instruction to perform:
        #     0 = move the snake north
        #     1 = move the snake east
        #     2 = move the snake south
        #     3 = move the snake west
        #     4 = pause the game
        #     5 = restart the game
        #     6 = quit the game
        #     7 = force the lowest level fruit to spawn
        #     8 = force the next highest level fruit to spawn
        #     etc.
        self.obstacles = []
        # a list of Obstacle objects that would kill the snake
        self.rewards = []
        # a list of Fruit objects that would feed the snake
        self.next_fruit = None
        # None, or a string to indicate the next Fruit object that should be added
        self.fruits = kwargs.get("fruits",{
        # store a dict of name: function that instantiates a fruit object
                "apple": lambda dimensions: Fruit("apple", dimensions, 1, color=(255,0,0), frequency=0.1 ),
                # 1 in 10 chance of an apple appearing each second, worth 1 point
                "orange": lambda dimensions: Fruit("orange", dimensions, 10, color=(200,200,0), frequency=0.01 ),
                # 1 in 100 chance of an orange appearing each second, worth 10 points
                "bananna": lambda dimensions: Fruit("bananna", dimensions, 20, color=(255,255,0), frequency=0.005 ),
                # 1 in 200 chance of an bananna appearing each second, worth 10 points
            })
        try:
            for name,fnc in self.fruits.items():
                f = fnc([0,0,self.size])
                assert f.name == name
                assert isinstance(f,Fruit)
            del f
        except Exception as err:
            ValueError(f"Fruits did not return a dictionary containing functions to create Fruit objects {err}")
        
        self.snake = None
        self._loop_counter = 0
        self.__alive_reward_counter = 0
        self.scribe = Scribe("data.db")
        self.start()

    @property
    def score(self):
        """
        Track how many points have been scored, but return as a whole number.
        """
        return int(round(self._score))
    
    @score.setter
    def score(self, value):
        self._score = value

    @property
    def _loop_counter(self):
        """
        Limit how fast the snake moves per second
        """
        return self.__loop_counter
    
    @_loop_counter.setter
    def _loop_counter(self, value):
        self.__loop_counter = value


    @property
    def next_cmd(self):
        """
        Check the input.
        """
        return self.__next_cmd
    
    @next_cmd.setter
    def next_cmd(self, value):
        """
        If the value is a valid command, keep it.
        """
        result = None
        try:
            # debug(f"setting next_cmd to {value}")
            if value is not None:
                if not isinstance(value,str):
                    value = str(value)
                    # make sure value is a str
                if value in self.__valid_keys:
                    # if the value is a valid key
                    result = self.__valid_keys.get(value)
                    # debug(f"read next_cmd {value} as {result} ")
                    # set it 
                else:
                    raise ValueError(f"Unacceptable command key {value} not in {self.__valid_keys}")
        except Exception as err:
            logging.exception(err)
            crit("Failed to set next_cmd")
        finally:
            # debug(f"setting next_cmd to {result}")
            self.__next_cmd = result

    @property
    def game_state(self):
        """
        Check the output pipe for new information.
        """
        result = []
        try:
            result = [
                    # the game
                    [
                        self.playing,
                        # whether the game is playing/paused
                        self.crashed,
                        # whether the game is playing/quit/crashed
                        self.score,
                        # current score for the game
                        self.size,
                        # how big a virual pixel is
                        self.height,
                        # the height of the playing field for this game
                        self.width,
                        # the width of the playing field for this game
                        self.snake_speed,
                        # how fast the snake is limited to move
                        self.auto_tick,
                        # whether the snake continues to move when playing but in absent of a move command
                    ],
                    # the obstacles 
                    [
                        seg.dimensions for seg in self.obstacles
                        # positions of obstacle segments
                    ],
                    # the rewards 
                    [
                        [seg.dimensions, seg.value] for seg in self.rewards
                        # [seg.x, seg.y, seg.value] for seg in self.rewards
                        # positions & values of rewards
                    ],
                    # the snake 
                    [
                        [ 
                            [seg.dimensions, seg.heading] for seg in self.snake.segments 
                            # positions of snake segments
                        ],
                        self.snake.belly,
                        # how many points are in the snakes belly
                        self.snake.length,
                        # how long overall the snake is
                    ],
                ]
            # raise IOError("Output pipe is closed")
        except Exception as err:
            logging.exception(err)
            logging.critical("Failed to execute set_game_state")
        finally:
            # debug(f"set_game_state returning {result}")
            # if result is not None and result is not []:
            #     self.__game_state = result
            return result

    @staticmethod
    def label_state(state):
        def labels_fmt(state,labels):
            d = OrderedDict()
            if state is None:
                return None
            for idx,l in enumerate(labels):
                if isinstance(l,str):
                    d[l] = state[idx]
                elif isinstance(l,tuple) and len(l) == 2 and isinstance(l[1],list):
                    name, lbs = l
                    temp = []
                    for item in state[idx]:
                        if all([isinstance(i,str) for i in lbs]):
                            temp += [OrderedDict([a for a in zip(lbs, item)])]
                        else:
                            temp += [labels_fmt(item, tuple(lbs))]
                    d[name] = temp
                elif isinstance(l,tuple) and len(l) == 2 and isinstance(l[1],tuple):
                    name, lbs = l
                    d[name] = labels_fmt(state[idx],lbs)
                elif callable(l):
                    return l(*state)
                else:
                    for i,name in enumerate(l):
                        if isinstance(state[idx],(tuple,list)) :
                            if len(state[idx]) < i+1:
                                d[name] = None
                            else:
                                d[name] = state[idx][i]
                        else:
                            d[name] = state[idx]
            return d
        obstacle_str = lambda x,y,w,h: f"Obstacle< x:{x: >5}, y:{y: >5}, w:{w: >5}, h:{h: >5}>"
        fruit_str = lambda dm,vl: f"Fruit< x:{dm[0]: >5}, y:{dm[1]: >5}, w:{dm[2]: >5}, h:{dm[2]: >5}, value:{vl}>"
        # segment_str = lambda dm,hd: f"Segment< x:{dm[0]: >5}, y:{dm[1]: >5}, w:{dm[2]: >5}, h:{dm[3]: >5}, heading:{hd}>"
        segment_str = lambda dm,hd: f"Segment< {dm} {hd} >"
        labels = (
                ("meta",("playing", "crashed", "score", "size", "height", "width", "snake_speed", "auto_tick")),
                ("obstacles", [
                                obstacle_str
                                # "x", "y", "w", "h"
                            ]),
                ("rewards", [
                                fruit_str
                                # ("x", "y", "s"),"v"
                            ]),
                ("snake", (
                        ("segments",[
                            # ("x", "y", "w", "h"),"heading"
                            segment_str
                        ]),
                        "belly",
                        "length",
                        )
                )
            )
        result = labels_fmt(state, labels)
        return result

    @staticmethod
    def compare_states(list_a, list_b):
        result = True
        try:
            if isinstance(list_b,list) and isinstance(list_a,list):
                if len(list_a) == len(list_b):
                    for idx,item in enumerate(list_b):
                        if result is False:
                            break
                        if isinstance(item,list) and len(list_a) < idx+1:
                            result = False 
                            break
                        if isinstance(item,list) and len(list_a) >= idx+1:
                            result = SnakeGame.compare_states(list_a[idx], list_b[idx])
                        else:
                            result = (list_a[idx] == list_b[idx])
                else:
                    result = False
            elif type(list_a) == type(list_b):
                if isinstance(list_a, (Segment,Obstacle)):
                    props = ["x","y","w","h","heading"]
                elif isinstance(list_a, Fruit):
                    props = ["x","y","w","h","value"]
                elif isinstance(list_a, Snake):
                    props = ["x","y","w","h"]
                    result = compare_states(list_a.segments, list_b.segments)
                    result = compare_states(list_a.belly, list_b.belly) and result
                    result = compare_states(list_a.heading, list_b.heading) and result
                    return result
                else:
                    props = list_a.__dict__.keys()
                for k in props:
                    if not hasattr(list_b,k) or list_b.__dict__[k] != list_a.__dict__[k]:
                        result = False 
                        break
            else:
                result = (list_a == list_b)
        except Exception as err:
            result = False
            error(f"Game.compare_states error: {err}")
        finally:
            return result
    
    def _set_seed(self, seed):
        self._seed = seed
        self.rand.seed(self._seed)

    def _init_randomizer(self, seed=None):
        self._seed = 1
        self.rand = random.Random()
        if seed is not None:
            self._set_seed(seed)

    def _init_rewards(self):
        self.rewards = []
        # self.scribe.record_fruits(self.rewards)


    def _init_boundaries(self):
        """
        Initialize the game boundaries; the four walls that surround the exterior of the game
        """
        self.obstacles = [
                # x,y,w,h
                Obstacle(0, -self.size, self.width, self.size),
                # north wall
                Obstacle(self.width, 0, self.size, self.height),
                # east wall
                Obstacle(0, self.height, self.width, self.size),
                # south wall
                Obstacle(-self.size, 0, self.size, self.height),
                # west wall
            ]
        # self.scribe.record_obstacles(self.obstacles)

    @property
    def can_germinate(self):
        """
        Whethe next_fruit can be set and spawn another reward object.
        """
        return len(self.rewards) < self.reward_limit

    @staticmethod
    def __access_fruit_freq(fruit):
        return fruit[1]

    def _organize_fruit(self):
        """
        Setup an attribute to track probabilities for the different fruits.
        """
        fruit_chances = []
        for name,fnc in self.fruits.items():
            fruit = fnc([0,0,self.size])
            fruit_chances += [(name, fruit.frequency)]
        self.fruit_chances = list(sorted(fruit_chances, key=SnakeGame.__access_fruit_freq))
        # sort them by their frequency (low to high) and store it as an attribute
        for idx,fruit in enumerate(self.fruit_chances):
            # for each fruit, least valuable to most valuable, 
            self.__valid_keys[str(idx+7)] = idx+7
            # accept a key that will spawn it 

    def get_point(self, depth=0):
        """
        Pick a point within the game boundaries and not currently occupied.
        """
        if depth >= 30:
            error("Went too deep trying to generate a random point")
            return (0,0)
        debug(f"Getting random point depth = {depth}")
        x = self.rand.randrange(0, self.width, self.size)
        y = self.rand.randrange(0, self.height, self.size)
        if x <= 0 or y <= 0:
            self._set_seed(self._seed+10)
            return self.get_point(depth=depth+1)
            # try to get a new random x,y point
        pseudo_segment = Segment([x, y, self.size, self.size],0)
        debug(f"Checking point {depth} against obstacles")
        for wall in self.obstacles:
            if Snake.intersects(wall, pseudo_segment):
                debug(f"point {pseudo_segment} intersects with wall")
                return self.get_point(depth=depth+1)
                # try to get a new random x,y point
        debug(f"Checking point {depth} against fruits")
        for fruit in self.rewards:
            if Snake.intersects(fruit, pseudo_segment):
                debug(f"point {pseudo_segment} intersects with fruit")
                return self.get_point(depth=depth+1)
                # try to get a new random x,y point
        debug(f"Checking point {depth} against Snake segments")
        if self.snake is not None and Snake.intersects(self.snake, pseudo_segment):
            debug(f"point {pseudo_segment} intersects with Snake")
            return self.get_point(depth=depth+1)
            # try to get a new random x,y point
        debug(f"Point {depth} approved")
        return (x,y)

    def get_fruit(self):
        """
        Pick what the next fruit to spawn will be.
        """
        if self.next_fruit is None and self.can_germinate:
            for name,chance in self.fruit_chances:
                if self.auto_tick:
                    # if the game is set to automatically progress, regardless of having an 
                    # active command, 
                    chance = chance/self.frames
                    # reduce the chance of spawning by how often get_fruit will be called per second
                if len(self.rewards) <= 0:
                    # if there currently are no rewards present
                    chance = chance*10
                    # increase the likelihood that there will be a reward spawned
                if self.rand.random() <= chance:
                    self.next_fruit = name
                    # debug(f"Next fruit will be {self.next_fruit}")
                    break

    def spawn_next_fruit(self):
        """
        Instantiate the next fruit object in the game.
        """
        if self.next_fruit in self.fruits and self.can_germinate:
            point = self.get_point()
            if point is not None and self.scribe.get_state:
                x,y = point
                fruit = self.fruits.get(self.next_fruit)([x,y,self.size])
                self.rewards += [fruit]
                # debug(f"Next fruit spawned {self.next_fruit}")
                self.scribe.record_fruits(fruit)
                self.next_fruit = None
                return fruit

    def _get_snake(self, depth=0):
        """
        Use the current attributes of the game to create a new snake object.
        """
        # debug("Game._get_snake")

        heading = self.rand.randint(0,3)
        # choose an integer between 0 and 3 to represent a cardinal direction
        position = self.get_point()
        if position is not None:
            try:
                snake = Snake([position[0], position[1], self.size, self.starting_length*self.size], heading)
            except Exception as err:
                snake = Snake([position[0], position[1], self.size, self.starting_length*self.size], (heading+1)%4)
            # safe_distance = int(round(min(self.width, self.height)/10))
            safe_distance = 5
            if self._peek(snake, snake.heading, safe_distance):
                # self.scribe.record_snake(snake)
                return snake
            else:
                if depth >= 30:
                    error("Went too deep trying to get a safe spawn for snake")
                    return None
                else:
                    return self._get_snake(depth=depth+1)
            # return a snake object that's within the game boundaries
        else:
            raise ValueError("Failed to pick a random point to spawn the snake")

    def spawn_snake(self):
        """
        Spawn a snake for the game
        """
        # debug("Game.spawn_snake")
        if self.snake is None:
            self.snake = self._get_snake()

    def start(self):
        self.obstacles = []
        # a list of Obstacle objects that would kill the snake
        self.rewards = []
        # a list of Fruit objects that would feed the snake
        self.next_fruit = None
        # None, or a string to indicate the next Fruit object that should be added
        self.snake = None
        # None, or a Snake object
        self._loop_counter = 0
        # counter to track whether movement is allowed
        self.__alive_reward_counter = 0
        # counter to track how much to reward the player for staying alive this long
        self._fruit_count = []
        # how many fruit of which values were consumed
        self._init_randomizer()
        self._organize_fruit()
        self._init_rewards()
        self._init_boundaries()
        self.spawn_snake()
        self.scribe.record_game_start(self)

    @property
    def alive_counter(self):
        """
        How many times the game awarded some points for they player staying alive
        """
        return self.__alive_reward_counter

    @property
    def alive_bonus(self):
        """
        Total points awarded for just staying alive
        """
        return sum([SnakeGame.__still_alive_reward_fnc(x) for x in range(self.__alive_reward_counter) ])

    @property
    def fruit_count(self):
        """
        Track how many times each unique fruit is eaten.
        """
        return [(cnt,val) for cnt,val in self._fruit_count]
        # return a list, where each item is a tuple

    def count_fruit(self,value):
        """
        A fruit was eaten: increment its counter, or start a counter for it.
        """
        if len(self._fruit_count) == 0:
            # if no fruit have been eaten yet
            self._fruit_count = [[1,value]]
            # create a counter tracking that we've awarded this value once
        else:
            for idx,(occurences,val) in enumerate(self._fruit_count):
                # for each fruit value we've awarded
                if val == value:
                    # if the values are the same
                    self._fruit_count[idx] = [occurences+1,value]
                    # increment the counter
                    break
                    # count_fruit has now counted the fruit with value, 
                    # exit the loop 
                elif val <= value:
                    # if the new value is greater than the current 
                    # value we're checking in the list of counters,
                    self._fruit_count.insert(idx,[1,value])
                    # insert a counter after it
                    break
                    # count_fruit has now counted the fruit with value, 
                    # exit the loop 
    @property
    def fruit_bonus(self):
        """
        Total points awarded for eating fruit
        """
        return sum([cnt*val for cnt,val in self._fruit_count])
    

    def get_still_alive_reward(self):
        """
        Award points for staying alive, but award more points towards the start
        of the game, and less points later on (but never no points)
        """
        # experimented with https://www.desmos.com/calculator
        # to find the right function I wanted to use;
        # the sliders were very helpful
        
        # y = (log(-x+1)+2)/2
        # y = 1/(1+e^(x*5-5))

        # x = (1-tan(y+1.5))*0.5

        # y = -atan((x/0.5)-1)+1.7
        # {0 < y <= 3}
        self.__alive_reward_counter += 1
        # self._score += ((-1*math.atan((self.__alive_reward_counter/0.5)-1))+1.7)
        self._score += SnakeGame.__still_alive_reward_fnc(self.__alive_reward_counter)
        # add the float to the hidden attribute; whereas 'score' will be the rounded
        # value of _score

    def update(self):
        """
        Progress the state of the game forward.
        """
        debug("UPDATE GAME STATE")
        state_changed = False
        moved_snake = False
        # 1) get cmd
        # 3) iff cmd exit -> exit
        # 4) iff cmd play/pause -> play/pause
        # 4) iff cmd restart/start -> restart/start
        # 2) iff cmd move -> move snake
        # 2) elif auto_tick & playing
        #     a) move snake in current heading
        #     b) do nothing to snake
        # 2) iff cmd fruit
        #     a) set next_fruit
        #     b) set next_fruit
        # 3) spawn next_fruit

        # cmd = self.snake.heading if self.auto_tick else None
        self._loop_counter += 1
        cmd = None
        # set a fallback value 
        # debug(f"self.next_cmd = {self.next_cmd}")
        if self.next_cmd is not None:
            # check if we've been given a command to execute
            cmd = int(self.next_cmd)
            if cmd in [4,5,6]:
                # if it can be immediately used
                self.scribe.record_command(cmd)
                self.next_cmd = None
                # remove the cached command

        if cmd == 4:
            # escape/spacebar     pause/play
            info("recv pause/play command")
            self.playing = self.playing is False
            # set the game to be playing if it wasnt,
            # and not playing if it was playing
            return
            # do nothing else during this update call
        elif cmd == 5:
            # restart/start
            info("recv restart command")
            if self.playing is False:
                # if we were not playing 
                self.playing = True
                # we are now
                return
                # do nothing else during this update call
        elif cmd == 6:
            # quit
            info("recv quit command")
            self.playing = False
            self.crashed = True
            return
            # do nothing else during this update call
        if self.playing:
            # if the game is currently playing

            # handle the snake
            move = None
            if cmd in [i for i in range(4)]:
                # if the next command is to tell the snake to move in a cardinal direction
                move = cmd
            elif self.auto_tick and self.playing:
                # if the snake was not told the direction to move AND its set to keep moving
                # in the last heading it was given and we're still playing
                # debug(f"MOVING SNAKE VIA {self.snake.heading}")
                move = self.snake.heading
            else:
                pass
                # leave the snake alone
            limit = int(self.frames/self.snake_speed)
            # if move is not None and (self.auto_tick is False or self._loop_counter >= limit or limit == 1):
            if move is not None and (self._loop_counter >= limit or limit == 1):
                # if we're allowed to move during this cycle
                debug(f"MOVING SNAKE TO {cmd} - {move}")
                self.snake.move(move)
                state_changed = True
                self._loop_counter = -1
                self.get_fruit()
                self.scribe.record_command(move)
                self.next_cmd = None
                # remove the cached command now that we've used it
            # else:
            #     debug(f"no move because {move} is not None and {self._loop_counter} >= {self.frames}/{self.snake_speed}")
            #     debug(f"no move because {move} is not None and {self._loop_counter} >= {int(self.frames/self.snake_speed)}")
            #     debug(f"no move because {move is not None} and {self._loop_counter >= int(self.frames/self.snake_speed)}")
                for wall in self.obstacles:
                    if self.snake.is_alive:
                        if self.snake.intersects(self.snake.head,wall):
                            info(f"Snake hit {wall}")
                            self.snake.interact(wall)
                if self.snake.is_alive:
                    for fruit in self.rewards:
                        if self.snake.intersects(self.snake.head,fruit):
                            info(f"Snake hit {fruit.name} @ {fruit.origin} worth {fruit.value}")
                            self.count_fruit(fruit.value)
                            self.score += fruit.value
                            self.snake.interact(fruit)
                            self.rewards.remove(fruit)
                if self.snake is not None and self.snake.is_alive:
                    self._last_length = self.snake.length
                    # store the snake length to be accessed when the game ends and there is no snake
                    self.get_still_alive_reward()
                elif self.scribe.get_game_instance:
                    self.scribe.record_game_end(get_timestamp())

            # handle the fruit 
            if cmd is not None and cmd-7 in [i for i in range(0, len(self.fruit_chances))]:
                # we're told to spawn a specific fruit
                self.scribe.record_command(cmd)
                cmd = cmd - 7
                self.next_fruit = list(reversed(self.fruit_chances))[cmd][0]
                # store the fruit name
                self.next_cmd = None
                # remove the cached command now that we've used it
            elif self.auto_tick:
                # we're NOT told to spawn a specific fruit, we're currently 
                reward_qty = len(self.rewards)
                self.get_fruit()
                # handle choosing the next fruit to instantiate
                state_changed = self.next_fruit is not None and self.can_germinate
            self.spawn_next_fruit()
            # handle instantiating the next fruit at a random point
            if state_changed:
                self.scribe.record_state({
                        "score": self.score,
                        "fruits": self.rewards,
                        "obstacles": self.obstacles,
                        "snake": self.snake,
                    })
        else:
            # the game is currently not playing,
            # we don't need to change the snake or fruit
            self.next_cmd = None
        # if self.scribe.get_game_instance is not None and (self.snake is None or not self.snake.is_alive):
        #     self.scribe.record_game_end(get_timestamp())
        
    def _peek(self, snake, direction, distance):
        """
        Check whether moving the snake in "direction" by "distance" units,
        would result in it intersecting an object.
        """
        survived = True
        try:
            astral_snake = copy.deepcopy(snake)
            while distance > 0:
                astral_snake.move(direction)
                for wall in self.obstacles:
                    if astral_snake.is_alive:
                        if astral_snake.intersects(astral_snake.head,wall):
                            debug(f"Astral Snake hit {wall}")
                            astral_snake.interact(wall)
                if astral_snake.is_alive:
                    for fruit in self.rewards:
                        if astral_snake.intersects(astral_snake.head,fruit):
                            debug(f"Astral Snake hit {fruit}")
                            astral_snake.interact(fruit)
                if not astral_snake.is_alive:
                    survived = False
                    break
                distance -= 1
        except Exception as err:
            survived = False
            error(f"Game.peek error: {err}")
        finally:
            return survived
