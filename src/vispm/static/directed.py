from ._base import StaticPresentor
from ..extensions._base import ChartExtension
from ..helpers.imputers.event_imputers import EventLabelImputer

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from scipy import interpolate

import numpy as np


from typing import Tuple

PLOT_STATE = ChartExtension.UpdateState

class DirectlyFollowsPresentor(StaticPresentor):
    """
    TODO
    """

    from pmkoalas.complex import ComplexEventLog
    from pmkoalas.directly import FollowLanguage

    _fig = None
    _ax = None 
    _log_name = "Unknown EventLog"
    _followers:FollowLanguage = None
    _colour_schemer = None
    _show_debug = True

    def __init__(self, event_log:ComplexEventLog, 
                 dpi:int=96, figsize:Tuple[float,float]=(8,8), ax:Axes=None,
                 debug: bool = True) -> None:
        super().__init__(debug)
        # so turns out its painful to not show a figure and still show it when needed.
        reset_it = plt.isinteractive()
        if reset_it:
            plt.ioff()
        if ax == None:
            self._fig = plt.figure(figsize=figsize,dpi=dpi,constrained_layout=True)
            self._ax = self._fig.subplots(1,1)
        else:
            self._fig = ax.get_figure()
            self._ax = ax
        if reset_it:
            plt.ion()
        #try to find event log name in attributes
        try:
            from pmkoalas.complex import ComplexEventLog
            if (isinstance(event_log, ComplexEventLog)):
                self._log_name = event_log.name
            else:
                raise ValueError("not a pmkoalas data structure")
        except:
            try :
                self._log_name = event_log.attributes['concept:name'] 
            except:
                self._debug("Cannot find concept:name in eventlog attributes.")
        # try to build follows languages
        if (isinstance(event_log, ComplexEventLog)):
            self._followers = event_log.simplify().directly_follow_relations()
            self._acts = event_log.seen_activities()
        else:
            raise ValueError("Directly follows construction not implemented for"
                             +" logs of ::" + type(event_log))


    def plot(self) -> Figure:
        self._ax = self._adjust_for_extensions(self._fig)
        self.update_plot_state(PLOT_STATE.DRAWING)
        self.update_extensions(followers=self._followers) 
        self._create_dfg_frame(self._followers,self._ax)
        self._debug("Cleaning up plot...")
        self._ax.set_xlim(0, 10)
        self._ax.set_ylim(0, -10)

    def _create_dfg_frame(self, followers:FollowLanguage, ax:Axes):
        imputer = EventLabelImputer(
            type=EventLabelImputer.IMPUTER_TYPE.find("shorter")
        )
        for act in self._acts:
            imputer.add_label(act)
        starting_acts = [
            start.right()
            for start 
            in followers.starts()
        ]
        ending_acts = [ 
            end.left()
            for end 
            in followers.ends()
        ]
        # work out starting spline
        A = len(starting_acts)
        r = 0.25
        Sx = 0.0625 * (5.65685 * (A+2) + 8 )
        SL = np.sqrt( 
            Sx ** 2 + Sx ** 2
        )
        Sy = Sx 
        shift = np.sqrt( 
            ((SL / 4) ** 2) / 2.0
        )
        # create spline point for starting pairs
        x_curr = (2 * r) + Sx
        y_curr = (2 * r) * -1
        points = [
            ((2 * r) + Sx, (2 * r) * -1)
        ]
        for adj in range(3):
            if adj % 2 == 1:
                extra = 2 * r * 0.5 + (A / 2.0) * r
            else:
                extra = r
            x_curr = x_curr - shift 
            y_curr = y_curr + (shift * -1) 
            points.append((x_curr - extra,y_curr + extra))
        points.append(((2 * r), ((2 * r) + Sx) * -1))
        # interplote points 
        xers = [ x for (x,y) in points ]
        yers = [ y for (x,y) in points ]
        xspace = np.linspace(0, 1, A+2)
        tck, _ = interpolate.splprep([xers, yers], s=5)
        starting_circle_pos = interpolate.splev(xspace, tck, der=0)
        # plot starting circles
        curr = 1
        for act in starting_acts:
            x = starting_circle_pos[0][curr]
            y = starting_circle_pos[1][curr]
            sact = imputer.get_label(act)
            circle =  Circle((x,y), r, color="green")
            ax.add_patch(circle)
            ax.text(x - (r/2), y, sact, fontdict={"fontsize" : 5})
            # add incoming arrow
            x2 = x - (2 * r)
            y2 = y + (2 * r)
            f_lin =  interpolate.interp1d( 
                [x2, x], [y2, y])
            xpsace = np.linspace(x2,x - r * 0.5,100)
            lines = ax.plot( 
                xpsace,
                f_lin(xpsace),
                'black'
            )
            self._add_arrow(lines[0], xpsace[98])
            curr += 1
        # # randomally draw a circle for each 
        # min_x = 0 
        # max_x = 10
        # min_y = 0
        # max_y = 10
        # # find some points
        # x_vals = min_x + np.random.rand(len(self._acts)) * (max_x - min_x)
        # y_vals = min_y + np.random.rand(len(self._acts)) * (max_y - min_y)
        # # drawing
        
        # for act, x, y in zip(self._acts, x_vals, y_vals):
        #     if act in starting_acts:
        #         color = "green"
        #     elif act in ending_acts:
        #         color = "red"
        #     else:
        #         color = "gray"
        #     act = imputer.get_label(act)
        #     circle =  Circle((x,y), 0.25, color=color)
        #     ax.add_patch(circle)
        #     ax.text(x - (r/2), y, act, fontdict={"fontsize" : 5})
        # # add spline between cords
        # for x1, y1, x4, y4 in zip(x_vals[:-1], y_vals[:-1], x_vals[1:], y_vals[1:]):
        #     dist_x = np.abs(x4 - x1) / 4.0
        #     dist_y = np.abs(y4 - y1) / 4.0
        #     x2 = x1 + dist_x if x1 < x4 else x1 - dist_x
        #     y2 = y1 + dist_y if y1 < y4 else y1 - dist_y 
        #     y2 += np.random.random()
        #     x3 = x1 + dist_x * 3 if x1 < x4 else x1 - dist_x * 3
        #     y3 = y1 + dist_y * 3 if y1 < y4 else y1 - dist_y * 3
        #     y3 += np.random.random()
        #     vals = np.array( [[x1,y1],[x2,y2],[x3,y3], [x4,y4]])
        #     xers = vals[:,0]
        #     yers = vals[:,1]
        #     f_cubic = interpolate.interp1d( 
        #         xers, yers, kind='cubic')
        #     if x1 < x4:
        #         xspace = np.linspace( x1, x4, 100 )
        #     else:
        #         xspace = np.linspace( x4, x1, 100)
        #     line = ax.plot(xspace, f_cubic(xspace), "green")
        #     self._add_arrow(line[0], xspace[95], color='black')


    def get_axes(self) -> Axes:
        return self._ax 

    def get_figure(self) -> Figure:
        return self._fig 
    
    def _add_arrow(self, line, position=None, direction='right', size=15, color=None):
        """
        add an arrow to a line.

        line:       Line2D object
        position:   x-position of the arrow. If None, mean of xdata is taken
        direction:  'left' or 'right'
        size:       size of the arrow in fontsize points
        color:      if None, line color is taken.
        """
        if color is None:
            color = line.get_color()

        xdata = line.get_xdata()
        ydata = line.get_ydata()

        if position is None:
            position = xdata.mean()
        # find closest index
        start_ind = np.argmin(np.absolute(xdata - position))
        if direction == 'right':
            end_ind = start_ind + 1
        else:
            end_ind = start_ind - 1

        line.axes.annotate('',
            xytext=(xdata[start_ind], ydata[start_ind]),
            xy=(xdata[end_ind], ydata[end_ind]),
            arrowprops=dict(arrowstyle="->", color=color),
            size=size
        )

    

