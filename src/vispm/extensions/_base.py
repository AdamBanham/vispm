


from matplotlib.axes import Axes
from ..helpers.metaclasses.vispm import Presentor

from abc import abstractmethod
from typing import Any, Tuple
from enum import IntEnum, auto

class ChartExtension():
    """
    Meta class for all extensions to a presentor. Each sub-class must implement this interface to be used in the library.
    """

    class Direction(IntEnum):
        """
        The direction to place the extension from the responsible presentor.
        """
        NORTH=auto()
        EAST=auto()
        SOUTH=auto() 
        WEST=auto()

    class UpdateState(IntEnum):
        """
        The state in which a extension draw function is called by the presentor.
        """
        INIT=auto()
        DRAWING=auto()
        PLOTTING=auto()
        FINISHED=auto()

    def __init__(self, debug:bool=True) -> None:
        self._show_debug:bool = debug
        self._parent:Presentor = None

    def _debug(self, message:str, end:str="\n"):
        if self._show_debug:
            print(f"[{self.__class__.__name__}] {message} ",end=end)

    @abstractmethod
    def compatable_with(self, presentor:Presentor) -> bool:
        """
        Returns if this extension is comptable with a given presentor.
        """
        pass 

    @abstractmethod
    def get_update_state(self) -> UpdateState:
        """
        Return when to call draw on extension for the presentor.
        """
        pass

    @abstractmethod
    def set_axes(self, axes:Axes):
        """
        Tells the extension to use the given axes.
        """
        pass 
    
    @abstractmethod
    def get_size(self,) -> Tuple[float,float]:
        """
        Returns the size of the axes that this extension thinks it needs.
        """
        pass

    def get_height(self) -> float:
        """
        Returns the height of the axes that this extension thinks it needs.
        """
        return self.get_size()[1]

    def get_width(self) -> float:
        """
        Returns the width of the axes that this extension thinks it needs.
        """
        return self.get_size()[0]

    @abstractmethod
    def get_direction(self,) -> Direction:
        """
        Returns the direction to place the extension on from the responsible presentor.
        """
        pass
    
    @abstractmethod
    def draw(self, *args, **kwags) -> Axes:
        """
        Tells the extension to update its axes with the given data. 
        """
        pass

    def set_responsible_presentor(self, presentor:Presentor):
        if self._parent != None:
            self._parent = presentor
        else:
            raise Exception(f"This extension already has a presentor that is responsible for it :: {self._parent.__class__.__name__}")

    