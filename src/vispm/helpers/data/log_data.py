
from dataclasses import dataclass
@dataclass(frozen=True)
class SequenceData():
    time:float
    weekday:int
    monthday:int 
    hour:int
    label:str
    lifecycle:str
    resource:str