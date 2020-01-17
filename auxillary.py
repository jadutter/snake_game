#!/usr/bin/python2.7
__doc__ = """
A place to put shared auxillary functions.
"""

import argparse
import datetime
import hashlib
import inspect
import itertools
import json
import logging
import logging.config
import logging.handlers
import math
import os
import re
import requests
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from yaml import safe_load as yaml_safe_load
from yaml import YAMLError

aux_log = logging.log
aux_crit = logging.critical
aux_error = logging.error
aux_warn = logging.warning
aux_info = logging.info
aux_debug = logging.debug

def thread_name():
    """Return the name of the current thread that calls this function"""
    return threading.current_thread().name

def sep_digits(val, interval=3, sep=","):
    """
    Convert a string containing a multi digit number into a more legible format; 
    default: every three digits, separate by a comma.
    """
    new_val = None
    if isinstance(val,str):
        new_val = ""
    elif isinstance(val,int):
        new_val = ""
        val = str(val)
    if new_val != None and re.search(r"^\d+$",val.strip()) != None:
        for i,digit in enumerate("".join(list(reversed(val.strip())))):
            if i%interval==0 and i != 0:
                new_val = sep + new_val
            new_val = digit + new_val
        val = new_val
    return val

def indent (s,i,c=" "):
    """
    Quick function to be able to change the    indentation level
    of a multiline string; such as for a log file
    """
    if isinstance(s,str) or isinstance(s,unicode) or isinstance(s,basestring):
        result = s
    else: 
        result = str(s)
    try:
        result = "\n".join(["{}{}".format(c*i,line) for line in result.split("\n") if line is not ""])
    except Exception as err:
        logging.exception(err)
        aux_warn("Failed to indent string:'{}'".format(s), extra = { "err": err, "tb": sys.exc_info()[2] } )
    finally:
        return result

def format_trace(t, i_incr, start=0, i_chr=" "):
    """
    Add extra indentation to a multiline string of a traceback.
    """
    result = t
    try:
        result = [line.strip() for line in result.split("\n") if line.strip() != ""]
        levels = 0
        for idx,line in enumerate(t):
            if line.find("File ") != 0:
                result[idx] = i_chr*start+indent(line,i_incr*(levels+1),c=i_chr)
            else:
                result[idx] = i_chr*start+indent(line,i_incr*levels,c=i_chr)
                levels += 1
        result = "\n".join(result)
    except Exception as err:
        logging.exception(err)
        aux_warn("Failed to format traceback string:'{}'".format(s), extra = { "err": err, "tb": sys.exc_info()[2] } )
    finally:
        return result

def filter_sort(val,cond):
    """
    Given an iterator and a condition (lambda function), 
    return an iterator where all are true, 
    and return an iterator where all are false.
    """
    if isinstance(val,dict):
        getter = "items"
    else:
        getter = "__iter__"
    a, b = list(), list()
    for v in getattr(val,getter)():
        if cond(v):
            a+=[v]
        else:
            b+=[v]
    return val.__class__(a), val.__class__(b)
# def show_callers_locals():
#     """Print the local variables in the caller's frame."""
#     frame = inspect.currentframe()
#     try:
#         result = {}
#         frame = frame.f_back
#         result = frame.f_locals
#     finally:
#         del frame
#         return result

def trace_call_path(skip=0, truncate=0, deep=None, shallow=None, delimiter=None):
    """
    When called, trace the series of functions that were called to get it.
    deep     = the name of the deepest function we'll want to exclude from using.
                don't use functions below this one.
    shallow  = the name of the shallowest function we'll want to exclude from using; 
                don't use functions above this one.
    skip     = how many deepest levels it should not bother using;
                applied after deep and shallow keyword arguments, if they're used.
    truncate = how many shallowest levels it should not bother using;
                applied after deep and shallow keyword arguments, if they're used.
    For sanity, it's recommended that you use (skip, truncate) or (deep,shallow).
    Good luck if you try using all three at once
    """
    if delimiter is None:
        delimiter = ":"
    elif not isinstance(delimiter,str):
        raise TypeError("Expected str for keyword argument delimiter, not {}".format(type(delimiter)))
    elif len(delimiter) != 0:
        raise ValueError("Expected a str containing a single character for keyword argument delimiter, not '{}'".format(delimiter))
    if shallow is not None and not isinstance(shallow,str):
        raise TypeError("Expected str for keyword argument shallow, not {}".format(type(shallow)))
    if deep is not None and not isinstance(deep,str):
        raise TypeError("Expected str for keyword argument deep, not {}".format(type(deep)))
    if not isinstance(skip,int):
        raise TypeError("Expected int for keyword argument skip, not {}".format(type(skip)))
    if not isinstance(truncate,int):
        raise TypeError("Expected int for keyword argument truncate, not {}".format(type(truncate)))
    curframe = inspect.currentframe()
    # the frame for trace_call_path 
    calframes = inspect.getouterframes(curframe, 2)
    # list of frames for what called the current frame
    call_path = [ item[3] for item in calframes if item[3] != inspect.getframeinfo(curframe)[2] ]
    call_path = list(reversed(call_path))
    call_path = [ ( __file__.split(os.sep)[-1][:-3] if item == "<module>" else item) for item in call_path ]
    # call_path is a list of names, where the first element is the name of the file, 
    # and the rest are the names of the functions called
    if shallow is not None or deep is not None:
        # if we want to exlude by name
        for idx,name in enumerate(call_path):
            # search for the index of the name
            if name == shallow:
                shallow = idx
            if name == deep:
                deep = idx
    if isinstance(shallow, int):
        # if we've got an index
        call_path = call_path[shallow+1:]
    if isinstance(deep, int):
        # if we've got an index
        call_path = call_path[0:deep]
    if skip > 0:
        if len(call_path) > skip:
            # if the list is longer than the number of elements we want to remove
            call_path = call_path[0:-skip]
        else:
            call_path = []
    if truncate > 0:
        if len(call_path) > truncate:
            # if the list is longer than the number of elements we want to remove
            call_path = call_path[truncate:]
        else:
            call_path = []
    return delimiter.join(call_path)


