#!/usr/bin/python3.7
import argparse
import logging
import unittest
from auxillary import *

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

class TestingArgumentParser(argparse.ArgumentParser):
    """
    Parse arguments to determine which tests to run.
    """
    _test_modules = [
            "gui", 
            "interfaces", 
            "objects", 
            "parsing",
        ]
    _test_cases = {}
    _test_methods = {}
    for mod in _test_modules:
        md = __import__(mod)
        _test_cases[mod] = []
        for case in dir(md):
            cs = getattr(md, case)
            if isinstance(cs,unittest.TestCase):
                _test_cases[mod] += [case]
                mod_case = "{}.{}".format(mod,case)
                _test_methods[mod_case] = []
                for met in dir(cs):
                    if met.find("test_") == 0:
                        _test_methods[mod_case] += [met]

    def __init__(self, 
            prog="tester",
            description="Determine which tests to run.",
            *arg, 
            **kwargs):
        super(TestingArgumentParser, self).__init__(prog=prog,*arg, **kwargs)

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

        test_modules = ["all"] + self._test_modules
        logging.debug(self._test_cases)
        # test_cases = [
        #     "{}.{}".format(mod,case) 
        #     for mod,case_list in self._test_cases 
        #     for case in case_list
        #     ]
        # test_methods = [
        #     "{}.{}".format(mod_case,met) 
        #     for mod_case,met_list in self._test_methods 
        #     for met in met_list
        #     ]
        self.add_argument("--test_module", "-tmd",
                            dest="modules",
                            nargs="+",
                            action="append",
                            # choices=test_modules,
                            # choices=[],
                            # default=[],
                            help="Select a module to run unittests on")
        self.add_argument("--test_case", "-tcs",
                            dest="cases",
                            nargs="+",
                            action="append",
                            # choices=test_cases,
                            # choices=[],
                            # default=[],
                            help="Select specific TestCases to test.")
        self.add_argument("--test_method", "-tmt",
                            dest="methods",
                            nargs="+",
                            action="append",
                            # choices=test_methods,
                            # choices=[],
                            # default=[],
                            help="Select specific methods to test.")


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
            namespace, args = super(TestingArgumentParser, self).parse_known_args(args=args,namespace=namespace)
        else:
            namespace, args = super(TestingArgumentParser, self).parse_known_args(namespace=namespace)
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
            has_tests = False
            if namespace.modules is None:
                namespace.modules = []
            elif isinstance(namespace.modules[0], list):
                namespace.modules = [i for item_list in namespace.modules for i in item_list]
            if namespace.cases is None:
                namespace.cases = []
            elif isinstance(namespace.cases[0], list):
                namespace.cases = [i for item_list in namespace.cases for i in item_list]
            if namespace.methods is None:
                namespace.methods = []
            elif isinstance(namespace.methods[0], list):
                namespace.methods = [i for item_list in namespace.methods for i in item_list]

            if len(namespace.modules) > 0: 
                has_tests = True
            elif len(namespace.cases) > 0: 
                has_tests = True
            elif len(namespace.methods) > 0: 
                has_tests = True
            if has_tests == False:
                namespace.modules = self._test_modules
            # debug("namespace.modules:{}".format(namespace.modules))
            # debug("namespace.cases:{}".format(namespace.cases))
            # debug("namespace.methods:{}".format(namespace.methods))
            # if all([
            #     (tests is None or len(tests) == 0)
            #     for tests in [
            #         namespace.modules, 
            #         namespace.cases, 
            #         namespace.methods
            #     ]]):
            #     # if no arguments are given for anything specific to use, 
            #     namespace.modules = ["all"]
            #     # then we'll be testing everything
        except Exception as err:
            logging.exception(err)
            crit("Failed to setup namespace.", extra={ "err": err, "tb": sys.exc_info()[2]})
            namespace = None
            raise err
        return namespace, args
    @property
    def loader(self):
        if not hasattr(self,"_loader"):
            self._loader = unittest.TestLoader()
        return self._loader

    @property
    def suites(self):
        if not hasattr(self,"_suites"):
            self._suites = []
        return self._suites
    
    @suites.setter
    def suites(self, value):
        self._suites = value
    
    def load_modules(self, app, suite):
        """
        Load unittests for all the specified modules
        """
        suites = []
        modules = []
        if "all" in app.modules:
            modules = self._test_modules
        else:
            modules = [mod for mod in app.modules if mod in self._test_modules]
        for mod_name in modules:
            mod = __import__(mod_name)
            suites.append(self.loader.loadTestsFromModule(mod))
        suite.addTests(unittest.TestSuite(suites))

    def load_cases(self, app, suite):
        """
        Load unittests for all the specified cases
        """
        suites = []
        # cases = [case for mod,case_list in app.cases.items() for case in case_list]
        # cases = [(case.split(".")[0],case.split(".")[-1]) for case in app.cases]
        for mod_case in app.cases:
            mod_name, case_name = mod_case.split(".")
            md = __import__(mod_name)
            cs = getattr(md, case_name)
            suites.append(self.loader.loadTestsFromTestCase(cs))
        suite.addTests(unittest.TestSuite(suites))

    def load_methods(self, app, suite):
        """
        Load unittests for all the specified methods
        """
        suites = []
        # methods = [method for mod_case,method_list in app.methods.items() for method in method_list]
        # methods = [method.split(".")[-1] for method in app.methods]
        for method in app.methods:
            mod_name, case_name, met_name = method.split(".")
            md = __import__(mod_name)
            cs = getattr(md, case_name)
            suites.append(self.loader.loadTestsFromName(met_name, module=cs))
        suite.addTests(unittest.TestSuite(suites))

    def run_tests(self, app):
        suite = unittest.TestSuite()
        self.load_modules(app, suite)
        if "all" not in app.modules:
            self.load_cases(app, suite)
            self.load_methods(app, suite)
        if app.verbosity <= logging.DEBUG:
            verbosity = 2
        elif app.verbosity <= logging.INFO:
            verbosity = 1
        else:
            verbosity = 0
        runner = unittest.TextTestRunner(verbosity=verbosity)
        testResult = runner.run(suite)
        return testResult

    # @staticmethod
    # def get_test_cases(mod):
    #     md = __import__(mod)
    #     return [
    #         "{}.{}".format(mod, item) 
    #         for item in dir(mod)
    #         if isinstance(getattr(md,item), unittest.TestCase)
    #     ]
        
    # @staticmethod
    # def get_test_methods(mod,case):
    #     md = __import__(mod)
    #     cs = getattr(md,case)
    #     return [
    #         "{}.{}.{}".format(mod, case, item) 
    #         for item in dir(cs)
    #         if (item.find("test_") == 0)
    #     ]


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WidgetTestCase('test_default_widget_size'))
    suite.addTest(WidgetTestCase('test_widget_resize'))
    return suite
