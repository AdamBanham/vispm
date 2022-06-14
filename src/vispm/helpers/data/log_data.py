
from dataclasses import dataclass
@dataclass(frozen=True)
class SequenceData():
    time:float
    weekday:float
    monthday:int 
    label:str
    lifecycle:str