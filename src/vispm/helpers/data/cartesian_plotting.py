
from dataclasses import dataclass
from typing import List

import numpy as np

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
    
    def difference(self, other:'CPoint') -> float:
        """
        Returns the cartesian difference between this point and another,
        returns the absolute difference.
        """
        return np.sqrt(
            np.power( np.abs(self.x - other.x), 2)
            +
            np.power( np.abs(self.y - other.y), 2)
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
    centre:CPoint
    radius:int

    def get_point_on_perimeter(self, degree:float) -> CPoint:
        """
        Finds a cartesian point on the perimeter of this circle.
        Using the general form, where given the orgin (x,y) and radius r,
        where does the top point (x,y+r) move to after a rotation of D,
        the rotated point (u,v) can be found using:
        u = x cos(D) + (y+r) sin(D);
        v = -x sin(D) + (y+r) cos(D);
        """
        # first shift the orgin to the top
        rotation = self.centre.add_shift(
            CPoint(0, self.radius)
        )
        #
        radians = (degree * np.pi) / 180.0
        # then compute x-axis and y-axis
        u = rotation.x * np.cos(radians) + rotation.y * np.sin(radians)
        v = -1 * rotation.x * np.sin(radians) + rotation.y * np.cos(radians)
        return CPoint(
            u, v
        ) 

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
            self.centre,
            radius
        )
