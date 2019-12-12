import contextlib
with contextlib.redirect_stdout(None):
    import pygame.time as gtime
del contextlib
import random
from objects.snake import Snake
from objects.segment import Segment
from objects.obstacle import Obstacle
from objects.fruit import Fruit
import multiprocessing
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



# def never_release_lock(self):
#     if not self.locked():
#         raise RuntimeError("This lock should never be released by another process")
#     else:
#         warn("This lock should never be released")

class SnakeGame(object):
    """
    Setup a game to create and track the current state of the game.
    """
    defaults = {
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
        self.__flow_lock = multiprocessing.RLock()
        # create a lock that will dictate who can do what to which properties
        # self.__flow_lock.release = never_release_lock
        self.__cmd_child, self.__cmd_parent = multiprocessing.Pipe(duplex=True)
        # create a pipe to receive the next command; 
        # the Process that instantiated this object should only ever use self.__cmd_child to recieve data, 
        # while other Processes should use self.__cmd_parent to send data
        self.__state_child, self.__state_parent = multiprocessing.Pipe(duplex=True)
        # create a pipe to output the current game state; 
        # the Process that instantiated this object should only ever use self.__state_child to send data, 
        # while other Processes should use self.__state_parent to recieve data
        self.__flow_lock.acquire()
        # the instatiated object now has ownership of the pipes:
        #     this process:
        #         cmd:
        #             child: listen 
        #                         for next command
        #         state:
        #             child: send 
        #                         the current state of the game
        #     other process:
        #         cmd:
        #             parent: send 
        #                         what the next command will be
        #         state:
        #             parent: listen 
        #                         to what the current state of the game is
        self._loop_counter = 0
        self.start()
    # @property
    # def input(self):
    #     """
    #     A pipe to receive the next command.
    #     """
    #     # send
    #     # recv
    #     # poll
    #     # exitcode
    #     if self.__input.poll(self.timeout):
    #         self.__input.recv()
    #         # self.__input.recv_bytes(maxlength=16)
    #     return self.__input
    
    # @input.setter
    # def input(self, value):
    #     self.__input = value
    
    # @property
    # def output(self):
    #     """
    #     A pipe to output the current game state.
    #     """
    #     # send
    #     # recv
    #     # poll
    #     # exitcode
    #     return self.__output
    
    # @output.setter
    # def output(self, value):
    #     if self.__flow_lock.locked():
    #         # if we have ownership of the flow of data
    #         self.__output = value
    #     else:
    #         raise IOError("Do not have permission to write to output")
    @property
    def _loop_counter(self):
        """
        Limit how fast the snake moves per second
        """
        return self.__loop_counter
    
    @_loop_counter.setter
    def _loop_counter(self, value):
        self.__loop_counter = value
        # if (self.__loop_counter) > self.snake_speed*60
        # # self.snake_speed/60
    
    @property
    def owns_instance(self):
        """
        Whether the calling process owns this instantiated object.
        """
        return self.__flow_lock._semlock._is_mine()

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
        result = None
        try:
            # debug(f"getting game_state")
            if self.owns_instance:
                # if the calling Process owns this instantiated object
                result = self.set_game_state()
                # set the latest state of the game

                # result = self.__game_state
                # # used the last cached state
            else:
                if self.__state_parent.poll():
                    # if there's new data waiting to be received
                    result = self.__state_parent.recv()
                    # use the new data
                else:
                    result = self.__game_state
                    # used the last cached state
        except Exception as err:
            logging.exception(err)
            logging.critical("Failed to get game_state")
        finally:
            return result
    
    @game_state.setter
    def game_state(self, value):
        # debug(f"setting game_state")
        raise RuntimeError("Use set_game_state() instead of trying to directly set the game_state property")

    def set_game_state(self):
        """
        Collate the state of the game and send it on the output pipe.
        """
        result = None
        try:
            if not self.owns_instance:
                warn("Only the process that owns this object should be setting the state of the game")
                # do it anyway, rather than cause problems...
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
                    ],
                ]
            # raise IOError("Output pipe is closed")
        except Exception as err:
            logging.exception(err)
            logging.critical("Failed to execute set_game_state")
        finally:
            # debug(f"set_game_state returning {result}")
            if result is not None:
                self.__game_state = result
            return self.__game_state
    
    def _test_next_cmd_setter(self,value):
        """
        A method that is used in testing to ensure next_cmd
        can be set by a separate process.
        """
        if not self.owns_instance:
            self.next_cmd = value
        else:
            warn("This should not be called by the Process that owns this object")
    def _test_game_state_setter(self,value):
        """
        A method that is used in testing to ensure game_state
        can be set by a separate process.
        """
        if not self.owns_instance:
            self.game_state = value
        else:
            warn("This should not be called by the Process that owns this object")
        
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
        x = self.rand.randrange(0, self.width, self.size)
        y = self.rand.randrange(0, self.height, self.size)
        if x <= 0 or y <= 0:
            self._set_seed(self._seed+10)
            return self.get_point(depth=depth+1)
            # try to get a new random x,y point
        pseudo_segment = Segment([x, y, self.size, self.size],0)
        for wall in self.obstacles:
            if Snake.intersects(wall, pseudo_segment):
                debug(f"point {pseudo_segment} intersects with wall")
                return self.get_point(depth=depth+1)
                # try to get a new random x,y point
        for fruit in self.rewards:
            if Snake.intersects(fruit, pseudo_segment):
                debug(f"point {pseudo_segment} intersects with fruit")
                return self.get_point(depth=depth+1)
                # try to get a new random x,y point
        if self.snake is not None and Snake.intersects(self.snake, pseudo_segment):
            debug(f"point {pseudo_segment} intersects with Snake")
            return self.get_point(depth=depth+1)
            # try to get a new random x,y point
        return (x,y)
    def get_fruit(self):
        """
        Pick what the next fruit to spawn will be.
        """
        if self.next_fruit is None and self.can_germinate:
            for name,chance in self.fruit_chances:
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
            if point is not None:
                x,y = point
                fruit = self.fruits.get(self.next_fruit)([x,y,self.size])
                self.rewards += [fruit]
                # debug(f"Next fruit spawned {self.next_fruit}")
                self.next_fruit = None
                return fruit
    def _get_snake(self):
        """
        Use the current attributes of the game to create a new snake object.
        """
        debug("Game._get_snake")

        heading = self.rand.randint(0,3)
        # choose an integer between 0 and 3 to represent a cardinal direction
        position = self.get_point()
        if position is not None:
            try:
                snake = Snake([position[0], position[1], self.size, self.starting_length*self.size], heading)
            except Exception as err:
                snake = Snake([position[0], position[1], self.size, self.starting_length*self.size], (heading+1)%4)
            return snake
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
        self._init_randomizer()
        self._organize_fruit()
        self._init_rewards()
        self._init_boundaries()
        self.spawn_snake()
    def update(self):
        """
        Progress the state of the game forward.
        """
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
                self.next_cmd = None
                # remove the cached command

        if cmd == 4:
            # escape/spacebar     pause/play
            debug("escape/spacebar")
            self.playing = self.playing is False
            # set the game to be playing if it wasnt,
            # and not playing if it was playing
            return
            # do nothing else during this update call
        elif cmd == 5:
            # restart/start
            debug("restart/start")
            if self.playing is False:
                # if we were not playing 
                self.playing = True
                # we are now
                return
                # do nothing else during this update call
        elif cmd == 6:
            # quit
            debug("quit")
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
            if move is not None and self._loop_counter >= self.frames/self.snake_speed:
                # if we're allowed to move during this cycle
                debug(f"MOVING SNAKE TO {cmd} - {move}")
                self.snake.move(move)
                self._loop_counter = -1
                self.get_fruit()
                self.next_cmd = None
                # remove the cached command now that we've used it
            for wall in self.obstacles:
                if self.snake.is_alive:
                    if self.snake.intersects(self.snake.head,wall):
                        debug(f"Snake hit {wall}")
                        self.snake.interact(wall)
            if self.snake.is_alive:
                for fruit in self.rewards:
                    if self.snake.intersects(self.snake.head,fruit):
                        debug(f"Snake hit {fruit}")
                        self.snake.interact(fruit)
                        self.rewards.remove(fruit)

            # handle the fruit 
            if cmd is not None and cmd-7 in [i for i in range(0, len(self.fruit_chances))]:
                # we're told to spawn a specific fruit
                cmd = cmd - 7
                self.next_fruit = list(reversed(self.fruit_chances))[cmd][0]
                # store the fruit name
                self.next_cmd = None
                # remove the cached command now that we've used it
            elif self.auto_tick:
                # we're NOT told to spawn a specific fruit, we're currently 
                self.get_fruit()
                # handle choosing the next fruit to instantiate
            self.spawn_next_fruit()
            # handle instantiating the next fruit at a random point
        else:
            # the game is currently not playing,
            # we don't need to change the snake or fruit
            # if cmd in []:
            self.next_cmd = None
        
    def play(self):
        """
        Change the game to a playing state.
        """ 
        self.playing = True
        
    def pause(self):
        """
        Change the game to a paused state.
        """ 
        self.playing = False

    def __getstate__(self):
        # capture what is normally pickled
        state = self.__dict__.copy()
        # state["clock"] = None
        # # Can't pickle pygame.time.Clock
        # state["fruit"] = { k:None for k,v in self.fruits.items() }
        # # Can't pickle lambda functions
        # state["snake"] = None
        # state["obstacles"] = []
        # state["rewards"] = []

        # approved = ["flow_lock","__cmd","__state"]
        # for k,v in state.items():
        #     if all([k.find(a) == -1 for a in approved]):
        #         state[k] = None
        
        denied = ["clock"]
        for k,v in state.items():
            if k == "fruits":
                state[k] = { k:None for k,v in self.fruits.items() }
            elif any([k.find(d) != -1 for d in denied]):
                state[k] = None


        # # replace the `value` key (now an EnumValue instance), with it's index:
        # state['value'] = state['value'].index
        # # what we return here will be stored in the pickle
        return state

    # def __setstate__(self, newstate):
    #     # re-create the EnumState instance based on the stored index
    #     newstate['value'] = self.Values[newstate['value']]
    #     # re-instate our __dict__ state from the pickled state
    #     self.__dict__.update(newstate)

def spawn_next_cmd_tester(self,value):
    """
    """
    proc = multiprocessing.Process(target=SnakeGame._test_next_cmd_setter,args=(self,value,))
    proc.start()
    proc.join()
    
def spawn_game_state_tester(self,value):
    """
    """
    proc = multiprocessing.Process(target=SnakeGame._test_game_state_setter,args=(self,value,))
    proc.start()
    proc.join()