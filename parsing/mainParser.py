#!/usr/bin/python3.7
import argparse
import logging
from auxillary import *
from parsing.startup import SnakeGameArgumentParser
from parsing.testing import TestingArgumentParser

try:
    logr = logging.getLogger("Parser")
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
    logging.critical("Failed to configure logging for Parser.")
    logging.exception(err)
    # print the message to the root logger
    raise err


class MainArgumentParser(argparse.ArgumentParser):
    """
    Parse arguments and decide which function this project should perform.
    """
    def __init__(self, 
            prog="SnakeDQN",
            description="Decide which function this project should perform.",
            *arg, 
            **kwargs):
        super(MainArgumentParser, self).__init__(prog=prog,*arg, **kwargs)

        vb_args = self.add_mutually_exclusive_group()
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
        self.add_argument("action",
                            type=str,
                            choices=["play", "test", "screenshot"],
                            help="Available actions to perform.")

        # subparsers = self.add_subparsers(
        #                     parser_class=SnakeGameArgumentParser,
        #                     help='Available actions to perform',
        #                     )
        # subparsers.add_parser("play",
        #                     parser_class=SnakeGameArgumentParser,
        #                     help="Play one or more games of snake.")
        # subparsers.add_parser("test",
        #                     parser_class=TestingArgumentParser,
        #                     help="Test one or more modules, cases, or methods.") 

    def parse_known_args(self, args=None, namespace=None):
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
        if args is not None and len(args) > 0:
            namespace, args = super(MainArgumentParser, self).parse_known_args(args=args)
        else:
            namespace, args = super(MainArgumentParser, self).parse_known_args()
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
            if namespace.action == "play":
                parser = SnakeGameArgumentParser()
            elif namespace.action == "test":
                parser = TestingArgumentParser()
                namespace._test_parser = parser
            else:
                raise argparse.ArgumentError("action", "invalid action: please choose one of the listed keywords.")
            if args:
                namespace, args = parser.parse_known_args(args=args,namespace=namespace)
                # namespace = parser.parse_args(args=args)
            else:
                namespace, args = parser.parse_known_args(namespace=namespace)
                # namespace = parser.parse_args()

        except Exception as err:
            crit("Failed to setup namespace.", extra={ "err": err, "tb": get_tb()})
            namespace = None
        return namespace, args

