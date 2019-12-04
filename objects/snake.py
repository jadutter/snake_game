#!/usr/bin/python3.7
# from auxillary import *
import contextlib
with contextlib.redirect_stdout(None):
    from pygame import Rect
    from pygame.draw import rect as draw_rect
del contextlib
from .fruit import Fruit
from .obstacle import Obstacle
from .segment import Segment

class Snake(object):
    """
    The object a human or computer controls as they move about the game space.
    """
    def __init__(self, dimensions, heading, *args, **kwargs):
        super(Snake, self).__init__()
        self.heading = heading
        head = Segment(dimensions, self.heading)
        self.segments = [head]
        # initialize the array of Segments that compose it's body
        self.size = head.size

    def _render(self):
        """
        Generate a series of Rectangles representing this Snake's segments.
        """
        for i, seg in enumerate(self.segments):
            yield seg.render()

    def render(self):
        """
        Return a series of Rectangles representing this Snake's segments.
        """
        return list(self._render())

    def draw(self,surface,color):
        """
        Draw a series of rectangles on a Surface.
        """
        def get_green(i):
            val = 10
            # the color should never go below 10 green
            val = max(val, 255-255*(i))
            # the color should start bright green, and decrease 
            # in intensity with each segment
            return val
        for i, seg in enumerate(self._render()):
            # get an index and a Rectangle representing a Segment
            fraction = i/len(self.segments)
            color = (0, get_green(fraction), 0)
            # get the color we want to use on this Segment
            draw_rect(surface, color, seg)
            # draw the segment onto the surface

    @property
    def belly(self):
        """
        If belly > 0, belly will be decremented instead of tail
        """
        if not hasattr(self,"_belly"):
            self._belly = 0
            return self._belly
        return max(0, self._belly)

    @belly.setter
    def belly(self, value):
        """
        Set the belly to a positive integer.
        """
        # debug("Changing belly from {} to {}".format(self._belly,value))
        self._belly = max(value, 0)
    
    @property
    def length(self):
        """
        The sum of the lengths of all the Snake's segments.
        """
        return sum([ seg.length for seg in self.segments ])

    @property
    def head(self):
        """
        The segment that represents the Snake's head.
        """
        return self.segments[0]

    @property
    def tail(self):
        """
        The segment that represents the Snake's tail.
        """
        return self.segments[-1]

    @property
    def is_alive(self):
        """
        Returns a boolean for whether the Snake is still alive.
        """
        return len(self.segments) > 0

    @staticmethod
    def _is_between (pa, pb, pc, i):
        """
        Given three points, and an integer (0 or 1), 
        check if the third point is between the first two points
        on the given dimension 'i'.
        """
        # example: 
        # --- i == 0 => checking x 
        # --- pa => point for segment  
        # --- pb => point for segment  
        # --- pc => point for head  
        if pa[i] < pb[i]:
            # determine order for the segment points, 
            # before checking if head point is between them 
            if ((pa[i] <= pc[i]) and (pc[i] <= pb[i])):
                # head x value is between segment x values
                return True
        else:
            if ((pb[i] <= pc[i]) and (pc[i] <= pa[i])):
                # head x value is between segment x values
                return True
        return False
    @staticmethod
    def _compare_segments(head_heading, head, seg_heading, seg):
        """
        Given two segments (their headings and the x,y for each of their points), 
        determine if they segments intersect each other.
        """
        # debug("Segment Points: {} and {}".format(head, seg))
        A, B = head
        C, D = seg
        if head_heading == seg_heading:
            # pointed in the same or exact opposite direction
            # debug("same direction")
            if head_heading%2 == 0:
                # head is pointed north or south
                # debug("head is pointed north or south")
                if A[0] == C[0]:
                    # are colinear on the x axis
                    if (Snake._is_between(C, D, A, 1) or Snake._is_between(C, D, B, 1)):
                        # head point A.y is between segment points.y, or 
                        # head point B.y is between segment points.y;
                        # they overlap 
                        return True
                else:
                    # are parallel
                    pass
            else:
                # head is pointed east or west
                # debug("head is pointed east or west")
                if min(A[1],B[1]) == min(C[1],D[1]):
                    # debug("colinear")
                    # are colinear on the y axis
                    if (Snake._is_between(C, D, A, 0) or Snake._is_between(C, D, B, 0)):
                        # head point A.x is between segment points.x, or 
                        # head point B.x is between segment points.x;
                        # they overlap 
                        return True
                else:
                    # debug("parallel")
                    # are parallel
                    pass
        else:
            # segement and head are at 90 degree angles
            # debug("perpendicular")
            if head_heading%2 == 0:
                # debug("head is pointed north or south")
                # head is pointed north or south, 
                # head's points have the same x value
                if Snake._is_between(C, D, A, 0) and Snake._is_between(A, B, C, 1):
                    # head point A.x value is between segment points.x values, and
                    # segment point C.y value is between head points.y values
                    # debug("head point A.x value is between segment points.x values, and segment point C.y value is between head points.y values")
                    return True
            else:
                # debug("head is pointed east or west")
                # head is pointed east or west, 
                # segment is pointed north or south, 
                # segments's points have the same x value
                if Snake._is_between(A, B, C, 0) and Snake._is_between(C, D, A, 1):
                    # segment point C.x value is between head points.x values, and
                    # head point A.y value is between segment points.y values
                    # debug("segment point C.x value is between head points.x values, and head point A.y value is between segment points.y values")
                    return True
        # debug("no intersection found")
        return False
    @staticmethod
    def _extract(seg):
        """
        Given a segment, return its two points, and its heading.
        """
        if not hasattr(seg,"heading"):
            hdg = 0 if seg.h == max(seg.w, seg.h) else 1
        else:
            hdg = seg.heading
        if not hasattr(seg,"size"):
            half = seg.h if seg.h == min(seg.w, seg.h) else seg.w
        else:
            half = seg.size/2
        def get_half(hdg,df,delta):
            if delta:
                hf = -1*half
            else:
                hf = half
            if hdg == 0 and df == 0:
                # headed north, and getting x coord
                return delta+hf
            elif hdg == 1 and df == 1:
                # headed east, and getting y coord
                return delta+hf
            elif hdg == 2 and df == 0:
                # headed south, and getting x coord
                return delta+hf
            elif hdg == 3 and df == 1:
                # headed west, and getting y coord
                return delta+hf
            else:
                return delta+hf
        # get_half = lambda hdg,df: (half if hdg%2 == df else 0)
        A = [0,0]
        B = [0,0]
        A[0] = seg.x+get_half(hdg, 0, 0)
        A[1] = seg.y+get_half(hdg, 1, 0)
        B[0] = seg.x+get_half(hdg, 0, seg.w)
        B[1] = seg.y+get_half(hdg, 1, seg.h)
        return (A,B), hdg
    @staticmethod
    def intersects(segment_a,segment_b):
        """
        Given two segments, determine if they intersect each other.
        """
        try:
            # if isinstance(segment_a, Snake):
            #     segment_a = segment_a.segments
            # elif isinstance(segment_b, Snake):
            #     segment_b = segment_b.segments
            if isinstance(segment_a, Segment) and isinstance(segment_b, Segment):
                seg_a, seg_a_heading = Snake._extract(segment_a)
                seg_b, seg_b_heading = Snake._extract(segment_b)
                return Snake._compare_segments(seg_a_heading, seg_a, seg_b_heading, seg_b)
            else:
                if isinstance(segment_a, Snake):
                    segment_a = segment_a.segments
                else:
                    segment_a = [segment_a]
                if isinstance(segment_b, Snake):
                    segment_b = segment_b.segments
                else:
                    segment_b = [segment_b]
                result = True
                if len(segment_a) == 1:
                    seg_a, seg_a_heading = Snake._extract(segment_a[0])
                    for sb in segment_b:
                        seg_b, seg_b_heading = Snake._extract(sb)
                        result = (result and Snake._compare_segments(seg_a_heading, seg_a, seg_b_heading, seg_b))
                elif len(segment_b) == 1:
                    seg_b, seg_b_heading = Snake._extract(segment_b[0])
                    for sa in segment_a:
                        seg_a, seg_a_heading = Snake._extract(sa)
                        result = (result and Snake._compare_segments(seg_a_heading, seg_a, seg_b_heading, seg_b))
                else:
                    for sg_a in segment_a:
                        seg_a, seg_a_heading = Snake._extract(sg_a)
                        for sg_b in segment_b:
                            seg_b, seg_b_heading = Snake._extract(sg_b)
                            result = (result and Snake._compare_segments(seg_a_heading, seg_a, seg_b_heading, seg_b))
                return result
        except Exception as err:
            raise err
        return False
    @property
    def self_intersects(self):
        """
        Determine if the head intersects any of the other segments.
        """
        try:
            if len(self.segments) <= 1:
                return False
            head, head_heading = Snake._extract(self.head)
            for idx,seg in enumerate(self.segments[1:]):
                # debug("checking segment {}".format(idx))
                seg, seg_heading = Snake._extract(seg)
                if Snake._compare_segments(head_heading, head, seg_heading, seg):
                    # debug("{} {} {} {}".format(head_heading, head, seg_heading, seg))
                    return True
        except Exception as err:
            raise err
        return False

    def grow(self):
        """
        A condition has occured to cause the head to increment by one.
        """
        self.head.increment()

    def eat(self, fruit):
        """
        Ingest a fruit object, adding it's value to the Snake's belly.
        """
        self.belly = self.belly + fruit.value
        # debug("Belly has {} food".format(self.belly))

    def die(self):
        """
        The snake has died, and it's segments are now an empty list.
        """
        self.segments = []

    def move(self,direction):
        """
        Move the snake, interact with objects, 
        grow the head, and shrink the tail (if necessary).
        """
        def decrement():
            """
            We've moved, and need to subtract for the tail or belly.
            """
            if self.belly <= 0:
                # if no food in the belly
                self.tail.decrement()
                # decrease the tail
            else:
                # still have food in the belly, decrement it instead
                self.belly = self.belly - 1
            if self.tail.length <= 0:
                # if the tail segment no longer has a length, 
                self.segments.remove(self.tail)
                # remove the Segment from the list of segments that the snake is using
        if direction == self.heading:
            # still moving in the same heading?
            # debug("same direction")
            self.head.increment()
            # increase the head
            decrement()
        elif((direction+2)%4 == self.heading):
            # if we're moving in the direct opposite way of the original heading
            # debug("wrong direction")
            decrement()
            self.die()
            # die because the head turned 180 degrees and ran into the body
        else:
            # debug("new direction")
            # turning left or right of the original heading;
            # determine where the new segment needs to be
            if direction == 0:
                # changed to north
                if self.heading == 1:
                    # was east
                    origin = (self.head.x+self.head.w-self.size, self.head.y-self.size)
                else:
                    # was west
                    origin = (self.head.x, self.head.y-self.size)
            elif direction == 1:
                # changed to east
                if self.heading == 0:
                    # was north
                    origin = (self.head.x+self.size, self.head.y)
                else:
                    # was south
                    origin = (self.head.x+self.size, self.head.y+self.head.h-self.size)
            elif direction == 2:
                # changed to south
                if self.heading == 1:
                    # was east
                    origin = (self.head.x+self.head.w-self.size, self.head.y+self.size)
                else:
                    # was west
                    origin = (self.head.x, self.head.y+self.size)
            elif direction == 3:
                # changed to west
                if self.heading == 0:
                    # was north
                    origin = (self.head.x-self.size, self.head.y)
                else:
                    # was south
                    origin = (self.head.x-self.size, self.head.y+self.head.h-self.size)
            else:
                raise ValueError("Direction should be a number between 0-3, not {}".format(direction))
            self.heading = direction
            self.segments = [Segment([origin[0], origin[1], self.size], self.heading)]+self.segments
            # create a new segment to be the new head
            decrement()
        if self.is_alive and self.self_intersects:
            # determine if the snake currently is self intersecting
            self.die()

    def interact(self,other):
        """
        Determine what happens when the Snake interacts with certain object.
        """
        if isinstance(other, Obstacle):
            self.die()
        elif isinstance(other, Segment):
            self.die()
        elif isinstance(other, Snake):
            self.die()
        elif isinstance(other, Fruit):
            self.eat(other)
