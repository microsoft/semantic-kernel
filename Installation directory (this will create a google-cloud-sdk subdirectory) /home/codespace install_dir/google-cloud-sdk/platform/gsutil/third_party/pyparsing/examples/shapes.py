# shapes.py
#
#   A sample program showing how parse actions can convert parsed
# strings into a data type or object.
#
# Copyright 2012, Paul T. McGuire
#

# define class hierarchy of Shape classes, with polymorphic area method
class Shape(object):
    def __init__(self, tokens):
        self.__dict__.update(tokens.asDict())

    def area(self):
        raise NotImplementedException()

    def __str__(self):
        return "<{0}>: {1}".format(self.__class__.__name__, self.__dict__)

class Square(Shape):
    def area(self):
        return self.side**2

class Rectangle(Shape):
    def area(self):
        return self.width * self.height

class Circle(Shape):
    def area(self):
        return 3.14159 * self.radius**2


from pyparsing import *

number = Regex(r'-?\d+(\.\d*)?').setParseAction(lambda t:float(t[0]))

# Shape expressions:
#   square : S <centerx> <centery> <side>
#   rectangle: R <centerx> <centery> <width> <height>
#   circle : C <centerx> <centery> <diameter>

squareDefn = "S" + number('centerx') + number('centery') + number('side')
rectDefn = "R" + number('centerx') + number('centery') + number('width') + number('height')
circleDefn = "C" + number('centerx') + number('centery') + number('diameter')

squareDefn.setParseAction(Square)
rectDefn.setParseAction(Rectangle)

def computeRadius(tokens):
    tokens['radius'] = tokens.diameter/2.0
circleDefn.setParseAction(computeRadius, Circle)

shapeExpr = squareDefn | rectDefn | circleDefn

tests = """\
C 0 0 100
R 10 10 20 50
S -1 5 10""".splitlines()

for t in tests:
    shape = shapeExpr.parseString(t)[0]
    print(shape)
    print("Area:", shape.area())
    print()
