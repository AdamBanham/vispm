
from typing import Tuple,Any,List
from abc import ABC,abstractmethod

from vispm.helpers.colours.colourmaps import CATEGORICAL

from vispm.helpers.data.log_data import SequenceData

class ColourImputer(ABC):

    @abstractmethod
    def __call__(self, *args:Any, **kwds: Any) -> Any:
        pass

    @abstractmethod
    def _set_cm(self,cm):
        pass

class TraceColourer(ColourImputer):

    _cm = get_cmap("Accent")

    def __init__(self,cm=None) -> None:
         if cm != None:
            self._cm = cm 

    def __call__(self, trace_id:int, *args, **kwags) -> Tuple[float,float,float,float]:
        color = self._cm(trace_id % len(self._cm.colors) / len(self._cm.colors))
        return color

    def _set_cm(self, cm):
        self._cm = cm