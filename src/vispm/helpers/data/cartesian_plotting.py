
from dataclasses import dataclass
from typing import List, Callable

import numpy as np
from scipy import interpolate

@dataclass(frozen=True)
class CShift():
    """
    A shift vector to apply to a cartesian point.
    """
    x:float 
    y:float

    def inverse(self) -> 'CShift':
        """
        Returns the negation of this shift, or the additive inverse, as 
        a new shift. 
        """
        return CShift(
            self.x * -1,
            self.y * -1
        )
    
    def magnify(self, mag:float) -> 'CShift':
        """
        Returns a relative increase of this shift, as a new shift.
        """
        return CShift(
            self.x * mag,
            self.y * mag
        )
    
    def add(self, other:'CShift') -> 'CShift':
        """
        Returns an adjustment of this shift based on the given, as a new shift.
        """
        return CShift(
            self.x + other.x,
            self.y + other.y
        )
    
    def power(self) -> float:
        """
        Returns the power of the shift (vector length of longside of triangle)
        """
        return np.sqrt( np.power(self.x, 2) + np.power(self.y, 2))

@dataclass(frozen=True)
class CPoint():
    """
    A point in the cartesian plane.
    """

    x:float
    y:float

    def add_shift(self, shift:CShift) -> 'CPoint':
        """
        Returns this point adjusted by the shift, as a new point.
        """
        return CPoint(
            self.x + shift.x,
            self.y + shift.y
        )
    
    def difference(self, other:'CPoint') -> CShift:
        """
        Returns the cartesian difference between this point and another,
        returns the relative distance between x and y as a CShift.
        """
        return CShift(
            other.x - self.x,
            other.y - self.y
        )
    
    def shift_to_quad(self, quad:int) -> 'CPoint':
        """
        Returns this point but placed in another quad.
        """
        if quad == 1:
            return CPoint(
                np.abs(self.x), np.abs(self.y)
            )
        elif quad == 2:
            return CPoint(
                np.abs(self.x), np.abs(self.y) * -1
            ) 
        elif quad == 3:
            return CPoint(
                np.abs(self.x) * -1, np.abs(self.y) * -1
            )  
        elif quad == 4:
            return CPoint(
                np.abs(self.x) * -1, np.abs(self.y)
            )  
        else:
            raise ValueError("Expected quad to be between 1 and 4.")

@dataclass(frozen=True)
class CCircle():
    """
    A representation of the permeter of a circle on a cartesian plane.
    """
    center:CPoint
    radius:int

    def get_point_on_perimeter(self, degree:float) -> CPoint:
        """
        Finds a cartesian point on the perimeter of this circle.
        """
        radians = (degree * np.pi) / 180.0
        point = CPoint(
            self.center.x + (self.radius * np.cos(radians)), 
            self.center.y + (self.radius * np.sin(radians))
        ) 
        return point

    def find_equal_distance_points(self, lower:float, upper:float, 
                                   num:int,) -> List[CPoint]:
        """
        Finds [num] points on the perimeter of this circle between the
        given degrees that are equally distanced from each other.
        """
        degrees = np.linspace(lower, upper, num)
        return [
            self.get_point_on_perimeter(d)
            for d 
            in degrees
        ]
    
    def change_radius(self, increment:float) -> 'CCircle':
        """
        Returns a new cartesian circle with the same origin but with changed
        radius by the given increment.
        """
        radius = self.radius + increment
        if (radius < 0):
            raise ValueError(
                f"Cannot make a new circle with non-positive radius ::"+
                f" resultant radius was {radius}"
                )
        return CCircle(
            self.center,
            radius
        )


# helper functions
def interpolate_between(points:List[CPoint], )-> Callable:
        """
        Given a sequence of points, returns the linear interpolate between 
        them, returns a function on x to find y.
        """
        xers = [ p.x for p in points]
        yers = [ p.y for p in points ]
        return  interpolate.interp1d( 
                xers, yers
        )

def angle_from_origin(point:CPoint) -> float:
    """
    Computes the angle of a triangle from this point to the origin (0,0).
    Returns the angle in degrees.
    """
    # compute the length of the long side
    c = np.sqrt(
        np.power(point.y, 2) + np.power(point.x, 2) 
    )
    # compute the angle of <a
    return (np.arcsin(
        point.y / c
    ) * 180) / np.pi
