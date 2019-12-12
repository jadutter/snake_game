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
    # test_modules = ["interfaces"]
    # test_modules = ["objects"]
    # test_modules = ["gui","interfaces"]
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
        "height": 320,
        "width": 320,
        "size": 10,
        "snake_speed": 10,
        "auto_tick": True,
        "frames": 60,
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
# fix the frequency at which fruit spawn
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
# determine what will set the score, and how it is tracked overtime
# set exe icon
# create win condition and winning screen
# set restart to start the game again from the beginning instead of resuming the current game
# create easy, meduim, hard default settings
# setup game to convert images into video (timestamped) on game over


# *** RESEARCH TOPICS ***
# # hamiltonian loops
# # A* search algorithm



# *** TESTS ***
# Get AI to play a perfect game
# Get AI to train on different games with different fruits, and still play a perfect game

