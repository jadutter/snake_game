from parsing import *
from auxillary import *
from objects import *
from yaml import safe_load as yaml_safe_load
from yaml import YAMLError
from gui.gameboard import Gameboard
from interfaces.game import SnakeGame

try:
    # open the yaml file
    with open(os.path.join(
            os.path.dirname(__file__),
            "logging_config.yml"), "r") as f:
        cfg = yaml_safe_load(f)
        # and parse the yaml data into a python dict
    log_folder = cfg.pop("log_folder")
    # get the directory where we want the log files to reside
    if not os.path.isdir(log_folder):
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
    try:
        info_handlers = [ hdl for hdl in logr.handlers 
            if hasattr(hdl,"stream") and 
                hasattr(hdl,"level") and 
                int(hdl.level) <= 20 ]
        if len(info_handlers) > 0:
            progress_bars = [ ProgressBar(h.stream) for h in info_handlers if h.stream.name == "<stdout>"]
    except Exception as err:
        debug("Failed to create progress bars:{}".format(str(err)))
    assert debug == getattr(logr,"debug"), "Something went wrong with getting logging functions..."
    # the logger method called "debug", should now be the same as our function debug()
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

def test_locking():
    import multiprocessing
    testLock = multiprocessing.RLock()
    debug(testLock)
    debug(dir(testLock))
    debug(dir(testLock._semlock))
    # debug(dir(multiprocessing.RLock))
    # debug(testLock._semlock._count())
    debug(testLock._semlock._get_value())
    debug(testLock._semlock._is_mine())
    testLock.acquire()
    # debug(testLock._semlock._count())
    debug(testLock._semlock._get_value())
    debug(testLock._semlock._is_mine())
    testLock.release()
    debug(testLock._semlock._get_value())
    debug(testLock._semlock._is_mine())
    # debug(testLock._rand)
    debug(testLock)

def run_tests(*args,**kwargs):
    import unittest
    # test_locking()
    test_modules = ["objects", "interfaces", "gui", "parsing"]
    # test_modules = ["gui"]
    suites = []
    loader = unittest.TestLoader()
    for mod_name in test_modules:
        mod = __import__(mod_name)
        suites.append(loader.loadTestsFromModule(mod))
    suite = unittest.TestSuite(suites)
    # testResult = unittest.TextTestRunner(verbosity=2).run(suite)
    testResult = unittest.TextTestRunner().run(suite)

def computer_game(*args,**kwargs):
    """
    Start a game of Snake for a computer to play.
    """
    return 

def human_game(*args,**kwargs):
    """
    Start a game of Snake for a human to play.
    """
    data = {
        "height": 80,
        "width": 80,
        "size": 10,
        "snake_speed": 10,
        "auto_tick": True,
        "frames": 60,
    }
    game = SnakeGame(**data)
    board = Gameboard(game)
    board.start()
    debug("Finished starting")
    return 

def main(*args):
    """
    Start a game of Snake for a human or AI to start playing.
    """
    sg = startup.SnakeGameArgumentParser()
    if args:
        app = sg.parse_args(args=args)
    else:
        app = sg.parse_args()
    if app is None:
        return 
    human_game()
    # run_tests()


if __name__ == '__main__':
    main("human")


# *** TODO LIST ***
# Write DQN to read current state and send commands
# Setup game to be able to log state to a database
# Setup game board to be able to render and play slices of a recorded game state
# Change game to not spawn snake close to and pointed at a wall
# Setup menu to be able to change settings:
#     size
#     speed
#     who plays
# Clean up unused pieces of code ( specifically so that the main game is single threaded )
# Clean up logging and error catching
# determine what will set the score, and how it is tracked overtime
# set exe icon
# create win condition and winning screen
# fix intersection detection when Snake has no segments
# set restart to start the game again from the beginning instead of resuming the current game
# fix the frequency at which fruit spawn
# create easy, meduim, hard default settings
# set font sizes to be dependent on screen sizes
# fix error logging 
# """2019-12-11 16:13:52,805 - root         - ERROR    - cannot import name '__file__' from '__main__' (unknown location)
# Traceback (most recent call last):
#   File "G:\Home\Code\game_3\auxillary.py", line 135, in trace_fnc_path
#     from __main__ import __file__ as main_file;
# ImportError: cannot import name '__file__' from '__main__' (unknown location)
# 2019-12-11 16:13:52,820 - root         - ERROR    - cannot import name '__file__' from '__main__' (unknown location)
# Traceback (most recent call last):
#   File "G:\Home\Code\game_3\auxillary.py", line 135, in trace_fnc_path
#     from __main__ import __file__ as main_file;
# ImportError: cannot import name '__file__' from '__main__' (unknown location)"""

# *** RESEARCH TOPICS ***
# # hamiltonian loops
# # A* search algorithm



# *** TESTS ***
# Get AI to play a perfect game
# Get AI to train on different games with different fruits, and still play a perfect game