def get_tb():
    """
    Use this function when you want a traceback
    of an exception that has just occurred.
    """ 
    result = ""
    try:
        result = sys.exc_info()[2]
        if not result:
            result = "Failed to get tb"
    except Exception as err:
        logging.exception(err)
    finally:
        return result

def stringify(v):
    """
    Accept a set of arguments, and transform 
    them info a single string.
    """
    if isinstance(v,str):
        pass
    elif isinstance(v,list):
        v = str(v)
    elif isinstance(v,tuple):
        if len(v) == 1:
            v = stringify(v[0])
        else:
            v = str("({})".format(",".join([stringify(x) for x in v])))
    elif isinstance(v,list):
        v = str("[{}]".format(",".join([stringify(x) for x in v])))
    elif isinstance(v,itertools.imap):
        v = str("[{}]".format(",".join([stringify(x) for x in v])))
    elif isinstance(v,Exception):
        # if the arg is an Exception, 
        v = stringify(str(v))
    else:
        # if its anything else exotic,
        # try to turn it into a string
        v = str(v)
    return v

class AliasDict(dict):
    """
    Expand the standard dictionary so that
    many keys can map to the same values.
    """
    def __init__(self, *args, **kwargs):
        super(AliasDict, self).__init__(*args,**kwargs)
        # print("AliasDict.__init__ for {}".format(id(self)))
        # self._test_all()
    def __del__(self, *args, **kwargs):
        super(AliasDict, self).__init__(*args,**kwargs)
        # print("AliasDict.__del__ for {}".format(id(self)))
    def values(self, *args, **kwargs):
        """
        Return all values, without duplicates.
        """
        return list(set(super(AliasDict, self).values(*args,**kwargs)))
    @property
    def inverted(self):
        """
        Swap the keys and values; every value that was, 
        is now a key containing a list of everything that was its key.
        Note: this is roughly ten times slower than the items method, 
        so it may be worth calling once and storing the dict for later.
        """
        used_values = []
        # a list containing all values already yielded
        temp = dict.copy(self)
        for key,val in self.items():
            # for each pair,
            if val not in used_values:
                # if the val was not yielded yet
                key_list = []
                used_values += [val]
                for k,v in temp.items():
                    if v == val:
                        key_list += [k]
                        temp.pop(k)
                yield (val, key_list)
                # yield a tuple containing the val in the key position, 
                # and a list containing all keys that mapped to val 
    def get_inverted(self):
        return {k:v for (k,v) in self.inverted}
    # def _test(self):
    #     # correct_type = all([ 
    #     #                     isinstance(v, (list, tuple, set))
    #     #                     for k,v in self.items()
    #     #                 ])
    #     # if correct_type is False:
    #     #     raise TypeError("keys should map to a list of strings")
    #     used_keywords = []
    #     for key, keywords in self.items():
    #         # for each available key
    #         duplicates = [ v for v in keywords if v in used_keywords ]
    #         # check if we've already used the keyword
    #         if len(duplicates) > 0:
    #             for idx,dup in enumerate(duplicates):
    #                 # for each duplicate
    #                 duplicates[idx] = ", ".join([k for k,v in self.items() if k in dup])
    #                 # list its keys as comma separated string
    #                 duplicates[idx] = "{} mapped to {}".format(dup, duplicates[idx])
    #                 # create a string for that one keyword
    #             raise ValueError("A key maps to many keywords, but a keyword should map to exactly one key. {}".format("; ".join(duplicates)))
    #         else:
    #             used_keywords += keywords
    # def _test_all(self):
    #     used_keywords = []
    #     duplicates = []
    #     for keyword, key in self.items():
    #         # for each available key
    #         if keyword in used_keywords:
    #             # check if we've already used the keyword
    #             duplicates += [keyword]
    #             # save the duplicate for later analysis
    #         else:
    #             used_keywords += keyword
    #     if len(duplicates) == 0:
    #         # if no duplicates were found, the test passed
    #         return
    #     else:
    #         # otherwise
    #         for idx,dup in enumerate(duplicates):
    #             # for each keyword
    #             duplicates[idx] = ", ".join([k for k,v in self.items() if k in dup])
    #             # collect all the keys that it maps to 
    #             duplicates[idx] = "{} mapped to {}".format(dup, duplicates[idx])
    #             # create a string for that one keyword
    #         # duplicates has been transformed from a list of unique keywords
    #         # that map to many keys, to a list of sentences, describing each keyword 
    #         # that was found to map to more than one key
    #         raise ValueError("A key maps to many keywords, but a keyword should map to exactly one key. {}".format("; ".join(duplicates)))
    @staticmethod
    def fromkeys(*args, **kwargs):
        """
        Create an AliasDict, or update 
        an existing instance's entries.
        """
        def _get_pairs(args,depth=0): 
            """
            Accept the args tuple, and chunk it 
            into keys and value pairs.
            """
            if len(args) == 0:
                # if given no arguments
                yield args
            elif len(args)%2==0:
                # if given an even number of arguments
                for idx in range(0,len(args),2):
                    yield args[idx:idx+2]
                # this parses the following example
                # args = (["keyA","key_a"],"valA",["keyB","key_b"],"valB")
            elif len(args) > 0 and hasattr(args[0],"__iter__") and depth <= 1:
                for possible_pair in args:
                    yield _get_pairs(possible_pair,depth=1)
                # this parses the following example
                # args = ([["keyA","key_a"],"valA"],[["keyB","key_b"],"valB"])
            else:
                raise ValueError("Uneven pairing of keys and values")
        self = None
        if len(args) > 0:
            if isinstance(args[0], AliasDict):
                self = args[0]
                args.remove(args[0])
                # if this was called on an instance, use the instance.
        if self == None:
            self = AliasDict()
            # else create an instance
        for pair in _get_pairs(args):
            # for each set of keys that should have a given value,
            # print(pair)
            temp = None
            duplicate = None
            temp = dict.fromkeys(*pair,**kwargs)
            # call dict.fromkeys to get a dict for those keys with that value,
            # print(temp.keys())
            if temp:
                for k in temp.keys():
                    if k in self.keys():
                        duplicate = k
                        break
                if duplicate:
                    raise ValueError("A key maps to many aliases, but an alias should map to exactly one key. Cannot re-use '{}'.".format(duplicate))
                self.update(temp)
                # and use that dict in self.update()
        # self._test_all()
        return self

