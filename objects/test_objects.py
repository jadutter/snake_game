#!/usr/bin/python3.7
import unittest
import contextlib
with contextlib.redirect_stdout(None):
    from pygame import Rect
del contextlib
from .fruit import Fruit 
from .segment import Segment 
from .snake import Snake
from .obstacle import Obstacle

class TestFruitObject(unittest.TestCase):
    """
    Test that the Fruit object behaves as expected.
    """
    def test_init(self):
        """
        Test if we can create a fruit object.
        """
        position = [0, 2]
        size = 5
        apple_value = 10
        orange_value = 20
        name = "apple"
        dimensions = [ position[0], position[1], size, size ]

        apple = Fruit(name, dimensions, apple_value)

        self.assertEqual(position[0], apple.x)
        self.assertEqual(position[1], apple.y)
        self.assertEqual(name, apple.name)
        self.assertEqual([ position[0], position[1], size ], apple.dimensions)
        self.assertEqual(apple_value, apple.value)

        apple_drawn = apple.render()
        self.assertIsInstance( apple_drawn, Rect)
        
        orange = Fruit("orange", [ position[0], position[1], size ], 20)
        self.assertEqual(20, orange.value)

class TestSegmentObject(unittest.TestCase):
    """
    Test that the Segment object behaves as expected.
    """
    def test_init(self):
        """
        Test if we can create a Segment object.
        """
        position = [0, 50]
        size = 5
        length = 25
        dimensions = [ position[0], position[1], length, size ]
        heading = 1
        # pointed EAST
        seg = Segment(dimensions, heading)
        self.assertEqual(seg.heading, seg.head_heading)
        self.assertEqual(seg.heading, heading)
        self.assertEqual(3, seg.tail_heading)
        self.assertEqual(seg.length, length)
        seg_drawn = seg.render()
        self.assertIsInstance( seg_drawn, Rect)

class TestObstacleObject(unittest.TestCase):
    """
    Test that the Obstacle object behaves as expected.
    """
    def test_init(self):
        """
        Test if we can create a Obstacle object.
        """
        position = [0, 0]
        size = 5
        length = 100
        ns_dimensions = [ position[0], position[1], size, length ]
        ew_dimensions = [ position[0], position[1], length, size ]

        ns_wall = Obstacle(ns_dimensions)
        ew_wall = Obstacle(ew_dimensions)

        self.assertEqual(ns_wall.heading, 0)
        self.assertEqual(ns_wall.x, position[0])
        self.assertEqual(ns_wall.y, position[1])
        self.assertEqual(ns_wall.w, size)
        self.assertEqual(ns_wall.h, length)

        self.assertEqual(ew_wall.heading, 1)
        self.assertEqual(ew_wall.x, position[0])
        self.assertEqual(ew_wall.y, position[1])
        self.assertEqual(ew_wall.w, length)
        self.assertEqual(ew_wall.h, size)

        ns_wall_drawn = ns_wall.render()
        self.assertIsInstance( ns_wall_drawn, Rect)
        ew_wall_drawn = ew_wall.render()
        self.assertIsInstance( ew_wall_drawn, Rect)


class TestSnakeObject(unittest.TestCase):
    """
    Test that the Snake object behaves as expected.
    """
    def test_init(self):
        """
        Test if we can create a Snake object.
        """
        position = [0, 48]
        size = 8
        length = 24
        dimensions = [ position[0], position[1], length, size ]
        heading = 3
        # pointed WEST
        ouroboros = Snake(dimensions, heading)
        self.assertEqual(ouroboros.heading, heading)
        self.assertEqual(len(ouroboros.segments), 1)
        self.assertEqual(ouroboros.length, length)
        self.assertEqual(ouroboros.head.length, length)
        snake_drawn = ouroboros.render()
        self.assertIsInstance( snake_drawn, list)
        self.assertIsInstance( snake_drawn[0], Rect)
    def test_self_intersection(self):
        position = [0, 48]
        size = 8
        length = 24
        dimensions = [ position[0], position[1], length, size ]
        heading = 3
        ouroboros = Snake(dimensions, heading)
        head = Segment([28, 0, 7, 56], 0)
        tail = Segment([0, 28, 56, 7], 1)
        ouroboros.segments = [head, tail]
        self.assertTrue(ouroboros.self_intersects)

