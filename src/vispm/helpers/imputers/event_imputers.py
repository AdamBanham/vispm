from copy import deepcopy
from string import ascii_uppercase

from typing import List, Tuple

from matplotlib.cm import get_cmap

class EventLabelImputer():

    _OPTIONS = deepcopy(ascii_uppercase)


    def __init__(self, name_keyyer=None, colour_keyyer=None) -> None:
        self._lookup = dict()
        self._num_lookup = dict()
        self._colour_lookup = dict()
        self._curr = 0
        self._num = 0
        self._length = 1
        self._prefix = ""
        self._prefex = []
        self._keyyer = {}
        self._colour_keyyer = {}
        self._colour_map = get_cmap("jet")
        self._colour_map_max = 25 
        if name_keyyer != None:
            self._keyyer = deepcopy(name_keyyer)
        if colour_keyyer != None:
            self._colour_keyyer = deepcopy(colour_keyyer)

    def _reset(self):
        self._lookup = dict()
        self._num_lookup = dict()
        self._curr = 0
        self._num = 0
        self._length = 1
        self._prefix = ""

    def set_labels(self, labels:List[str]) -> None:
        self._reset()
        for label in labels:
            self.add_label(label)

    def add_label(self, label:str) -> bool:
        if label in self._lookup.keys():
            return False
        else:
            if label in self._keyyer.keys():
                val = self._keyyer[label]
            else:
                print(f"{self._curr=} :: {len(self._OPTIONS)=}")
                val = self._prefix + self._OPTIONS[self._curr]
                while val in self._keyyer.values():
                    self._curr += 1
                    if (self._curr > len(self._OPTIONS)):
                        self._curr = 0
                    val = self._prefix + self._OPTIONS[self._curr]
            if label in self._colour_keyyer:
                cval = self._colour_keyyer[label]
            else :
                cnum = (self._num % self._colour_map_max) / self._colour_map_max
                cval = self._colour_map(cnum)
            self._lookup[label] = val 
            self._colour_lookup[label] = cval
            self._curr += 1
            if (self._curr >= len(self._OPTIONS)):
                # reset current pointer
                self._curr = 0
                # handle prefix selection
                if (len(self._prefex) < 1):
                    self._prefex.append(0)
                    self._prefix = self._OPTIONS[self._prefex[-1]]
                elif (self._prefex[-1]+1 < len(self._OPTIONS)):
                    self._prefex[-1] = self._prefex[-1] + 1 
                    self._prefix = self._prefix[:-1] + self._OPTIONS[self._prefex[-1]]
                else:
                    self._prefex.append(0)
                    self._prefix = self._prefix + self._OPTIONS[self._prefex[-1]]
            self._num_lookup[label] = self._num 
            self._num += 1
            return True

    def get_label_num(self, label:str) -> int:
        if label in self._num_lookup.keys():
            return self._num_lookup[label]
        else:
            raise Exception("Label has not been seen, unable to return alternative label.")

    def get_label(self, label:str) -> str:
        if label in self._lookup.keys():
            return self._lookup[label]
        else:
            raise Exception("Label has not been seen, unable to return alternative label.")
    
    def get_label_colour(self, label:str) -> Tuple[float,float,float,float]:
        """
        Gets the colour for this label
        """
        if label in self._colour_lookup.keys():
            return self._colour_lookup[label]
        else:
            raise Exception("Label has not been seen, unable to return alternative label.")

    def get_reverse_label_data(self, imputed_label:str) -> Tuple[str,int,object]:
        if imputed_label in self._lookup.values():
            for (key,val) in self._lookup.items():
                if val == imputed_label:
                    return key, self._num_lookup[key], self._colour_lookup[key]