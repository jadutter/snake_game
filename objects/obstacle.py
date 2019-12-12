#!/usr/bin/python3.7
# from auxillary import *
import contextlib
with contextlib.redirect_stdout(None):
    from pygame import Rect
    from pygame.draw import rect as draw_rect
del contextlib

class Obstacle(object):
    """
    Something that is not part of the snake,
    but will still trigger death if the snake intersects it.
    """
    def __init__(self, *dimensions):
        super(Obstacle, self).__init__()
        if len(dimensions) == 1:
            # if given one argument
            # p = [1,2,3,4]
            # o = Obstacle(p)
            self.dimensions = dimensions[0]
            # assume its an iterable with 4 elements
        else:
            # o = Obstacle(1,2,3,4)
            self.dimensions = dimensions
            # otherwise, assume we've gotten the 4 arguments
    def render(self):
        """
        Return a rectangle to display in a Surface.
        """
        return Rect(*self.dimensions)
        # return Rect(self.x, self.y, self.w, self.h)

    def draw(self,surface,color):
        """
        Draw this obstacle on a Surface.
        """
        draw_rect(surface, color, self.render())

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
        if len(value) == 3:
            self._dimensions = [value[0], value[1], max(value[2], 0), max(value[2], 0)]
        else:
            self._dimensions = [value[0], value[1], max(value[2], 0), max(value[3], 0)]
        # set _dimensions so that x,y,w,h getters work;
        # height and width cannot be negative
        if self.w == max(self.w,self.h):
            # if the width is the longest
            # self._size = self.h
            self._size = 3
            # set size to return the dimension at index 3 (height)
            self._heading = 1
            # the obstacle is pointed EW (odd)
        else:
            # if the height is the longest
            # self._size = self.w
            self._size = 2
            # set size to return the dimension at index 2 (width)
            self._heading = 0
            # the obstacle is pointed NS (even)

    @property
    def x(self):
        """
        Getter for the horizontal position.
        """
        return self.dimensions[0]

    @property
    def y(self):
        """
        Getter for the vertical position.
        """
        return self.dimensions[1]

    @property
    def w(self):
        """
        Getter for the width.
        """
        return self.dimensions[2]

    @property
    def h(self):
        """
        Getter for the height.
        """
        return self.dimensions[3]

    @property
    def heading(self):
        """
        Whether this obstacle is pointed NS or EW;
        """
        return self._heading

    @property
    def size(self):
        """
        An obstacle is a bar of some length, 
        that occupies one virtual pixel in width.
        Size returns the virtual pixel value (how many pixels, 
        it's one virtual pixel occupies)
        """
        return self.dimensions[self._size]
    def __str__(self):
        # return "Obstacle<{}>".format(self.dimensions)
        return f"Obstacle({self.dimensions})"

    def __repr__(self):
        return str(self)




