#!/usr/bin/python3.7
import contextlib
with contextlib.redirect_stdout(None):
    from pygame import Rect
    from pygame.draw import rect as draw_rect
del contextlib

class Fruit(object):
    """
    Provides a reward to the Snake.
    """
    def __init__(self, name, dimensions, value, *args, **kwargs):
        super(Fruit, self).__init__()
        self.name = name
        self.value = value
        self.dimensions = dimensions
        self.color = kwargs.get("color", (200, 200, 200) )
        self.frequency = kwargs.get("frequency", )
        self.id = None

    def render(self):
        """
        Return a rectangle to display in a Surface.
        """
        return Rect(self.x, self.y, self.w, self.h)

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
        self._dimensions = [value[0], value[1], max(value[2], 0)]
        # set _dimensions so that x,y,size getters work;
        # size cannot be negative

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
    def origin(self):
        """
        Getter for the x,y position.
        """
        return self.dimensions[0], self.dimensions[1]
    @property
    def size(self):
        """
        How many pixels this virtual pixel occupies
        """
        return self.dimensions[2]
    @property
    def w(self):
        """
        The width of the fruit in pixels.
        """
        return self.size
    @property
    def h(self):
        """
        The height of the fruit in pixels.
        """
        return self.size

    @property
    def name(self):
        """
        Getter for what the fruit is named.
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Setter for what the fruit is named.
        """
        if not hasattr(self,"_name"):
            self._name = value
        else:
            raise ValueError("Name should not change after initialization")

    @property
    def value(self):
        """
        Getter for how much this object is worth to a snake.
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Setter for how much this object is worth to a snake.
        """
        self._value = value

    @property
    def color(self):
        """
        Getter for what color this Fruit would appear as when drawn on a surface.
        """
        return self._color

    @color.setter
    def color(self, color):
        """
        Setter for what color this Fruit would appear as when drawn on a surface.
        """
        self._color = color

    @property
    def frequency(self):
        """
        Getter for how often this object should randomly
        appear in a given game per second.
        """
        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        """
        Setter for how often this object should randomly
        appear in a given game per second.
        """
        self._frequency = frequency

    def __str__(self):
        # return "Fruit<{}>".format(self.value)
        return f"Fruit({self.name},v={self.value},dim={self.dimensions})"

    def __repr__(self):
        return str(self)
