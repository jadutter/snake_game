import shlex
import logging
import logging.config
import os
from yaml import safe_load as yaml_safe_load
from yaml import YAMLError
from auxillary import dir_path

try:
    # open the yaml file
    with open(os.path.join(
            os.path.dirname(__file__),
            "logging_config.yml"), "r") as f:
        cfg = yaml_safe_load(f)
        # and parse the yaml data into a python dict
    log_folder = cfg.pop("log_folder")
    # get the directory where we want the log files to reside
    if not dir_path(log_folder, suppress=True):
        # if the directory does not exist
        os.mkdir(log_folder)
        # make the directory
    for name,hdlr in cfg.get("handlers").items():
        # for each handler in the config
        if "filename" in hdlr:
            # if the handler has a filename attribute
            cfg["handlers"][name]["filename"] = os.path.join(log_folder, hdlr.get("filename"))
            # set the file to reside in the log directory we want to use
    logging.config.dictConfig(cfg)
    # use the dict to configure the most of the logging setup
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
    # try:
    #     info_handlers = [ hdl for hdl in logr.handlers 
    #         if hasattr(hdl,"stream") and 
    #             hasattr(hdl,"level") and 
    #             int(hdl.level) <= 20 ]
    #     if len(info_handlers) > 0:
    #         progress_bars = [ ProgressBar(h.stream) for h in info_handlers if h.stream.name == "<stdout>"]
    # except Exception as err:
    #     debug("Failed to create progress bars:{}".format(err))

    assert debug == getattr(logr,"debug"), "Something went wrong with getting logging functions..."
    # the logger method called "debug", should now be the same as our function debug()

    from auxillary import *
    from parsing import *
    from gui.gameboard import Gameboard
    from interfaces.game import SnakeGame
except YAMLError as err:
    logging.critical("Failed to read yaml file.")
    logging.exception(err)
    # print the message to the root logger
    raise err
except Exception as err:
    logging.critical("Failed to configure logging.")
    logging.exception(err)
    # print the message to the root logger
    raise err
finally:
    del cfg
    del f
    del yaml_safe_load
    del YAMLError

def computer_game(*args,**kwargs):
    """
    Start a game of Snake for a computer to play.
    """
    data = {
        "height": 160,
        "width": 160,
        "size": 10,
        "snake_speed": 10,
        "auto_tick": False,
        "frames": 10,
        "testing": False,
    }
    game = SnakeGame(**data)
    data = {
        "screenshot_path": None,
    }
    board = Gameboard(game, **data)
    board.start()
    debug("Finished starting")
    return 

def human_game(*args,**kwargs):
    """
    Start a game of Snake for a human to play.
    """
    data = {
        "height": 320,
        "width": 320,
        "size": 10,
        "snake_speed": 8,
        "auto_tick": True,
        "frames": 60,
        "testing": False,
    }
    # data = {
    #     "height": 320,
    #     "width": 320,
    #     "size": 10,
    #     "snake_speed": 10,
    #     "auto_tick": False,
    #     "frames": 8,
    #     "testing": False,
    # }
    # data = {
    #     "height": 320,
    #     "width": 320,
    #     "size": 10,
    #     "snake_speed": 8,
    #     "auto_tick": False,
    #     "frames": 8,
    #     "testing": False,
    # }
    game = SnakeGame(**data)
    data = {
        "screenshot_path": None,
    }
    board = Gameboard(game, **data)
    board.start()
    debug("Finished starting")
    return 

# def main(*args):
#     """
#     Start a game of Snake for a human or AI to start playing.
#     """
#     sg = startup.SnakeGameArgumentParser()
#     if args:
#         app = sg.parse_args(args=args)
#     else:
#         app = sg.parse_args()
#     if app is None:
#         return 
#     # human_game()
#     computer_game()
#     # run_tests()



def start_play(app):
    gui_data = {
        "screenshot_path": None,
    }
    # game_data = {
    #     "player_name": app.player_name,
    #     "height": app.height,
    #     "width": app.width,
    #     "size": app.size,
    #     "snake_speed": app.snake_speed,
    #     "auto_tick": app.auto_tick,
    #     "frames": app.frames,
    #     "testing": app.testing,
    # }
    if app.mode == "human":
        game_data = {
            "player_name": "JAD",
            "height": 320,
            "width": 320,
            "size": 10,
            "snake_speed": 10,
            "auto_tick": True,
            "frames": 60,
            "testing": False,
        }
        # game_data = {
        #     "height": 320,
        #     "width": 320,
        #     "size": 10,
        #     "snake_speed": 10,
        #     "auto_tick": False,
        #     "frames": 8,
        #     "testing": False,
        # }
        # game_data = {
        #     "height": 320,
        #     "width": 320,
        #     "size": 10,
        #     "snake_speed": 8,
        #     "auto_tick": False,
        #     "frames": 8,
        #     "testing": False,
        # }
    elif app.mode == "computer":
        game_data = {
            "player_name": "Derik Q Newton",
            "height": 160,
            "width": 160,
            "size": 10,
            "snake_speed": 10,
            "auto_tick": False,
            "frames": 10,
            "testing": False,
        }
    else:
        return
    game = SnakeGame(**game_data)
    board = Gameboard(game, **gui_data)
    board.start()

def main(*args):
    """
    Start a game of Snake for a human or AI to start playing.
    """
    parser = mainParser.MainArgumentParser()
    if args and len(args) ==1:
        args = shlex.split(args[0])
    if args:
        app, args = parser.parse_known_args(args=args)
    else:
        app, args = parser.parse_known_args()
    if not app:
        return 
    debug(app)
    if not hasattr(app, "action") or app.action == "play":
        start_play(app)
    elif app.action == "test":
        results = app._test_parser.run_tests(app)
        info(results)
    else:
        return


if __name__ == '__main__':
    # main("screenshot")
    main("play human -pn 'JAD'")
    # main("test --verbose -tcs objects.TestObstacleObject -tmt objects.TestSnakeObject.test_self_intersection")
    # main("test --verbose -tcs interfaces.TestScribe")


# *** TODO LIST ***
# change game to maintain sql connection until its game over
# change GET_UUID

# Setup game board to be able to render and play slices of a recorded game state
# Setup game to be able to log state to a database
# create a method(s) so that a series of states can be given, and the game will save the screenshots
# Write DQN to read current state and send commands
# Setup menu to be able to change settings:
#     size
#     speed
#     who plays
# Clean up unused pieces of code ( specifically so that the main game is single threaded )
# Clean up logging and error catching
# set exe icon
# create win condition and winning screen
# set restart to start the game again from the beginning instead of resuming the current game
# create easy, meduim, hard default settings
# setup game to convert images into video (timestamped) on game over
# fix screenshots to be saved as a single gif while playing

# *** RESEARCH TOPICS ***
# # hamiltonian loops
# # A* search algorithm



# *** TESTS ***
# Get AI to play a perfect game
# Get AI to train on different games with different fruits, and still play a perfect game

