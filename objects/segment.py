#!/usr/bin/python3.7
import contextlib
with contextlib.redirect_stdout(None):
    from pygame import Rect
    # from pygame.draw import rect as draw_rect
del contextlib
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

class Segment(object):
    """
    A Segment represents a single rectangle in a Snake.
    A Snake can have many segments, and segments can occupy
    many virtual pixels.
    """
    def __init__(self, *args, **kwargs):
        super(Segment, self).__init__()
        if len(args) == 1:
            # if given one argument
            dimensions, heading = args[0]
            # assume element 0 is iterable with length of 2
        else:
            dimensions, heading = args
            # otherwise, assume its iterable with length of 2
        self.dimensions = dimensions
        self.heading = heading
        if self.w > self.h:
            # if the width is longer than the height
            assert (self.heading%2 == 1), "Heading does not match up with the longest dimension"
            # heading should be an odd number to indicate east or west
        elif self.h > self.w:
            # if the height is longer than the width
            assert (self.heading%2 == 0), "Heading does not match up with the longest dimension"
            # heading should be an even number to indicate north or south

    def render(self):
        """
        Return a rectangle to display in a Surface.
        """
        return Rect(*self.dimensions)
        # return Rect(self.x, self.y, self.w, self.h)

    @property
    def length(self):
        """
        Return the longest dimension of the segment.
        """
        # return max(self.h, self.w)
        if self.heading%2 == 0:
            # if pointed north/south
            return self.h
            # return height
        else:
            # if pointed east/west
            return self.w
            # return width

    @property
    def dimensions(self):
        """
        Getter for the x,y,w,h values
        """
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value):
        """
        Setter for the x,y,w,h values
        """
        self._dimensions = [value[0], value[1], max(value[2], 0), max(value[3], 0)]
        # set _dimensions so that x,y,w,h getters work;
        # height and width cannot be negative
        if self.w == max(self.w,self.h):
            # if the width is the longest
            # self._size = self.h
            self._size = 3
            # set size to return the dimension at index 3 (height)
        else:
            # if the height is the longest
            # self._size = self.w
            self._size = 2
            # set size to return the dimension at index 2 (width)

    @property
    def x(self):
        """
        Getter for the horizontal position.
        """
        return self.dimensions[0]
    
    @x.setter
    def x(self, value):
        """
        Setter for the horizontal position.
        """
        self.dimensions[0] = value

    @property
    def y(self):
        """
        Getter for the vertical position.
        """
        return self.dimensions[1]
    
    @y.setter
    def y(self, value):
        """
        Setter for the vertical position.
        """
        self.dimensions[1] = value

    @property
    def w(self):
        """
        Getter for the width.
        """
        return self.dimensions[2]
    
    @w.setter
    def w(self, value):
        """
        Setter for the width.
        """
        self.dimensions[2] = max(value, 0)

    @property
    def h(self):
        """
        Getter for the height.
        """
        return self.dimensions[3]
    
    @h.setter
    def h(self, value):
        """
        Setter for the height.
        """
        self.dimensions[3] = max(value, 0)

    @property
    def size(self):
        """
        How many pixels this segment occupies
        """
        # return self.dimensions[self._size]
        return min(self.dimensions[2],self.dimensions[3])

    @property
    def origin(self):
        """
        Getter top left point of this rectangle.
        """
        return [self.x,self.y]

    @property
    def heading(self):
        """
        Getter for the direction this segment is pointed toward.
        """
        return self._heading

    @heading.setter
    def heading(self, value):
        """
        Setter for the direction this segment is pointed toward.
        """
        self._heading = value

    @property
    def head_heading(self):
        """
        The direction the head is pointed towards.
        """
        return self.heading

    @property
    def tail_heading(self):
        """
        The direction the tail is pointed towards.
        """
        return (self.heading+2)%4
    
    def increment(self):
        """
        Append a virtual pixel to the head
        """
        # debug("increment{}".format(id(self)))
        if self.heading == 0:
            # headed north
            self.y -= self.size
            self.h += self.size
            # move top left corner & incr height
        elif self.heading == 1:
            # headed east
            self.w += self.size
            # keep top left corner & incr width
        elif self.heading == 2:
            # headed south
            self.h += self.size
            # keep top left corner & incr height
        elif self.heading == 3:
            # headed west
            self.x -= self.size
            self.w += self.size
            # move top left corner & incr width

    def decrement(self):
        """
        Remove a virtual pixel to the tail
        """
        # debug("decrement{}".format(id(self)))
        if self.heading == 0:
            # headed north
            self.h -= self.size
            # keep top left corner & decr height
        elif self.heading == 1:
            # headed east
            self.x += self.size
            self.w -= self.size
            # move top left corner & decr width
        elif self.heading == 2:
            # headed south
            self.y += self.size
            self.h -= self.size
            # move top left corner & decr height
        elif self.heading == 3:
            # headed west
            self.w -= self.size
            # keep top left corner & decr width

    def __str__(self):
        # return "Seg<{},{},{},{}|{}|{}|{}>".format(self.x,self.y,self.w,self.h,self.dimensions,self.heading,self.length)
        return "Seg<{},{},{},{}>".format(self.x,self.y,self.w,self.h)

    def __repr__(self):
        d = {}
        for k in ["x","y","w","h","origin","heading","length"]:
            if (k.find("__") != 0):
                d[k] = getattr(self,k)
        return "Seg({})".format(", ".join(["{} = {}".format(k,v) for k,v in d.items()]))
        # return str(self)
