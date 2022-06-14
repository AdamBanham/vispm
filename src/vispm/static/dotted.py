from enum import Enum
from ..helpers.data.log_data import SequenceData
from ..helpers.metaclasses.pm4py import EventLog
from ..helpers.handlers.log_runners import SequenceDataExtractor
from ..helpers.imputers.colour_imputers import ColourImputer, TraceColourer

from typing import List,Tuple

from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure

class StaticDottedChartPresentor():

    _fig = None
    _ax = None 
    _extractor = SequenceDataExtractor()
    _sequences = None
    _log_name = "Unknown EventLog Name"
    _colour_schemer = None

    class EventColourScheme(ColourImputer,Enum):
        Trace:ColourImputer=TraceColourer()

        def __call__(self, *args, **kwags) -> Tuple[float,float,float,float]:
            return self.value(*args, **kwags)

        def _set_cm(self,cm):
            self.value._set_cm(cm)


    def __init__(self, event_log:EventLog,dpi=96,figsize=(12,8),event_colour_scheme:EventColourScheme=EventColourScheme.Trace) -> None:
        self._fig = plt.figure(figsize=figsize,dpi=dpi)
        self._ax = self._fig.subplots(1,1)
        self._sequences = self._extractor(event_log)
        self._colour_schemer = event_colour_scheme
        try :
            self._log_name = event_log.attributes['concept:name'] 
        except:
            print(f"[{self.__class__.__name__}] Cannot find concept:name in eventlog attributes.")

    def _create_dotted_frame(self,sequences:List[List[SequenceData]], ax:Axes) -> List[Artist]:
        all_artists = []
        for y,sequence in enumerate(sequences):
            color = self._colour_schemer(trace_id=y,seq_data=sequence)
            artists = ax.plot(
                [ seq.time for seq in sequence ],
                [ y for _ in  range(len(sequence)) ],
                "o",
                color=color,
                markerfacecolor="None",
                markersize = 1,
            )
            all_artists = all_artists + artists
        return all_artists

    def plot(self,show=True):
        self._create_dotted_frame(self._sequences,self._ax)
        #clean up plot
        self._ax.set_ylim([0,len(self._sequences)])
        min_x = self._sequences[0][0].time
        max_x = max([ seq[-1].time for seq in self._sequences])
        self._ax.set_xlim([min_x, max_x ])
        self._ax.set_yticks([])
        # add suitable xticks 
        diff_x = max_x - min_x 
        tickers = [ min_x] + \
                    [ min_x + (portion/100) * diff_x 
                        for portion in range(10,100,10) ] + \
                    [ max_x ]
        suffix, scale = self._find_scale(diff_x)
        self._ax.set_xticks(
            tickers
        )
        self._ax.set_xticklabels(
            [ 
                f"{(tick - min_x) / scale:.2f}{suffix}"
                for tick 
                in self._ax.get_xticks()
            ],
            rotation=-90
        )    
        #add labels
        self._ax.set_ylabel("Trace")
        self._ax.set_xlabel("Time")
        self._ax.set_title(f"Dotted Chart of\n {self._log_name}")
        self._ax.grid(True,color="grey",alpha=0.33)
        # show in interactive matplotlib setting
        if show:
            plt.show()

    def get_axes(self) -> Axes:
        return self._ax

    def get_figure(self) -> Figure:
        return self._fig 

    def _find_scale(self, seconds:float) -> Tuple[str,float]:
        if seconds < (60 * 3):
            return ("min" , 60)
        elif seconds < (  60 * 60 * 20):
            return ("hr", ( 60 * 60))
        elif seconds < (  60 * 60 * 24 * 183):
            return ("d", ( 60 * 60 * 24))
        else: 
            return ("yr", ( 60 * 60 * 24 * 365))