class StackContextFilter(logging.Filter):
    """
    Provide a context filter to trace an exception.
    """
    def __init__(self):
        pass
    def filter(self, record):
        err = None
        try:
            record.ex_only = "Unknown"
            record.ex = "NaN"
            if hasattr(record,"tb"):
                try:
                    # if hasattr(record,"locals"):
                    #     print("locals:{}".format(record.locals))
                    if hasattr(record,"globals"):
                        if isinstance(record.globals,dict):
                            # record.globals="\n"+indent("Globals:\n"+"\n".join(['''\t{} = {}'''.format(k,v) for k,v in record.globals.items()]),4)
                            record.globals="\n"+indent("Globals:\n{}".format(json.dumps(record.globals,indent=4,sort_keys=True,separators=(",",": "),cls=CustomEncoder)),4)
                        else:
                            record.globals=record.__dict__.get("globals","\n"+indent("Globals: Not exported.",4))
                    else:
                        record.globals="\n"+indent("Globals: Not exported.",4)
                    if hasattr(record,"locals"):
                        if isinstance(record.locals,dict):
                            # record.locals="\n"+indent("Locals:\n"+"\n".join(['''\t{} = {}'''.format(k,v) for k,v in record.locals.items()]),4)
                            record.locals="\n"+indent("Locals:\n{}".format(json.dumps(record.locals,indent=4,sort_keys=True,separators=(",",": "),cls=CustomEncoder)),4)
                        else:
                            record.locals=record.__dict__.get("locals","\n"+indent("Locals: Not exported.",4))
                    else:
                        record.locals="\n"+indent("Locals: Not exported.",4)

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    record.ex_only = exc_type.__name__
                    record.stack = traceback.format_exc(record.tb)
                    record.ex = record.stack.strip().split("\n")[-2].strip()
                except Exception as err:
                    record.globals={}
                    record.locals={}
                    record.stack = "No tb"
                    # aux_warn("StackContextFilter failed to get traceback.{}".format(err), extra={"err" : err, "tb" : sys.exc_info()[2]})
                    # logging.critical("StackContextFilter failed to get traceback.", extra={"err" : err, "tb" : sys.exc_info()[2]})
            else:
                # print(json.dumps(vars(record), indent=4, separators=(",",": "), sort_keys=True, cls=CustomEncoder))
                record.stack = "You forgot to export tb when an exception occurs."
                # record.stack = json.dumps(vars(record), indent=4, separators=(",",": "), sort_keys=True, cls=CustomEncoder)
                # record.stack = vars(record)
            ### example of exporting the tb below:
            ### except Exception as e:
            ###     aux_crit("Failed to data from database", extra={"err" : err, "tb" : sys.exc_info()[2]})
        except Exception as err:
            logging.exception(err)
        finally:
            # return whether the record should be exported
            return err == None

class TraceContextFilter(logging.Filter):
    """
    Provide a context filter to show which function called which, 
    stopping when we reach our 'base_fnc', __wrap_log_fnc
    """
    def __init__(self, base_fnc="__wrap_log_fnc"):
        self.base_fnc = base_fnc
    def filter(self, record):
        err = None
        try:
            record.call_trace = trace_call_path(deep=self.base_fnc)
            # trace the which function called which function,
            # and stop at __wrap_log_fnc
        except Exception as err:
            record.call_trace = "Failed to get call_trace"
            # logging.exception(err)
        finally:
            # return whether the record should be exported
            return err == None

class SQLContextFilter(logging.Filter):
    """
    Provide a context filter to give events a type
    """
    # def __init__(self, base_fnc="__wrap_log_fnc"):
    #     self.base_fnc = base_fnc
    def filter(self, record):
        err = None
        # print("SQLContextFilter")
        try:
            record.type = int(getattr(record,"type"))
            # if not hasattr(record,"type"):
            #     record.type = int(getattr(record,"type"))
            #     if isinstance(record,int):
            #         pass
            #     else:
            #         sql_handler.suggest_foreign_key("type", keys_only=False)
            try:
                record.user = int(getattr(record,"user"))
            except Exception as err:
                logging.exception(err)
                record.user = 0
        except Exception as err:
            logging.exception(err)
        finally:
            # return whether the record should be exported
            # return err == None
            return True

def get_path(path):
    """
    Convert a full path
    """
    # print("Received {}".format(path))
    path = os.path.expandvars(path)
    # print("{}".format(path))
    path = os.path.expanduser(path)
    # print("{}".format(path))
    path = os.path.normpath(path)
    # print("{}".format(path))
    path = os.path.realpath(path)
    # print("{}".format(path))
    return path

