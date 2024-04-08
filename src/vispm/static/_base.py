
from ..helpers.metaclasses.vispm import Presentor
from ..extensions._base import ChartExtension

from abc import abstractmethod
from typing import Any, List

from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec

class StaticPresentor(Presentor):
    """
    Meta class for any static presentor. Each sub-class must implement this 
    interface to be used in the library.
    """

    def __init__(self, debug:bool=True) -> None:
        self._show_debug = debug
        self._extensions:List[ChartExtension] = []
        self._plot_state:ChartExtension.UpdateState= ChartExtension.UpdateState.INIT

    def _debug(self, message:str, end:str="\n"):
        if self._show_debug:
            print(f"[{self.__class__.__name__}] {message} ",end=end)

    @abstractmethod
    def plot(self) -> Figure:
        pass 

    @abstractmethod
    def get_axes(self) -> Axes:
        pass 

    @abstractmethod
    def get_figure(self) -> Figure:
        pass 

    def _adjust_for_extensions(self, fig:Figure) -> Axes:
        # work out gridspec 
        norths = [ ext for ext in self._extensions if ext.get_direction() == ChartExtension.Direction.NORTH ]
        easts = [ ext for ext in self._extensions if ext.get_direction() == ChartExtension.Direction.EAST ]
        souths = [ ext for ext in self._extensions if ext.get_direction() == ChartExtension.Direction.SOUTH ]
        wests = [ ext for ext in self._extensions if ext.get_direction() == ChartExtension.Direction.WEST ]
        # height of extensions
        rows = len(norths) + 1 + len(souths)
        cols = len(easts) + 1 + len(wests)
        if rows == 1 and cols == 1:
            return fig.get_axes()[0]
        else:
            self._fig.clear()
            # reshape fig to suit gridspec
            main_x, main_y = fig.get_size_inches()
            x_ratio = sum([ext.get_width() for ext in easts] + [main_x] + [ext.get_width() for ext in wests])
            y_ratio = sum([ ext.get_height() for ext in norths ] + [main_y] + [ ext.get_height() for ext in souths ])
            self._fig.set_size_inches(x_ratio, y_ratio)
            w_ratios = [ ext.get_width()/x_ratio for ext in easts ] + [main_x/x_ratio] + [ ext.get_width()/x_ratio for ext in wests ]
            h_ratios = [ ext.get_height()/y_ratio for ext in norths ] + [main_y/y_ratio] + [ ext.get_height()/y_ratio for ext in souths ]
            gs = GridSpec(nrows=rows,ncols=cols, width_ratios=w_ratios, height_ratios=h_ratios, figure=fig)

            # give extensions an axes
            center_col = len(wests)
            center_row = len(norths)
            counter = 0 
            for ext in norths:
                    ext.set_axes(fig.add_subplot(gs[counter, center_col]))
                    counter+= 1
            counter += 1
            for ext in souths:
                ext.set_axes(fig.add_subplot(gs[counter, center_col]))
                counter+= 1
            
            counter = 0 
            for ext in wests:
                ext.set_axes(fig.add_subplot(gs[center_row,counter]))
                counter+= 1
            counter += 1
            for ext in easts:
                ext.set_axes(fig.add_subplot(gs[center_row,counter]))
                counter+= 1

            return fig.add_subplot(gs[len(norths),len(wests)])

    def update_extensions(self, *args, **kwags):
        for ext in self._extensions:
            if ext.get_update_state() == self._plot_state:
                ext.draw(*args, **kwags)

    def update_plot_state(self, state:ChartExtension.UpdateState):
        self._plot_state = state

    def add_extension(self, extension:ChartExtension) -> bool:
        if extension.compatable_with(self):
            self._debug(f"Added extension : {extension.__class__.__name__}")
            self._extensions.append(extension)
            return True 
        else:
            return False 
    
    def remove_extension(self, extension:ChartExtension) -> bool:
        if extension in self._extensions:
            self._extensions.remove(extension) 
            return True 
        else:
            return False