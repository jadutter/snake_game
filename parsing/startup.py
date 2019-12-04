#!/usr/bin/python3.7
import argparse
from auxillary import *
# from parsing.mode import GameModeArgumentParser
from yaml import safe_load as yaml_safe_load
from yaml import YAMLError

try:
    # open the yaml file
    with open(os.path.join(
            os.path.dirname(__file__),
            "../logging_config.yml"), "r") as f:
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
    logr = logging.getLogger("Parsing")
    # get a logger

    log = logr.log
    crit = logr.critical
    error = logr.error
    warn = logr.warning
    info = logr.info
    debug = logr.debug
    # take the logger methods that record messages and 
    # convert them into simple one word functions
    # debug("START")
    # debug(debug)
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

class SnakeGameArgumentParser(argparse.ArgumentParser):
    """
    Initialize a game of snake with the following arguments.
    """
    select_options = AliasDict.fromkeys(
            ["player","p","human","h"], "player",
            ["ai","computer","c","dqn","q"], "computer",
        )
    def __init__(self, 
            prog="SnakeGame",
            description="Initialize a game of snake with the following arguments.",
            *arg, 
            **kwargs):
        metavar_set = (lambda var: "{"+", ".join(sorted([i for i in var]))+"}")    
        super(SnakeGameArgumentParser, self).__init__(prog=prog,*arg, **kwargs)
        meta_args = self.add_argument_group(
                            title="META",
                            description="""Arguments to modify how this script runs.""")
        aux_args = self.add_argument_group(
                            title="AUX",
                            description="""Auxillary functions to perform before the main command.""")
        game_args = self.add_argument_group(
                            title="GAME",
                            description="""Arguments to modify the game.""")

        vb_args = meta_args.add_mutually_exclusive_group()
        _vb_args = vb_args.add_argument_group()
        _vb_args.add_argument("--verbosity","-vb",
                            type=int,
                            default=20,
                            # by default, show logging.INFO level and up.
                            help="How verbose the logs should be.")
        _vb_args.add_argument("--verbose", "-v",
                            action="store_true",
                            help="Set the verbosity to be as explicit as possible.")
        vb_args.add_argument("--quiet", "-q",
                            action="store_true",
                            help="Set the verbosity to not print anything.")
        aux_args.add_argument("--clear_logs", "-cl",
                            action="store_true",
                            help="Clear the log files before beginning.")

        game_args.add_argument("mode", 
                            type=str,
                            metavar="MODE {}".format(metavar_set(["computer","human"])),
                            help="Select who will be playing this game.\n{}".format("KEYWORDS={}".format(metavar_set(self.select_options.keys()))))
        game_args.add_argument("--size", "-sz",
                            type=int,
                            default=10,
                            help="How many pixels a virtual pixel uses (determines snake and fruit width).")
        game_args.add_argument("--speed", "-sp",
                            type=int,
                            default=10,
                            help="How fast the snake must move.")
        game_args.add_argument("--width", "-w",
                            type=int,
                            default=64,
                            help="The height and width of the game in virtual pixels.")
        # cmd_subparsers = self.add_subparsers(
                    #         # prog="mode",
                    #         parser_class=GameModeArgumentParser,
        #                     # title="COMMANDS",
        #                     # dest="cmd", 
        #                     # description="Valid operations to perform.",
        #                     # help="Valid command options.",
        #                     )
        # # parser_a = cmd_subparsers.add_parser("select_mode",
        # #                     description="Select who will be playing this game.",
        # #                     help="Select who will be playing this game.",
        # #                     )
        # parser_b = cmd_subparsers.add_parser("mode",
        #                   prog="mode",
        #                   # dest="mode",
        #                     metavar=["player","ai"],
        #                     description="Select who will be playing this game.",
        #                     help="Select who will be playing this game.",)

    def parse_args(self, args=None, namespace=None):
        """
        Parse and validate args.
        """
        global crit, error, warn, info, debug, log
        # bring in the global variables containing the logger's methods
        def _export_namespace_dict(func):
            def _get_locals():
                try:
                    locals_result = {}
                    frame = inspect.currentframe()
                    frame = frame.f_back
                    # from _get_locals() to _export_namespace_dict()
                    frame = frame.f_back
                    # from _export_namespace_dict() to __wrap_log_fnc()
                    frame = frame.f_back
                    # from __wrap_log_fnc() to the function where crit or error was actually called.
                    locals_result = frame.f_locals
                finally:
                    del frame
                    return locals_result
            def __wrapped_fnc(*args,**kwargs):
                # print("__wrapped_fnc:{}".format(func))
                # print("__wrapped_fnc:{}".format(kwargs))
                foo = None
                if "extra" not in kwargs:
                    kwargs["extra"] = {}
                locals_result = {}
                globals_result = {}
                try:
                    frame = inspect.currentframe()
                    # frame = frame.f_back
                    # from __wrapped_fnc() to _export_namespace_dict()
                    frame = frame.f_back
                    # from _export_namespace_dict() to __wrap_log_fnc()
                    frame = frame.f_back
                    # from __wrap_log_fnc() to the function where crit or error was actually called.
                    locals_result = frame.f_locals
                    globals_result = frame.f_globals
                except Exception as err:
                    debug("Failed to grab locals and globals:{}".format(str(err)))
                finally:
                    del frame
                kwargs["extra"]["locals"] = locals_result
                kwargs["extra"]["globals"] = globals_result
                # print("__wrapped_fnc:{}".format(kwargs))
                return func(*args,**kwargs)
            return __wrapped_fnc
        def _wrap_log_fnc(func,lvl,n_args=1):
            """
            Accept a log event emitting function,
            and set it to not do anything if it's
            verbosity is not met in the current namespace.
            """
            # print("Wrapping {}\n\t{}".format(func,trace_fnc_path()))
            def __wrap_log_fnc(*args,**kwargs):
                """
                Accept args and kwargs, do a little preprocessing,
                and determine if its allowed to be passed to the 
                logger method. 
                """
                # print(namespace.verbosity, args[0])
                if (namespace.verbosity <= lvl and n_args == 1) or (n_args > 1 and namespace.verbosity <= args[0]):
                    if args and len(args) > 0:
                        if(n_args<1):
                            # if the wrapped method accepts no arg
                            # shouldn't happen
                            return func(**kwargs)
                        if(n_args==1):
                            # if the wrapped method only accepts 1 arg
                            return func(stringify(args),**kwargs)
                        else:
                            # print(namespace.verbosity, lvl, n_args, args[0])
                            # if the wrapped method accepts many arg
                            first_set = args[0:n_args-1]
                            second_set = args[n_args-1:]
                            # print("Logger.log was explicitly called")
                            args = tuple([a for a in first_set]+[stringify(second_set)])
                            if len(args) == 1:
                                args = args[0]
                            return func(*args,**kwargs)
                    else:
                        return func(*args,**kwargs)
                else:
                    return
            return __wrap_log_fnc
        if namespace == None:
            if args is not None and len(args) > 0:
                namespace = super(SnakeGameArgumentParser, self).parse_args(args=args)
            else:
                namespace = super(SnakeGameArgumentParser, self).parse_args()
        # doing everything the ArgumentParser class would do,
        # and get the namespace it returns
        if namespace.verbose:
            # if logging everything,
            namespace.verbosity = 1
            # set verbosity/logging level to 1
        if not namespace.verbosity:
            # if no verbosity is set yet,
            namespace.verbosity = 60
            # set it to be quiet
        logr.setLevel(namespace.verbosity)
        # set logging level
        if crit == getattr(logr,"critical"):
            # if we haven't wrapped the functions yet
            crit  = _export_namespace_dict(crit)
            error = _export_namespace_dict(error)
            # setup error and crit to automatically grab locals and globals from the stack they're called in
            crit  = _wrap_log_fnc(crit, 50)
            error = _wrap_log_fnc(error,40)
            warn  = _wrap_log_fnc(warn, 30)
            info  = _wrap_log_fnc(info, 20)
            debug = _wrap_log_fnc(debug,10)
            log = _wrap_log_fnc(log, 0, n_args=2)
            # crit is now _wrap_log_fnc() with the the 
            # Logger method "critical" called inside it.
        try:
            # write any special checks or attributes needed for namespace
            pass
        except Exception as err:
            crit("Failed to setup namespace.", extra={ "err": err, "tb": get_tb()})
            namespace = None
        return namespace

