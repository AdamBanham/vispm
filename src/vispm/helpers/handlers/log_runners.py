
from ..data.log_data import SequenceData
from ..metaclasses.pm4py import EventLog,Trace

from typing import List,Tuple

class SequenceDataExtractor():
    """
    Given a event log, this class extracts the minimum amount of data needed for visualisation. Should be used a one-shot.\n
    Assumptions:\n
    \tThe given event log has been sorted by starting event timestamp.
    """

    TIME_ATTR = "time:timestamp"
    LABEL_ATTR = "concept:name"
    LIFE_ATTR = "lifecycle:transition"

    def __init__(self) -> None:
        pass 

    def __call__(self, event_log:EventLog) -> List[SequenceData]:
        """Begins extracting SequenceData from an EventLog"""
        return self._convert_log(event_log)

    def _convert_trace(self,trace:Trace, startingTime:float) -> List[SequenceData]:
        timepoints = [] 
        for event in trace:
            time = event[self.TIME_ATTR].timestamp() - startingTime
            weekday = event[self.TIME_ATTR].weekday()
            monthday = event[self.TIME_ATTR].day
            label = event[self.LABEL_ATTR]
            lifecycle = event[self.LIFE_ATTR]
            data = SequenceData(time,weekday,monthday,label,lifecycle)
            timepoints.append(data)
        timepoints = sorted(timepoints, key=lambda x: x.time)
        return timepoints

    def _convert_log(self,log:EventLog) -> List[List[SequenceData]]:
        log_sequences = []
        startingTime = log[0][0][self.TIME_ATTR].timestamp()
        for trace in log:
            log_sequences.append(self._convert_trace(trace,startingTime))
        log_sequences = sorted(log_sequences,key=lambda x: x[0].time)
        return log_sequences