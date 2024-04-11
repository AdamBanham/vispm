from ._base import StaticPresentor
from ..extensions._base import ChartExtension
from ..helpers.imputers.event_imputers import EventLabelImputer
from ..helpers.data.cartesian_plotting import CPoint,CShift

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle,Patch

from scipy import interpolate

import numpy as np


from typing import Tuple, List, Callable, Union, Literal
from random import choice

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
        xers = [ pos.x for pos in self._pos_store.values()]
        max_x = np.max(xers) + np.max(xers) * 0.03
        self._ax.set_xlim(0, max_x)
        self._ax.set_ylim(0, -max_x)
        self._ax.grid()
        self._debug("Cleaning up ready to show...")

    def _create_dfg_frame(self, followers:FollowLanguage, ax:Axes):
        # handle labels
        imputer = EventLabelImputer(
            type=EventLabelImputer.IMPUTER_TYPE.find("shorter")
        )
        for act in self._acts:
            imputer.add_label(act)
        starters = [
            start
            for start 
            in followers.starts()
        ]
        enders = [ 
            end
            for end 
            in followers.ends()
        ]
        # work out starting spline
        r = .25
        # find a nice set of points on curve  
        starting = self._find_cubic_curve(
            r,
            len(starters),
            CShift( 0, 0),
        )
        # plot starting dfg states
        s_arrow_shift = CShift(
            (2 * r) * - 1,
            (2 * r)
        )
        e_arrow_shift = CShift(
            (r * 0.5) * -1,
            (r * 0.5),
        )
        # store dfg positions 
        self._pos_store = {}
        for start,point in zip(starters,starting[1:-1]):
            # plot starting dfg state
            self._pos_store[start] = point
            self._plot_dfg_state(
                point,
                r,
                imputer.get_label(start.right()),
                "green"
            )
            # add incoming arrow
            start_point = point.add_shift(s_arrow_shift)
            end_point = point.add_shift(e_arrow_shift)
            self._create_arrow(start_point, end_point, 98)
        # # plot the inbetweens of the dfg
        # for pair in followers.__iter__():
        #     if pair not in followers.starts() and pair not in followers.ends():
        #         point = CPoint( 
        #             2 + np.random.rand() * (7 - 2),
        #             -1 * (2 + np.random.rand() * (7 - 2))
        #         )
        #         while self._overlaps(point, 2 * r) and \
        #             self._overlaps(point, 4 * r):
        #             point = CPoint( 
        #             2 + np.random.rand() * (7 - 2),
        #             -1 * (2 + np.random.rand() * (7 - 2))
        #             )
        #         self._pos_store[pair] = point
        #         self._plot_dfg_state(
        #             point,
        #             r,
        #             imputer.get_label(pair.right()),
        #             "gray"
        #         )
        # add arcs and inbetween starts and ends
        working = [ pair for pair in starters ]
        # work out all the adjustments first
        adjustments = dict( 
            (pair, CShift(0, 0))
            for pair 
            in starters
        )
        adjustment = CShift( 2, -2)
        seen = set()
        while len(working) > 0:
            # pick the oldest state
            current = working.pop(0)
            left = adjustments[current]
            # get the following pairs
            nexters = followers.get(current.right())
            for next in nexters:
                if next not in seen and next not in enders:
                    adjustments[next] = left.add(adjustment)
                    working.append(next)
                    seen.add(next)
        # now work out a collection of points for each shift
        currrent_adjust = adjustment.magnify(1)
        adjustment_points = {}
        row_members = [ 
            val for val in adjustments.values() if val == currrent_adjust 
        ]
        while len(row_members) > 0:
            adjustment_points[currrent_adjust] = self._find_cubic_curve(
                r, (len(row_members))*2, currrent_adjust
            )[1:-1:2]
            currrent_adjust = currrent_adjust.add(adjustment)
            row_members = [ 
                val for val in adjustments.values() if val == currrent_adjust 
            ]

        keys = sorted(list(adjustment_points.keys()), key=lambda x: x.x)
        for key in keys:
            print(
                f"for key :: {key}"
            )
            print(
                f"we have the following points :: {str(adjustment_points[key])}"
            )
        # find a nice set of points on curve  for enders
        ending = self._find_cubic_curve(
            r,
            (len(enders))*2,
            currrent_adjust,
        )
        # plot ending dfg states
        for end,point in zip(enders,ending[1:-1:2]):
            # plot starting dfg state
            self._pos_store[end] = point
            self._plot_dfg_state(
                point,
                r,
                imputer.get_label(end.left()),
                "red"
            )
            # add incoming arrow
            end_point = point.add_shift(s_arrow_shift.inverse())
            start_point = point.add_shift(e_arrow_shift.inverse())
            self._create_arrow(start_point, end_point, 98)
        # finally plot new states
        seen = set()
        working = [ pair for pair in starters ]
        while len(working) > 0:
            # pick the oldest state
            current = working.pop(0)
            # get its position
            start_pos = self._pos_store[current]
            # look at its next
            nexters = followers.get(current.right())
            # plot state and draw arc between current and arc
            for arc in nexters:
                if arc not in seen and arc not in enders:
                    # plot and store a new state 
                    point = adjustment_points[adjustments[arc]].pop()
                    self._pos_store[arc] = point
                    self._plot_dfg_state(
                        point,
                        r,
                        imputer.get_label(arc.right()),
                        "gray"
                    )
                # arc
                end_pos = self._pos_store[arc]
                end_point = end_pos.add_shift(e_arrow_shift)
                start_point = start_pos.add_shift(e_arrow_shift.inverse())
                self._create_arrow(start_point, end_point, 98)
                if arc not in seen:
                    working.append(arc)
                    seen.add(arc)
                

    def get_axes(self) -> Axes:
        return self._ax 

    def get_figure(self) -> Figure:
        return self._fig 
    
    def _overlaps(self, point:CPoint, range:float) -> bool:
        """
        Returns true if the given point is within the range of anything else
        in storage, otherwise false.
        """
        for other in self._pos_store.values():
            if point.difference(other) <= range:
                return True
        return False

    
    def _plot_dfg_state(self, p:CPoint, r:float, 
                    label:str, colour="None") -> Patch:
        """
        Plots a state of the dfg at the given point.
        """
        circle =  Circle((p.x,p.y), r, color=colour)
        self._ax.add_patch(circle)
        text_shift = CShift(-1 * (r/2), 0)
        tp = p.add_shift(text_shift)
        self._ax.text(tp.x, tp.y, label, fontdict={"fontsize" : 5})

    
    def _interpolate_between(self, points:List[CPoint], 
                            )-> Callable:
        """
        Given a sequence of points, returns the linear interpolate between 
        them, returns a function on x to find y.
        """
        xers = [ p.x for p in points]
        yers = [ p.y for p in points ]
        return  interpolate.interp1d( 
                xers, yers
        )

    def _cubic_interpolate(self, points:List[CPoint],
                           smoothing:float = 1.5,
                           num_points:int = 3,
                           ) -> List[CPoint]:
        """
        Finds a cubic ploynomial between the givens and returns num_points
        points along the found curve.
        """
        xers = [ p.x for p in points ]
        yers = [ p.y for p in points ]
        xspace = np.linspace(0, 1, num_points)
        tck, _ = interpolate.splprep([xers, yers], s=smoothing)
        positions = interpolate.splev(xspace, tck, der=0)
        return [ 
            CPoint(x, y)
            for x,y 
            in zip(positions[0], positions[1])
        ]
    
    def _find_cubic_curve(self, 
                          radius:float,
                          points_on_curve:int,
                          start_shift:CShift,
                          ) -> List[CPoint]:
        """
        
        """
        # equation setup for curve finding
        Sx = 0.0625 * (5.65685 * (points_on_curve+2) + 8 )
        SL = np.sqrt( 
            Sx ** 2 + Sx ** 2
        )
        SL_shift = np.sqrt( 
            ((SL / 4) ** 2) / 2.0
        )
        adj_shift = CShift(-1 * SL_shift, -1 * SL_shift)
        # create points for cubic interpolation
        start_point = CPoint(
            (2 * radius) + Sx, (2 * radius) * -1
        ).add_shift(start_shift)
        points = [
            start_point
        ]
        curr_point = start_point
        for adj in range(3):
            if adj % 2 == 1:
                extra = 2 * radius * 0.5 + (points_on_curve / 2.0) * radius
            else:
                extra = radius
            # travel along long side
            curr_point = curr_point.add_shift(
                adj_shift
            )
            # shift left or right
            extra_shift = CShift(
                -1 * extra, 
                extra
            )
            # add to interpolation
            points.append(
                curr_point.add_shift(extra_shift)
            )
        # add far end of long side
        points.append(
            curr_point.add_shift(
                adj_shift
            )
        )
        # find cubic interpolation
        points = self._cubic_interpolate(points, num_points=points_on_curve+2)
        return points
    
    def _create_arrow(self, start:CPoint, end:CPoint, 
                      
                      arrow_cutoff:int=100):
        """
        Plots an arrowhead between start and end, with the head at the end.
        """
        f_lin =  self._interpolate_between([start,end])
        xpsace = np.linspace(start.x, end.x, 100)
        lines = self._ax.plot( 
            xpsace,
            f_lin(xpsace),
            'black',
            alpha=0.33
        )
        self._add_arrow(lines[0], xpsace[arrow_cutoff])

    
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
            arrowprops=dict(arrowstyle="->", color=color, alpha=0.66),
            size=size,
            alpha=0.33
        )

    

