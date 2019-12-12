import contextlib
with contextlib.redirect_stdout(None):
    import pygame as pg
del contextlib
# from auxillary import trace_call_path
import logging
import time
import re
import os
import copy
import json
from interfaces.game import SnakeGame

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
        "title": "Snake",
        "icon": "./resources/snake_iconx32.png",
        "background": (0,0,0),
        "obstacle_color": (0,0,255),
        "screenshot_path": "./screenshots/",
        # "snake_color": lambda i,t: (0,255-min(i/t*255, 10),0),
        "fonts":{
            "normal": {
                "family": "./resources/Roboto-Regular.ttf",
                "size": 32
            },
        },
    }
    valid_keys = {
        "north":{
            "codes": [pg.K_UP],
            "direction":0,
            "cmd": 0
        },
        "east":{
            "codes": [pg.K_RIGHT],
            "direction":1,
            "cmd": 1
        },
        "south":{
            "codes": [pg.K_DOWN],
            "direction":2,
            "cmd": 2
        },
        "west":{
            "codes": [pg.K_LEFT],
            "direction":3,
            "cmd": 3
        },
        "pause/play":{
            "codes": [pg.K_SPACE],
            "cmd": 4
        },
        "retry":{
            "codes": [pg.K_r],
            "cmd": 5
        },
        "quit":{
            "codes": [pg.K_ESCAPE, pg.K_q],
            "cmd": 6
        },
        "apple":{
            "codes": [pg.K_a],
            "cmd": 7
        },
        "orange":{
            "codes": [pg.K_o],
            "cmd": 8
        },
        "bananna":{
            "codes": [pg.K_b],
            "cmd": 9
        }
    }
    move_codes = [pg.K_UP, pg.K_LEFT, pg.K_DOWN, pg.K_RIGHT]
    def __init__(self, game, *args, **kwargs):
        super(Gameboard, self).__init__()
        for k,v in self.defaults.items():
            # for each item in the default configuration
            setattr(self, k, kwargs.get(k,v))
            # try to get and use a keyword argument, else use default; 
            # set value for the attribute
        self.app_surface = None
        self.game = game
        # self._init_gui()
        for name,font in self.fonts.items():
            self.fonts[name]["size"] = min(32, max(10,round(self.width/640*font.get("size"))))
        self.key_sequence = []
        self.valid_codes = [ code for name,key_cfg in self.valid_keys.items() for code in key_cfg.get("codes") ]
        self.latest_state = None
        self.screenshot_counter = 0
        if isinstance(self.screenshot_path,str):
            self.screenshot_path = os.path.realpath(os.path.normpath(os.path.expanduser(os.path.expandvars(self.screenshot_path))))

    @property
    def testing(self):
        return self.game.testing
    
    @testing.setter
    def testing(self, value):
        self.game.testing = value

    def _simplify_pattern(self, sequence):
        """
        Simplify (down, up, down) pattern to (down).
        """
        redundancies = []
        # variable to store indeces for events we need to remove
        last_up_buffer = None
        # variable to store down,up pairs for a key, while we check for 
        # another down event for the same key
        for idx,(prv_key,key_type) in enumerate(sequence):
            # for every key event in the sequence
            last_up_buffer = None
            # reset the temp variable since we're checking a new key for 
            # redundant events
            if key_type == pg.KEYDOWN:
                # if we're checking a key being pressed down 
                for i,(pk,kt) in enumerate(sequence):
                    # check it against the other key events in the sequence
                    # that come after it
                    if i <= idx:
                        # if its the same index, or before it, skip it
                        pass
                    elif pk == prv_key:
                        # if the index is not the same, but the key is
                        if kt == pg.KEYUP:
                            # we found a down, up pair for a key
                            last_up_buffer = (idx,i)
                            # remember the pair of down, up events for this key
                        elif kt == pg.KEYDOWN and last_up_buffer is not None:
                            # we found another down after a down,up pair was found
                            first_down, first_up = last_up_buffer
                            redundancies += [first_up, i]
                            # remember to remove the previous up, and this redundant down event;
                            # as if the key had remained down instead of down, up, down
                            last_up_buffer = None
                            # reset the temp variable
                            # keep checking prv_key for any more down,up,down patterns
        # debug(f"redundancies {redundancies}")
        return [item for i,item in enumerate(sequence) if i not in redundancies]
    def _remove_duplicates(self, sequence):
        """
        Simplify (down, down, down, ...) pattern for the Same Key to (down), 
        and do the same for repeat up events.
        """
        redundancies = []
        # variable to store indeces for events we need to remove
        # sequence_buffer = []
        # # events we've approved and want to keep
        for idx,(prv_key,key_type) in enumerate(sequence):
            # for every key event in the sequence
            for i,(pk,kt) in enumerate(sequence):
                # check it against the other key events in the sequence
                # that come after it
                if i <= idx:
                    # if its the same index, or before it, skip it
                    pass
                elif pk == prv_key and kt == key_type:
                    # the code and type are the same
                    redundancies += [i]  
                    # make a note to remove this duplicate
                else:
                    break
        # for idx,item in enumerate(sequence):
        #     # for each event in the sequence
        #     if idx not in redundancies:
        #         # if we did not note it was redundant
        #         sequence_buffer += [item]
        #         # keep the event
        # return sequence_buffer
        return [item for i,item in enumerate(sequence) if i not in redundancies]
        # return the sequence without the duplicates
    def _ensure_persistance(self, sequence, interval=6):
        """
        Ensure a pressed key over a 
        long period is reflected in the sequence.
        """
        # Example: the sequence
        # [Av, Bv, B^, Cv, C^, Dv, D^, Ev, Fv, E^, F^... A^]
        # where "v" is down, and "^" is up,
        # would result in the A command being passed only once at the start, 
        # but since A has not released yet, we want it to keep performing A 
        # between all these other commands too; 
        # so the new sequence should be more like
        # [Av, Bv, B^, Cv, C^, Dv, D^, Av, Ev, Fv, E^, F^, Av ... A^]
        
        persisting = []
        # a buffer for keys that are down and need to relfect that
        keys_between = 0
        # how many events occur between the down event and when (if) it was released
        sequence_buffer = sequence
        buffer_additions = 0
        for idx,(prv_key,key_type) in enumerate(sequence):
            # for every key event in the sequence
            if key_type == pg.KEYDOWN and prv_key in self.move_codes:
                # if we're checking a key being pressed down 
                keys_between = 0
                # reset the counter
                found_key_up = False
                for i,(pk,kt) in enumerate(sequence):
                    # check it against the other key events in the sequence
                    # that come after it
                    if i <= idx:
                        # if its the same index, or before it, skip it
                        pass
                    else:
                        if pk != prv_key:
                            # if they are not the same key
                            keys_between += 1
                            # count the event as between the down and the next up 
                            pass
                        elif kt == pg.KEYDOWN:
                            # if they are the same key and,
                            # this next event represents the key remaining down
                            break
                            # stop checking first down at idx against the rest of the the sequence;
                            # a down event has already been added
                        # debug(f"{prv_key} keys_between {keys_between}")
                        # debug(f"prv_key = {prv_key} and kt == pg.KEYUP  {kt == pg.KEYUP }")
                        # debug(f"keys_between <= interval  {keys_between <= interval }")
                        # debug(f"keys_between > interval  {keys_between > interval }")
                        # debug(f"kt == pg.KEYUP  {kt == pg.KEYUP }")
                        if pk == prv_key and kt == pg.KEYUP and keys_between <= interval:
                            # if the key down event is followed soonish by an up event
                            break
                        elif keys_between > interval:
                            # debug(f"adding down event for {prv_key}")
                            buffer_additions += 1
                            # note that we're adding an extra event
                            sequence_buffer.insert(i,(prv_key, key_type))
                            # insert another down event for this key after this latest event we just checked
                            break
        return sequence_buffer
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
        for event in pg.event.get():
            # for eveery detected event
            if event.type == pg.QUIT:
                self.game.crashed = True
            elif hasattr(event,"key") and event.key in self.valid_codes:
                # if its a key that means something
                self.key_sequence += [(event.key, event.type)]
                # add it to our list of key events that we need to convey to the game
        self.key_sequence = self._simplify_pattern(self.key_sequence)
        # (down, up, down) -> (down)
        self.key_sequence = self._ensure_persistance(self.key_sequence)
        # [Av, Bv, B^, Cv, C^, Dv, D^, Ev, Fv, E^, F^... A^] ->
        #     [Av, Bv, B^, Cv, C^, Dv, D^, Av, Ev, Fv, E^, F^, Av ... A^]
        self.key_sequence = self._remove_duplicates(self.key_sequence)
        # [Av, Av, Av, Bv, Av, A^, A^, B^] -> [Av, Bv, Av, A^, B^]


        if self.game.next_cmd is None:
            # if the game is ready to receive its next command
            # debug(f"self.key_sequence = {self.key_sequence}")
            while self.game.next_cmd is None and self.key_sequence:
                debug(f"self.key_sequence = {self.key_sequence}")
                key_code, key_type = self.key_sequence.pop(0)
                # get the first code in the sequence; the next key the game should receive
                if key_type == pg.KEYDOWN:
                    # if the key is pressed
                    for key_name, key_cfg in self.valid_keys.items():
                        # for every valid key 
                        if key_code in key_cfg.get("codes"): 
                            # if the key event is in the list of approved codes
                            self.game.next_cmd = key_cfg.get("cmd")
                            # give the game the corresponding command for that key 
                            if not any([ (kc == key_code and key_type == pg.KEYDOWN and kt == pg.KEYUP) for (kc,kt) in self.key_sequence]) and key_code in self.move_codes and self.game.playing: 
                                # if there is no key up in the sequence 
                                self.key_sequence += [(key_code, key_type)]
                            break
        # else:
        #     debug(f"Waiting for next_cmd to be consumed")
    def simulate_keys(self, *args, **kwargs):
        valid_directions = {
                "^": pg.KEYUP,
                "v": pg.KEYDOWN,
            }
        delimiter = kwargs.get("delimiter", ",")
        # get the delimiter
        action = kwargs.get("action", "return")
        # get the action
        delimiter = re.sub(r"\s+","", delimiter)
        # remove whitespace
        sequence = []
        for a in args:
            if isinstance(a,str):
                sequence += re.sub(r"\s+","", a).split(delimiter)
                # remove all whitespace and split into a list 
                # before adding it to the sequence
            elif isinstance(a, (list,tuple)):
                sequence += [i for i in a]
                # add it to the sequence
            else:
                raise TypeError(f"Unable to parse {type(a)}")
        for idx,event in enumerate(sequence):
            key, direction = (event[0:-1], event[-1])
            direction = direction.lower()
            if direction not in valid_directions.keys():
                raise ValueError(f"Unable to parse key type from {event}")
            direction = valid_directions.get(direction)
            if len(key) == 1:
                key = "K_"+key.lower()
            else:
                key = "K_"+key.upper()
            if key in dir(pg):
                key = pg.__dict__[key]
            else:
                raise ValueError(f"Unable to parse key code from {event}")
            sequence[idx] = (key, direction)
        if action == "return":
            return sequence
        else:
            self.key_sequence = sequence
    
    @staticmethod
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
            if key in lexicon:
                key = lexicon.get(key, key)
            else:
                for k,v in pg.__dict__.items():
                    if str(v) == str(k):
                        key = k
                        break
            sequence[idx] = f"{key}{direction}"
        return sequence

    def play_game(self):
        self.game.playing = True
        self.game.start()
        if pg.display.get_init() is None:
            pg.display.init()
            pg.font.init()
        while self.game.snake.is_alive and self.game.crashed is False:
            # debug(f"self.game.game_state {self.game.game_state}")
            if isinstance(self.screenshot_path,str) and self.game.game_state is not None:
                self.screenshot()
            self.handle_keys()
            self.game.update()
            self.app_surface.fill(self.background)
            for wall in self.game.obstacles:
                pg.draw.rect(self.app_surface, self.obstacle_color, wall.render())
            if self.game.snake.is_alive:
                for fruit in self.game.rewards:
                    pg.draw.rect(self.app_surface, fruit.color, fruit.render())
            self.game.snake.draw(self.app_surface,None)
            # debug(f"rewards = {self.game.rewards}")
            # debug(f"snake = {self.game.snake.segments}")
            # debug(f"obstacles = {self.game.obstacles}")

            self.update()
            if self.game.snake.is_alive is False:
                info(f"GAME OVER")
                self.game.snake = None
                self.game.playing = False
                break

    def screenshot(self):
        # def compare_lists(list_a, list_b):
        #     result = True
        #     try:
        #         if isinstance(list_b,list) and isinstance(list_a,list):
        #             for idx,item in enumerate(list_b):
        #                 if isinstance(item,list):
        #                     result = compare_lists(list_a[idx], list_b[idx])
        #                 else:
        #                     result = (list_a[idx] == list_b[idx])
        #                 if result is False:
        #                     break
        #         else:
        #             result = (list_a == list_b)
        #     except Exception as err:
        #         result = False
        #         error(f"Gameboard.screenshot.compare_lists error: {err}")
        #     finally:
        #         return result
        # if self.latest_state != self.game.game_state:
        #     # if the state we last took a screenshot does not match the current state of the game
        #     self.latest_state = self.game.game_state

        current_state = copy.deepcopy(self.game.game_state)
        # create a copy of the current game state
        filename = f"screenshot-{self.screenshot_counter:0>7}.png"
        filename = os.path.join(self.screenshot_path,filename)
        if self.testing is False:
            debug(f"Next screenshot {filename}")
        pretty_state = lambda st: json.dumps(SnakeGame.label_state(st),indent=4,separators=(",",": "))
        if self.game.playing:
            if not SnakeGame.compare_states(self.latest_state, current_state):
                # if the state of the last screenshot taken does not
                # match the current state of the game
                debug(f"Saving {filename}")
                pg.image.save(self.app_surface, filename)
                # save a screenshot of the current game
                self.latest_state = copy.deepcopy(current_state)
                # hold onto the latest state of the game
                self.screenshot_counter += 1
            else:
                # if self.testing is False:
                #     debug(f"self.latest_state {pretty_state(self.latest_state)}")
                #     debug(f"current_state {pretty_state(current_state)}")
                #     debug(f"Can't save screenshot because no change detected")
                self.latest_state = copy.deepcopy(current_state)


    def update(self,frames=None):
        # debug(f"pg.display.get_init() {pg.display.get_init()}")
        try:
            if pg.display.get_init() is None:
                pg.display.init()
                pg.font.init()
            else:
                pg.display.flip()
                # Update the full display Surface to the screen
        except Exception as err:
            error(f"Gameboard.update error: {err}")
        finally:
            if frames is None:
                frames = self.frames
            self.game.clock.tick(frames)

    def draw_score(self):
        font_style = self.fonts.get("normal")
        font = pg.font.Font(font_style.get("family"), font_style.get("size"))
        msg = "Score: {}".format(self.score)
        if len(msg) > 0:
            text = font.render(msg, True, (0, 200, 0), self.background) 
            textBoundaries = text.get_rect()              
            textBoundaries.center = (self.width/2, self.height/4) 
            # debug(f"self.app_surface { {k:getattr(self.app_surface,k) for k in dir(self.app_surface) } }")
            # time.sleep(10)
            self.app_surface.blit(text, textBoundaries)

    def menu(self):
        debug(f"Gameboard.menu has begun")
        while True:
            debug(f"Gameboard.handle_keys")
            self.handle_keys()
            # debug(f"Game.update")
            self.game.update()
            # debug(f"Gameboard.app_surface.fill")
            self.app_surface.fill(self.background)
            # debug(f"Gameboard.draw_score")
            self.draw_score()
            # debug(f"Gameboard.update")
            self.update()
            if not (self.game.crashed is False and self.game.playing is False):
                break
        debug(f"Gameboard.menu has completed")

    def _init_gui(self):
        try:
            # debug(f"Gameboard._init_gui has begun {pg.font.get_init()} {pg.display.get_init()}")
            if not bool(pg.display.get_init()):
                # debug("pg.display.init()")
                pg.display.init()
            if not hasattr(self,"_loaded_icon"):
                try:
                    icon = pg.image.load(self.icon)
                    pg.display.set_icon(icon)
                except Exception as err:
                    error(f"Gameboard failed to set icon: {err}")
                self._loaded_icon = True
            if not bool(pg.font.get_init()):
                # debug("pg.font.init()")
                pg.font.init()
            if self.app_surface is None:
                # debug("self.app_surface init")
                self.app_surface = pg.display.set_mode((self.width, self.height))
            # if pg.get_init() is None:
            #     debug("pg.init()")
            #     pg.init()
            debug(f"pg.display.set_caption() {pg.display.get_init()} {pg.font.get_init()} {pg.display.get_init()}")
            pg.display.set_caption(self.title)
        except Exception as err:
            error(f"Gameboard._init_gui failed: {err}")
        finally:
            # debug(f"Gameboard._init_gui complete")
            pass

    def _start(self):
        try:
            debug(f"Gameboard._start has begun")
            self._init_gui()
            self.game.playing = False
            while self.game.crashed is False:
                self.menu()
                if self.game.playing:
                    debug(f"Gameboard switching states")
                    self.play_game()
                    debug(f"Gameboard done playing {self.game.playing}")
            pg.quit()
            return self.score
        except Exception as err:
            error(f"Gameboard._start has failed: {err}")
            raise err
        finally:
            pass
    def start(self):
        try:
            import threading
            debug(f"Creating Gameboard._start thread")
            t = threading.Thread(target=Gameboard._start,args=(self,))
            t.start()
        except Exception as err:
            error(f"Gameboard.start has failed: {err}")
            raise err
        finally:
            debug(f"Gameboard.start completed")


    @property
    def frames(self):
        return self.game.frames

    @property
    def height(self):
        return self.game.height

    @property
    def width(self):
        return self.game.width

    @property
    def score(self):
        return self.game.score