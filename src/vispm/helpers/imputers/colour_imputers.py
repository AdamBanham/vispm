
from typing import Set, Tuple,Any,List
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

    @abstractmethod
    def get_seen_order(self) -> Set[Any]:
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
        self._seen_order = list()
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
            c = self._query_colour(self._counter)
            if c not in self._seen_order:
                self._seen_order.append(c)
            self._counter += 1
            return c

    def _query_colour(self, color_id:int) -> Tuple[float,float,float,float]:
        return self._cm( (color_id % self._loop_back_counter)/self._loop_back_counter)

    def _set_cm(self, cm):
        self._cm = cm
        if hasattr(self._cm, 'colors'):
            self._loop_back_counter = len(self._cm.colors)
        else: 
            self._loop_back_counter = 25

    def get_seen_order(self) -> List[Tuple[float,float,float,float]]:
        return self._seen_order


class TraceColourer(ColourImputer):
    """
    Colours event data by trace identifier or iteratively over traces.
    """


    def __init__(self,cm=None) -> None:
        self._cm = CATEGORICAL
        self._loop_back_counter = 25
        self._seen_order = list()
        
        if cm != None:
            self._cm = cm 
        if hasattr(self._cm, 'colors'):
            self._loop_back_counter = len(self._cm.colors)

    def __call__(self, trace_id:int, seq_data:List[SequenceData], *args, **kwags) -> Tuple[float,float,float,float]:
        color = self._cm( (trace_id % self._loop_back_counter)/self._loop_back_counter)
        if color not in self._seen_order:
            self._seen_order.append(color)
        return [color for _ in range(len(seq_data))]

    def _set_cm(self, cm):
        self._cm = cm
        if hasattr(self._cm, 'colors'):
            self._loop_back_counter = len(self._cm.colors)
        else: 
            self._loop_back_counter = 25

    def get_seen_order(self) -> List:
        return self._seen_order


class SequenceBreakerColourer(ColourImputer):
    """
    Changes the colourmap used for a given colourer, depending on time of the event being coloured. 
    """

    def __init__(self, type:ColourImputer=EventLabelColourer, colormaps=List, intervals=List[Tuple[float,float]]) -> None:
        self._type = type 
        assert len(colormaps) == len(intervals)
        self._intervals = intervals 
        self._colormaps = colormaps
        self._seen_order = list()

    def __call__(self, trace_id:int, seq_data:List[SequenceData], *args, **kwags) -> Tuple[float,float,float,float]:
        colours = []
        for seq in seq_data:
            time = seq.time
            for (min,max),map in zip(self._intervals,self._colormaps):
                if time >= min and time < max:
                    self._type._set_cm(map)
                    break
            c_return = self._type(trace_id=trace_id, seq_data=[seq], *args, **kwags)
            self._seen_order = self._seen_order + [c for c  in set(c_return) if c not in self._seen_order]
            if isinstance(c_return, list):
                colours = colours + c_return
            else:
                colours.append(c_return)
        return colours

    def _set_cm(self, cm):
        self._cm = cm

    def get_seen_order(self) -> List[Tuple[float,float,float,float]]:
        return self._seen_order