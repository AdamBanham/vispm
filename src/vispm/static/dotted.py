from enum import Enum
from ..helpers.data.log_data import SequenceData
from ..helpers.metaclasses.pm4py import EventLog
from ..helpers.handlers.log_runners import SequenceDataExtractor
from ..helpers.imputers.colour_imputers import ColourImputer, TraceColourer, EventLabelColourer
from ..helpers.colours.colourmaps import CATEGORICAL
from ..helpers.iters.tools import iter_chunker

from typing import List,Tuple
from math import ceil, floor

from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap

class StaticDottedChartPresentor():

    _fig = None
    _ax = None 
    _extractor = SequenceDataExtractor()
    _sequences = None
    _log_name = "Unknown EventLog"
    _colour_schemer = None
    _show_debug = True
    _marksize =0.5

    class EventColourScheme(Enum):
        """
        Parameter Enum for StaticDottedChartPresentor. Sets how events are coloured when plotting.
        """
        Trace:ColourImputer=TraceColourer
        EventLabel:ColourImputer=EventLabelColourer    

        def __call__(self,*args, **kwags) -> ColourImputer:
            return self.value(*args,**kwags)


    def __init__(self, event_log:EventLog, dpi:int=96, figsize:Tuple[float,float]=(8,8), ax:Axes=None,
        markersize:float=0.5, starting_time=None,
        colormap:ListedColormap=CATEGORICAL,debug:bool=True,
        event_colour_scheme:EventColourScheme=EventColourScheme.Trace) -> None:
        # set default values
        self._show_debug = debug
        self._marksize = markersize
        # so turns out its painful to not show a figure and still show it when needed.
        reset_it = plt.isinteractive()
        if reset_it:
            plt.ioff()
        if ax == None:
            self._fig = plt.figure(figsize=figsize,dpi=dpi,)
            self._ax = self._fig.subplots(1,1)
        else:
            self._fig = ax.get_figure()
            self._ax = ax
        if reset_it:
            plt.ion()
        # process event data
        self._debug("Processing event data...")
        self._sequences = self._extractor(event_log, start_time=starting_time)
        if isinstance(event_colour_scheme, self.EventColourScheme):
            self._colour_schemer = event_colour_scheme(cm=colormap)
        else:
            self._colour_schemer = event_colour_scheme
        try :
            self._log_name = event_log.attributes['concept:name'] 
        except:
            self._debug("Cannot find concept:name in eventlog attributes.")
        self._debug("Ready to plot...")

    def _debug(self, message:str, end="\n"):
        if self._show_debug:
            print(f"[{self.__class__.__name__}] {message} ",end=end)

    def _create_dotted_frame(self,sequences:List[List[SequenceData]], ax:Axes) -> List[Artist]:
        self._debug("Compiling plot data...             ", end="\r")
        all_artists = []
        x_data = [  0.0 for trace in sequences for ev in trace ]
        y_data = [ 0.0 for trace in sequences for ev in trace]
        colors = [ (0.0,0.0,0.0,0.0) for trace in sequences for ev in trace ]
        #collect markers
        total_seqs = len(sequences)
        percentile = ceil(total_seqs * 0.01)
        start_idx = 0
        for y,sequence in enumerate(sequences):
            end_idx = start_idx + len(sequence)
            new_colors = self._colour_schemer(trace_id=y,seq_data=sequence)
            colors[start_idx:end_idx] = new_colors
            x_data[start_idx:end_idx] = [ seq.time for seq in sequence ]
            y_data[start_idx:end_idx] = [ y for _ in  range(len(sequence)) ]
            if y > 0 and y % percentile == 0:
                self._debug(f" {(y/total_seqs)*100:03.1f}% compiled...        ",end="\r")
            start_idx = end_idx
        # plot markers
        self._debug("Compiling finished...        ")
        self._debug("Plotting data...")
        for xers,yers,cers in zip(iter_chunker(x_data,500),iter_chunker(y_data,500),iter_chunker(colors,500)):
            artists = ax.scatter(
                x=xers,
                y=yers,
                s = self._marksize,
                color=cers,
                alpha=0.66
            )
            all_artists.append(artists)
        return all_artists

    def plot(self) -> Figure:
        self._create_dotted_frame(self._sequences,self._ax)
        self._debug("Cleaning up plot...")
        #clean up plot
        self._ax.set_ylim([0,len(self._sequences)])
        min_x = self._sequences[0][0].time
        max_x = max([ seq[-1].time for seq in self._sequences if len(seq) > 0])
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
        self._debug("Plot is ready to show...")
        return self._fig

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