def dir_path(d, suppress=False):
    """
    Convert a string into a full path to a folder, 
    ensuring the folder exists.
    """
    d = get_path(d)
    if not os.path.isdir(d) and suppress == False:
        raise ValueError("{} does not appear to be a proper path to a folder.".format(d))
    return d

def file_path(f, suppress=False):
    """
    Convert a string into a full path to a file,
    ensuring the file exists.
    """
    # suppress prevents it from throwing an error; useful if
    # we're checking and creating the file if it doesn't exist
    f = get_path(f)
    if not os.path.isfile(f) and suppress == False:
        raise ValueError("{} does not appear to be a proper path to a file.".format(f))
    return f

class CustomEncoder(json.JSONEncoder):
    """
    Specialized JSONEncoder to handle decoding 
    special python objects that json 
    normally doesn't cover.

    Currently doesn't catch circular JSON errors... 
    """
    def default(self, obj):
        try:
            if(isinstance(obj, basestring)):
                msg = obj
            elif(isinstance(obj, complex)):
                # example of creating a custom output from an unsupported type
                msg = (lambda x: [x.real, x.imag])(obj)
            elif(inspect.ismodule(obj)):
                msg = "<module>"
            # elif(inspect.ismethod(obj)):
            #     msg = "<method>"
            # elif(inspect.isfunction(obj)):
            #     msg = "<function>"
            elif(inspect.isfunction(obj)):
                msg = str(obj)
            elif(isinstance(obj, datetime.datetime)):
                msg = obj.strftime("%Y-%m-%d %H:%M:%S")
            elif(isinstance(obj, type)):
                # transform the class object into a 
                # string that states what class it is
                msg = "(CLS {})".format(obj.__name__)
            elif(hasattr(obj, "__dict__")):
                # if it has __dict__, iterate over the 
                # entries to give key value pairs
                try:
                    d = {}
                    for attr, val in obj.__dict__.items():
                        d[attr] = str(val)
                    msg = d
                except Exception as e:
                    print(str(e))
                    msg = "(CLS {} - circ reference in dict)".format(obj.__name__)
            else:
                # we haven't written a rule to handle this object yet
                try:
                    obj_type = str(type(obj))
                    msg = re.sub(r"^<type '(.+)'>$", r"\1", obj_type)
                    # just show its type
                except Exception as e:
                    # fallback in case things go very wrong
                    msg = "Not JSON Seriablizable"
        except Exception as err:
            # fallback in case things go very wrong
            msg = "Not JSON Seriablizable"
        return msg

class OptionalStrAction(argparse.Action):
    """
    Setup an ArgumentParser's str argument to be an empty string
    if no string is passed to it.
    Examples:
        A)
            '--proxy_url "some/new/value/for/it" --quantity 1'
            Namespace.proxy_url == "some/new/value/for/it"
            Namespace.quantity == 1
        B)
            '--proxy_url "" --quantity 1'
            Namespace.proxy_url == ""
            Namespace.quantity == 1
        C)
            '--proxy_url --quantity 1'
            Namespace.proxy_url == ""
                # would have been None
            Namespace.quantity == 1
    """
    def __init__(self, *args, **kwargs):
        super(OptionalStrAction, self).__init__(kwargs.pop("option_strings"), kwargs.pop("dest"), **kwargs)
    def __call__(self, parser, namespace, value, *args, **kwargs):
        if value == None:
            value = ""
        setattr(namespace, self.dest, value)

def force_hash(d):
    """
    Get a hash number Always.
    """
    h = []
    try:
        if d == None:
            return hash(1)
        # if isinstance(d, str) or isinstance(d, unicode) or isinstance(d, bool) or isinstance(d, int) or isinstance(d, float) or isinstance(d, buffer) or isinstance(d, bytearray):
        if isinstance(d, str) or isinstance(d, bool) or isinstance(d, int) or isinstance(d, float) or isinstance(d, buffer) or isinstance(d, bytearray):
            return hash(d)
        elif(isinstance(d, list) or isinstance(d, tuple)):
            if len(d) == 0:
                return force_hash(None)
            else:
                for item in d:
                    h += [force_hash(item)]
        elif(isinstance(d, datetime.datetime)):
            return hash(d.strftime("%Y-%m-%d %H:%M:%S"))
        elif hasattr(d, "__dict__") or isinstance(d, dict):
            # if it looks like a dictionary
            if not isinstance(d, dict):
                # but it isnt
                d = d.__dict__
                # make it a dict
            for (i, k) in enumerate(sorted(d.keys())):
                h += [hash(tuple([k, force_hash(d[k])]))]
        elif hasattr(d, "__str__"):
            return hash(str(d))
        else:
            raise StandardError("Unable to force a hash on this varable")
    except Exception as err:
        aux_crit("FAILED TO FORCE HASH", extra={"err" : err, "tb" : get_tb()})
    h = hash(tuple(h))
    if h <= 0:
        h = int(str(h).replace("-","")+"0")
    else:
        h = int(str(h).replace("-","")+"1")
    return h


