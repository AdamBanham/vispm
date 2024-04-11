
from dataclasses import dataclass

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