class TestSnakeMethods(unittest.TestCase):
    """
    Test that the Snake object behaves as expected.
    """

    def setUp(self):
        position = [42, 14]
        size = 7
        length = 28
        dimensions = [ position[0], position[1], size, length ]
        heading = 0
        # pointed North
        self.snake = Snake(dimensions, heading)
    def test_move_north(self):
        """
        Test if we can move north
        """
        self.assertEqual(len(self.snake.segments), 1)
        self.snake.move(0)
        self.assertEqual(len(self.snake.segments), 1)
        self.assertEqual(self.snake.length, self.snake.head.length)

    def test_move_east(self):
        """
        Test if we can move east
        """
        self.assertEqual(len(self.snake.segments), 1)
        self.snake.move(1)
        self.assertEqual(len(self.snake.segments), 2)
        self.assertEqual(self.snake.size, self.snake.head.length)
        self.assertEqual(self.snake.length-self.snake.size, self.snake.tail.length)

    def test_move_south(self):
        """
        Test if we can move south
        """
        self.assertEqual(len(self.snake.segments), 1)
        self.snake.move(2)
        self.assertEqual(len(self.snake.segments), 0)

    def test_move_west(self):
        """
        Test if we can move west
        """
        self.assertEqual(len(self.snake.segments), 1)
        self.snake.move(3)
        self.assertEqual(len(self.snake.segments), 2)
        self.assertEqual(self.snake.size, self.snake.head.length)
        self.assertEqual(self.snake.length-self.snake.size, self.snake.tail.length)

    def test_move_and_eat(self):
        """
        Test if we can move west,
        eat an apple,
        and move south
        """
        snake_head = self.snake.head
        apple = Fruit("apple", [ snake_head.x-snake_head.size, snake_head.y, snake_head.size ], 7)
        self.assertEqual(len(self.snake.segments), 1)

        self.assertFalse(Snake.intersects(snake_head, apple))
        self.snake.move(3)
        # move west, into the apple
        self.assertEqual(len(self.snake.segments), 2)
        self.assertEqual(self.snake.size, self.snake.head.length)
        self.assertEqual(self.snake.length-self.snake.size, self.snake.tail.length)
        # we have the expected length in the right segments
        snake_head = self.snake.head
        # update our local variable
        self.assertTrue(Snake.intersects(snake_head,apple))
        # The snake is now intersecting the apple
        tail_before = self.snake.tail.length
        # store the length of the tail before we interact with the apple
        self.snake.interact(apple)
        # Tell the snake to interact with the apple
        self.assertEqual(self.snake.belly, 7)
        self.snake.move(2)
        # move south, creating a counter-clockwise U shape
        self.assertEqual(len(self.snake.segments), 3)
        self.assertEqual(self.snake.size, self.snake.head.length)
        self.assertEqual(self.snake.size, self.snake.segments[1].length)
        self.assertEqual(self.snake.length-self.snake.size*2, self.snake.tail.length)
        # the tail is equal to the full length, minus two sizes; one for each newly created segment
        self.assertEqual(tail_before, self.snake.tail.length)
        self.assertEqual(self.snake.belly, 6)
        # we moved, and decremented the belly instead of the tail length
        self.assertTrue(self.snake.is_alive)
        self.snake.move(0)
        # move north, just to prove the snake can die
        self.assertFalse(self.snake.is_alive)
        self.assertEqual(len(self.snake.segments), 0)
        self.assertEqual(self.snake.belly, 5)

    def test_move_into_wall(self):
        """
        Test if we can move west,
        into a wall,
        and die
        """
        snake_head = self.snake.head
        wall = Obstacle([ snake_head.x-snake_head.size, 0, snake_head.size, 700 ])
        self.assertEqual(len(self.snake.segments), 1)
        self.assertFalse(Snake.intersects(snake_head, wall))
        self.assertTrue(self.snake.is_alive)
        self.snake.move(3)
        # move west, into the wall
        self.assertEqual(len(self.snake.segments), 2)
        self.assertEqual(self.snake.size, self.snake.head.length)
        self.assertEqual(self.snake.length-self.snake.size, self.snake.tail.length)
        # we have the expected length in the right segments
        snake_head = self.snake.head
        # update our local variable
        self.assertTrue(Snake.intersects(snake_head,wall))
        # The snake is now intersecting the wall
        self.assertTrue(self.snake.is_alive)
        # haven't interacted yet, so its still alive
        self.snake.interact(wall)
        # Tell the snake to interact with the wall
        self.assertFalse(self.snake.is_alive)
        self.assertEqual(len(self.snake.segments), 0)

    def test_move_into_snake(self):
        """
        Test if we can move west,
        into another snake,
        and die
        """
        snake_head = self.snake.head
        ouroboros = Snake([ snake_head.x-snake_head.size, 0, snake_head.size, 700 ], 2)
        self.assertEqual(len(self.snake.segments), 1)
        self.assertEqual(len(ouroboros.segments), 1)
        self.assertTrue(ouroboros.is_alive)
        self.assertTrue(self.snake.is_alive)

        self.assertFalse(Snake.intersects(self.snake, ouroboros))
        self.snake.move(3)
        # move west, into the other snake

        snake_head = self.snake.head
        # update our local variable
        self.assertEqual(len(self.snake.segments), 2)
        self.assertEqual(len(ouroboros.segments), 1)
        self.assertEqual(self.snake.size, snake_head.length)
        self.assertEqual(ouroboros.head.length, ouroboros.length)
        self.assertEqual(self.snake.length-self.snake.size, self.snake.tail.length)
        # we have the expected length in the right segments

        self.assertTrue(Snake.intersects(snake_head,ouroboros))
        # The snake is now intersecting the other snake
        self.assertTrue(self.snake.is_alive)
        # haven't interacted yet, so its still alive
        self.snake.interact(ouroboros)
        # Tell the snake to interact with the other snake
        self.assertFalse(self.snake.is_alive)
        self.assertEqual(len(self.snake.segments), 0)

if __name__ == '__main__':
    unittest.main()