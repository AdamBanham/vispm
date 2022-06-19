
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

class EventLabelColourer(ColourImputer):
    """
    Colours event data by event label, will return the same colour for each label.\n
    Colour choice is decided by FIFO.
    """

    def __init__(self,cm=None) -> None:
        self._cm = CATEGORICAL
        self._loop_back_counter = 25
        self._seen_labels = dict()
        self._counter = 0

        if cm != None:
            self._cm = cm 
        if hasattr(self._cm, 'colors'):
            self._loop_back_counter = len(self._cm.colors)

    def __call__(self, seq_data:List[SequenceData], *args, **kwags) -> List[Tuple[float,float,float,float]]:
        colours = []
        for seq in seq_data:
            colours.append(self._get_colour(seq))
        return colours

    def _get_colour(self, data:SequenceData) -> Tuple[float,float,float,float]:
        if data.label in self._seen_labels.keys():
            return self._query_colour(self._seen_labels[data.label])
        else:
            self._seen_labels[data.label] = self._counter
            self._counter += 1
            return self._query_colour(self._seen_labels[data.label])

    def _query_colour(self, color_id:int) -> Tuple[float,float,float,float]:
        return self._cm( (color_id % self._loop_back_counter)/self._loop_back_counter)

    def _set_cm(self, cm):
        self._cm = cm
        if hasattr(self._cm, 'colors'):
            self._loop_back_counter = len(self._cm.colors)
        else: 
            self._loop_back_counter = 25


class TraceColourer(ColourImputer):
    """
    Colours event data by trace identifier or iteratively over traces.
    """

    _cm = get_cmap("Accent")

    def __init__(self,cm=None) -> None:
         if cm != None:
            self._cm = cm 

    def __call__(self, trace_id:int, *args, **kwags) -> Tuple[float,float,float,float]:
        color = self._cm(trace_id % len(self._cm.colors) / len(self._cm.colors))
        return color

    def _set_cm(self, cm):
        self._cm = cm