class ProgressBar(object):
    def __init__(self, stream, incrementation=50, tick="#", blank=" ", start="[", end="]"):
        super(ProgressBar, self).__init__()
        self.stream = stream
        self.incrementation = incrementation
        self.increments = 0
        self.tick = tick
        self.blank = blank
        self.start = start
        self.end = end
        self.length = 0
        self._progress = 0
        self._total = 0
        self._bar = ""
        self.msg = ""
    @property
    def step_size(self):
        return float(self.total)/float(self.incrementation)
    @property
    def remainder(self):
        return self.incrementation-self.increments
    @property
    def percentage(self):
        return int(math.ceil(self.increments*100/self.incrementation))
    @property
    def percentage_str(self):
        return "{: >3}%".format(self.percentage)
    @property
    def bar(self):
        return self._bar
    @bar.setter
    def bar(self, value):
        self._bar = "".join([
                        (self.blank if c >= self.increments else self.tick)
                        for c in range(self.incrementation)])
    @property
    def msg(self):
        return self._msg
    @msg.setter
    def msg(self, value):
        self.bar = ""
        self._msg = u"{percentage} {start}{bar}{end}".format(
                        percentage=self.percentage_str,
                        start=self.start,
                        end=self.end,
                        bar=self.bar)
        self.length = len(self._msg)
    @property
    def total(self):
        return self._total
    @total.setter
    def total(self, value):
        self._total = value
    @property
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        self._progress = value
        while self.step_size*float(self.increments) < float(value) and self.increments <= self.incrementation:
            self.increments += 1
        self.msg = ""
    def seek(self,*steps):
        self.stream.write("\b"*self.length)
    def update(self, progress, total):
        # if total != self._total:
        if progress < self.progress:
            self.reset()
        self.total = total
        self.progress = progress
        self.stream.write(self.msg)
        self.stream.flush()
        if progress != total:
            self.seek()
        else:
            self.stream.write("\n")
    def reset(self):
        self.progress = 0
        self.increments = 0
    def __str__(self):
        return "<ProgressBar {}>".format(self.percentage_str)

def prompt_bool(prompt,strict=False):
    """
    Get user input for whether or not to continue with something. 
    returns True if the user confirms the prompt, False if the 
    user denies the prompt, and None if the user refuses to 
    answer the prompt (ie: KeyboardInterrupt).
    """
    answer = None
    # None = cancel/ no answer/ nonsense
    # False = deny the prompt
    # True = confirm the prompt
    strict_bool_pattern = r"(?:(?P<confirm>true|tru|tr|t|yes|yep|ye|y|1)|(?P<deny>false|no|n|nope|no|not|cancel|cance|canc|can|ca|c|cncl|stop|stp|0+))"
    free_bool_pattern = r"(?:\n|\s+|^)(?:(?P<confirm>true|tru|tr|t|yes|yep|ye|y|1)|(?P<deny>false|no|n|nope|no|not|cancel|cance|canc|can|ca|c|cncl|stop|stp|0+))(?:\n|\s+|$)"
    if strict == True:
        bool_pattern = strict_bool_pattern
    else:
        bool_pattern = free_bool_pattern
    bool_pattern = re.compile(bool_pattern,re.IGNORECASE)
    try:
        _answer = raw_input(prompt+"\n")
        s = re.search(bool_pattern,_answer)
        if s:
            s = s.groupdict()
            if s.get("deny",None) != None:
                s["deny"] = True
            else:
                s["deny"] = False
            if s.get("confirm",None) != None:
                s["confirm"] = True
            else:
                s["confirm"] = False
            if s.get("deny"):
                answer = False
            elif s.get("confirm"):
                answer = True
    except KeyboardInterrupt:
        pass
    return answer

def get_status_update_fnc(progress_bars):
    def status_update_fnc(byte_progress, byte_total):
        for bar in progress_bars:
            bar.update(byte_progress, byte_total)
    return status_update_fnc
def status_update_fnc(byte_progress, byte_total):
    global progress_bars
    for bar in progress_bars:
        bar.update(byte_progress, byte_total)

def dict_factory(cursor, row):
    """
    Export sqlite rows as dictionaries.
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def row_factories(*args):
    """
    Function to wrap all factory functions, and add a parser to 
    pick and choose which to use at any given time.
    """
    row_factory = sqlite3.Row
    def tuple_factory(cur, row):
        return row
    def dict_factory(cur, row):
        d = {}
        # junk because they're always None 'https://docs.python.org/2/library/sqlite3.html#sqlite3.Cursor.description'
        for idx, (header,junk1,junk2,junk3,junk4,junk5,junk6) in enumerate(cur.description):
            d[header] = row[idx]
        return d
    def obj_factory(cur, row):
        obj = argparse.Namespace()
        for idx, (header,junk1,junk2,junk3,junk4,junk5,junk6) in enumerate(cur.description):
            setattr(obj, header, row[idx])
        return obj
    setattr(row_factories, "default", tuple_factory)
    # setting it as an attribute of the function lets us change the 
    # default later if we need this function in a different context
    factories_dict = {name.replace("_factory", ""):fnc for name,fnc in locals().items() if name.find("_factory") != -1}
    # create a dict mapping local names to functions
    factories_list = factories_dict.keys()
    # get a list of those local names
    parser = argparse.ArgumentParser(description="choose what data format sql commands return.")
    parser.add_argument("factory",
                        choices=factories_list,
                        help="What data type should be output.")
    args = parser.parse_args(args)
    return factories_dict.get(args.factory, row_factories.default)
    # this seemed better than a long if-else chain, and having 
    # to make sure 'choices' gets updated with every new function

class SQLiteInterface(object):
    """docstring for SQLiteInterface"""
    # schema = "./SCHEMA_email_data.sql"
    # fixtures = "./FIXTURES_email_data.sql"
    def __init__(self, database, schema=None, fixtures=None, row_factory=None):
        super(SQLiteInterface, self).__init__()
        # self._row_factory = getattr(row_factories,"default")
        self._row_factory = row_factories("dict")
        try:
            if row_factory != None:
                self._row_factory = row_factories(row_factory)
        except Exception as err:
            logging.exception(err)
        self.__schema = None
        self.__fixtures = None
        if schema:
            self.__schema = file_path(schema)
        if fixtures:
            self.__fixtures = file_path(fixtures)
        self.database = database
        self.create_lock()
    @property
    def database(self):
        # getter for database path
        return self._database

    @property
    def db_name(self):
        # get basename for database file
        file = os.path.basename(self.database)
        name, ext = os.path.splitext(file)
        return name
    
    @database.setter
    def database(self, value):
        def read_sql_file_into_db(file_path, db):
            try:
                commands = [
                    ("cat",file_path),
                    ("sqlite3", db),
                    ]
                cmd_list = [None for cmd in commands]
                prev_cmd, result = None, None
                for idx,cmd_args in enumerate(commands):
                    if prev_cmd == None:
                        cmd_list[idx] = subprocess.Popen(
                                            cmd_args, 
                                            stdout=subprocess.PIPE)
                    else:
                        cmd_list[idx] = subprocess.Popen(
                                            cmd_args,
                                            stdin=prev_cmd.stdout,
                                            stdout=subprocess.PIPE)
                    if prev_cmd != None:
                        prev_cmd.stdout.close()
                        # Allow previous command to receive SIGPIPE if the next command exits
                    prev_cmd = cmd_list[idx]
                if prev_cmd != None:
                    result = prev_cmd.communicate()[0]
            except subprocess.CalledProcessError as err:
                result = "Error({}):{}\n\t{}".format(
                    err.returncode, 
                    str(err.output).strip(),
                    cmd_list)
            except Exception as err:
                raise err
            return result
        new_file = False
        try:
            db_path = file_path(value)
            # confirm its a file
        except Exception as err:
            db_path = file_path(value, suppress=True)
            # get the full path to where we want it to be
            new_file = True
            # note that we'll need to make the file
            
        self._database = db_path
        if self.__schema == None:
            try:
                self.__schema = file_path(os.path.join(os.path.dirname(db_path),"SCHEMA_"+self.db_name+".sql"))
                # Check if a schema exists in the same directory
            except Exception as err:
                # aux_debug("Failed to find schema for {}:{}".format(value,err))
                logging.exception(err)
                self.__schema = None
        if self.__fixtures == None:
            try:
                self.__fixtures = file_path(os.path.join(os.path.dirname(db_path),"FIXTURES_"+self.db_name+".sql"))
                # Check if a fixtures exists in the same directory
            except Exception as err:
                # aux_debug("Failed to find fixtures for {}:{}".format(value,err))
                logging.exception(err)
                self.__fixtures = None
        if new_file:
            with sqlite3.connect(self._database) as db:
                # connect/create the db file
                cur = db.cursor()
                # if self.schema:
                #     # aux_debug("Using schema")
                #     aux_debug("Using schema:'''{}'''".format(self.schema))
                # cur.executemany(self.schema)
                result = read_sql_file_into_db(self._schema, self.database)
                # aux_debug(result)
                # execute the sql commands found in the file
                # if self.fixtures:
                #     # aux_debug("Using fixtures")
                #     aux_debug("Using fixtures:'''{}'''".format(self.fixtures))
                # cur.executemany(self.fixtures)
                result = read_sql_file_into_db(self._fixtures, self.database)
                # aux_debug(result)
                # execute the sql commands found in the file

    @property
    def _schema(self):
        # read only
        return self.__schema
        # path to a sql file that holds the schema

    @property
    def _fixtures(self):
        # read only
        return self.__fixtures
        # path to a sql file that holds the fixtures

    @property
    def schema(self):
        # read only;
        # contents of the schema file
        result = ""
        if self._schema != None:
            with open(self._schema,"r") as f:
                result = f.read()
        return result

    @property
    def fixtures(self):
        # read only;
        # contents of the fixtures file
        result = ""
        if self._fixtures != None:
            with open(self._fixtures,"r") as f:
                result = f.read()
        return result

    @property
    def row_factory(self):
        # get the prefered row_factory to use after connecting to the database
        return self._row_factory

    @row_factory.setter
    def row_factory(self, value):
        # set the prefered row_factory to use after connecting to the database;
        # accepts a function, or a string to pass to row_factories
        if isinstance(value, str):
            value = row_factories(value)
        self._row_factory = value

    @property
    def _connection(self):
        # connect to the sql database
        return self.__connection
        # sqlite3.connect(self.database)
    
    @_connection.setter
    def _connection(self, value):
        # set values in the database
        self.__connection = value

    @property
    def _cursor(self):
        # cursor for the sql database
        return self.__cursor        

    def create_lock(self):
        self.lock = threading.RLock()

    def acquire(self):
        self.lock.acquire()
        self._connection = sqlite3.connect(self.database)
        # get and store the sqlite3 connection in the hidden attribute

    def release(self):
        self._connection.close()
        self.lock.release()

    def __enter__(self):
        self.acquire()
        self._connection.row_factory = self.row_factory
        self.__cursor = self.__connection.cursor()
        return self._cursor
        # return a sqlite cursor to the database

    def __exit__(self, type, value, traceback):
        self._connection.commit()
        self.release()
    def update_view(self, view_name):
        # drop and create a view again
        success = False
        view = None
        initial_factory = self.row_factory
        self.row_factory = "dict"
        self.acquire()
        self._connection.row_factory = self.row_factory
        db = self.__connection.cursor()
        rows = db.execute("SELECT name,tbl_name,sql FROM sqlite_master WHERE type='view'")
        result = [row for row in rows.fetchall()]
        for v in result:
            if v.get("name") == view_name or v.get("tbl_name") == view_name:
                # we've confirmed that the table exists in our db
                view = v
                # hold onto its config
        if view != None and view.get("sql",None) != None:
            # DROP VIEW IF EXISTS [Contacts];
            # CREATE VIEW IF NOT EXISTS [Contacts] AS SELECT users.role, users.name, users.username, emails.data as address FROM ((emails INNER JOIN users_emails ON emails.id=users_emails.email_id) INNER JOIN users ON users.id==users_emails.user_id);
            query = "DROP VIEW IF EXISTS [{}];".format(view_name)
            rows = db.execute(query)
            # drop the old view
            query = view.get("sql")
            if query.upper().find("IF NOT EXISTS") == -1:
                query = query.replace("CREATE VIEW","CREATE VIEW IF NOT EXISTS")
            rows = db.execute(query)
            # create the view again
            success = True
        self.release()
        self.row_factory = initial_factory
        return success

class SQLiteHandler(logging.Handler):
    """docstring for SQLiteHandler"""
    def __init__(self, database, table, schema=None, fixtures=None, row_factory=None):
        # super(SQLiteHandler, self).__init__()
        self.__interface = None
        self._columns = None
        self._set_interface(database, schema=schema, fixtures=fixtures, row_factory=row_factory)
        logging.Handler.__init__(self)
        self._table = table
        # the table to insert into during emit
        # sql_handler = SQLiteInterface("./email_data.db")
        try:
            self.interface.row_factory = row_factories("tuple")
            with self.interface as db:
                rows = db.execute("SELECT name,tbl_name FROM sqlite_master WHERE type='table'")
                tables = []
                for row in rows.fetchall():
                    tables += [row[0]]
                    tables += [row[1]]
                tables = list(set(tables))
                if table not in tables:
                    raise ValueError("{} not found in {}".format(table, database))
                # query = "SELECT name,pk FROM pragma_table_info('{}');".format(table)
                query = "PRAGMA TABLE_INFO('{}');".format(table)
                # columns = [(column,pk) for column,pk in rows.fetchall()]
                rows = db.execute(query)
                # rows = db.execute("PRAGMA TABLE_INFO(':table');", {"table":table})
                # self.__columns = [(column,pk) for cid,column,data_type,nnull,def_val,pk in rows.fetchall()]
                # self._columns = [column[0] for column in self.__columns]
                # self._primary = [column[0] for column in self.__columns if column[1] == 1]
                # changed it so we can store and check other info too, besides pk
                # aux_debug(rows.fetchall())
                self.__columns = { column:{
                        "cid": cid,
                        "column": column,
                        "data_type": data_type,
                        "nnull": nnull,
                        "def_val": def_val,
                        "pk":pk,
                        "fk":None
                    } for (cid,column,data_type,nnull,def_val,pk) in rows.fetchall()}               

                self._columns = [None for c in self.__columns.keys()]
                for column,cfg in self.__columns.items():
                    self._columns[cfg.get("cid")] = column
                for column,cfg in self.__columns.items():
                    if cfg.get("pk",0) == 1:
                        self._primary = column
                        break
                self.__insert = "INSERT INTO {table} ( {columns} ) VALUES ( {values} );".format(
                                    table=self.table,
                                    columns=", ".join(['"{}"'.format(col) for col in self.columns]),
                                    # values=", ".join([ ("?" if col.pk==0 else "NULL") for col in self.__columns]),
                                    # values=", ".join([ ("?" if cfg.get("pk",0)==0 else "NULL") for col,cfg in self.__columns.items()]),
                                    values=", ".join([ ("?" if self.__columns.get(col).get("pk",0)==0 else "NULL") for col in self.columns]),
                                    )
                query = "PRAGMA FOREIGN_KEY_LIST('{}');".format(table)
                rows = db.execute(query)
                f_keys = { frm:{
                        "id":id,
                        "seq":seq,
                        "table":table,
                        "frm":frm,
                        "to":to,
                        "on_update":on_update,
                        "on_delete":on_delete,
                        "match":match,
                        "choices":[]
                    } for id,seq,table,frm,to,on_update,on_delete,match in rows.fetchall()}
            self.interface.row_factory = row_factories("dict")
            with self.interface as db:
                for fk,cfg in f_keys.items():
                    if fk in self.__columns:
                        if cfg.get("table") in tables:
                            query = "SELECT * FROM {}".format(cfg.get("table"))
                        rows = db.execute(query)
                        cfg["choices"] = [row.get(cfg.get("to")) for row in rows.fetchall()]
                        self.__columns[fk]["fk"] = cfg
            # aux_debug(json.dumps(self.__columns,indent=4,separators=(",",": ")))
        except Exception as err:
            logging.exception(err)

    @property
    def table(self):
        return self._table
    @property
    def columns(self):
        return self._columns
    @property
    def primary(self):
        return self._primary

    @property
    def _insert(self):
        return self.__insert

    @property
    def interface(self):
        return self.__interface
    
    def _set_interface(self, database, schema=None, fixtures=None, row_factory=None):
        if self.__interface != None:
            if hasattr(self.__interface,"schema"):
                del self.__interface
        self.__interface = SQLiteInterface(database, schema=schema, fixtures=fixtures, row_factory=row_factory)


    def suggest_foreign_key(self, fk_col, keys_only=True):
        # show what values would be valid for this foreign key
        fk = self.__columns.get(fk_col, {}).get("fk",None)
        if fk:
            with self.interface as db:
                query = "SELECT * FROM {}".format(fk.get("table"))
                db.row_factory = row_factories("dict")
                rows = db.execute(query)
                to_col = fk.get("to")
                if keys_only==True:
                    result = [ row.get(to_col) for row in rows.fetchall() ]
                else:
                    result = { row.pop(to_col):row.get("name") for row in rows.fetchall() }
            return result
        else:
            raise ValueError("'{}' not found in table '{}', or it's not a foreign key.".format(fk_col, self.table))

    @property
    def event_types(self):
        if not hasattr(self,"__event_types"):
            self.__event_types = self.suggest_foreign_key("type", keys_only=False)
            # map key to foreign key
            # self._event_types = {v:k for k,v in self.__event_types.items()}
            # # map foreign key to key
        return self.__event_types

    @property
    def _event_types(self):
        # map foreign key to key
        return {v:k for k,v in self.event_types.items()}

    def emit(self, record):
        # todo: change it so that it gets the python type
        # from sql instead of hard coded here as integer
        # print("SQLiteHandler.emit()",file=sys.stderr)
        try:
            # print("SQLiteHandler.emit")
            record.level = record.__dict__.get("levelno",self.level)
            if not hasattr(record,"time"):
                record.time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not hasattr(record,"user"):
                record.user = None
            if not hasattr(record,"type"):
                record.type = 3
                # if no type was provided, use 'System'
            else:
                # double check the type value
                try:
                    record.type = int(record.type)
                except Exception as err:
                    # didn't recieve an integer as expected
                    if record.type in self._event_types:
                        record.type = self._event_types.get(record.type)
                    else:
                        raise err
                
            # msg = self.format(record)
            column_data = []
            for column in self.columns:
                if column != self.primary:
                    column_data += [record.__dict__.get(column,"NULL")]
            # aux_debug(self.columns)
            # aux_debug(self._insert)
            # aux_debug(column_data)
            # aux_debug(record.__dict__)
            with self.interface as db:
                db.execute(self._insert,tuple(column_data))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

# sql_interface = SQLiteInterface("./data.db")
# sql_interface.row_factory = row_factories("dict")

# def check_db(w):
#   debug("{}: waiting for db.".format(thread_name()))
#   time.sleep(w)
#   with sql_interface as db:
#       debug("{}: got db.".format(thread_name()))
#       # rows = db.execute("SELECT * FROM Contacts")
#       rows = db.execute("SELECT * FROM event_types")
#       debug("{}: did command.".format(thread_name()))
#       # result = [[db.description], [rows.fetchall()]]
#       # result = [(row.keys()[idx],column) for row in rows.fetchmany() for idx,column in enumerate(row)]
#       result = { row.get("id"):row for row in rows.fetchall() }
#       # debug(dir(getattr(sql_interface,"__connection")))
#       # debug(dir(db))
#       debug("{}: holding db.".format(thread_name()))
#       time.sleep(5)
#   debug("{}: released db.".format(thread_name()))
#   # debug("{}:{}".format(thread_name(),result))

# t1 = threading.Thread(target=check_db,name="T1",args=(0,))
# debug("{}: created threads.".format(thread_name()))
# t1.start()

def test_sql_handler(channel,logr):
    sql_handler = SQLiteHandler(
        database="/home/apsdev/bin/sql/email_data.db",
        table="events",
        schema="/home/apsdev/bin/sql/SCHEMA_email_data.sql",
        fixtures="/home/apsdev/bin/sql/FIXTURES_email_data.sql",
        )
    channel(sql_handler.columns)
    channel(sql_handler.primary)
    # channel(type(result[0]))
    sql_handler.setLevel(20)
    logr.addHandler(sql_handler)
    # channel(sql_handler.suggest_foreign_key("type", keys_only=False))
    channel(sql_handler._event_types.get("Output"))
    channel("Testing sql_handler".format(),extra={"type":"System"})
    logr.info("Testing sql_handler".format(),extra={"type":"System"})
    sql_handler.interface.update_view("Events Log")

    with sql_handler.interface as db:
        # db.row_factory = row_factories("dict")
        query = "SELECT * FROM Events Log"
        rows = db.execute(query)
        result = rows.fetchall()
        channel(result)
        query = "SELECT * FROM events"
        rows = db.execute(query)
        result = rows.fetchall()
        channel(result)

try:
    # # open the yaml file
    # with open(os.path.join(
    #         os.path.dirname(__file__),
    #         "logging_config.yml"), "r") as f:
    #     cfg = yaml_safe_load(f)
    #     # and parse the yaml data into a python dict
    # log_folder = cfg.pop("log_folder")
    # # get the directory where we want the log files to reside
    # if not os.path.isdir(log_folder):
    #     # if the directory does not exist
    #     os.mkdir(log_folder)
    #     # make the directory
    # for name,hdlr in cfg.get("handlers").items():
    #     # for each handler in the config
    #     if "filename" in hdlr:
    #         # if the handler has a filename attribute
    #         cfg["handlers"][name]["filename"] = os.path.join(log_folder, hdlr.get("filename"))
    #         # set the file to reside in the log directory we want to use
    # logging.config.dictConfig(cfg)
    # # use the dict to configure the most of the logging setup
    aux_logr = logging.getLogger("Aux")
    # get a logger 
    aux_log = aux_logr.log
    aux_crit = aux_logr.critical
    aux_error = aux_logr.error
    aux_warn = aux_logr.warning
    aux_info = aux_logr.info
    aux_debug = aux_logr.debug
    # take the logger methods that record messages and 
    # convert them into simple one word functions
    assert aux_debug == getattr(aux_logr,"debug"), "Something went wrong with getting logging functions..."
    # the logger method called "debug", should now be the same as our function aux_debug()
# except YAMLError as err:
#     logging.log(logging.CRITICAL,"Failed to read yaml file.")
#     logging.exception(err)
#     # print the message to the root logger
#     raise err
except Exception as err:
    logging.log(logging.CRITICAL,"Failed to configure logging.")
    logging.exception(err)
    # print the message to the root logger
    raise err

