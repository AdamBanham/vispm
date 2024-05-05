from ._base import StaticPresentor
from ..extensions._base import ChartExtension
from ..helpers.imputers.event_imputers import EventLabelImputer
from ..helpers.data.cartesian_plotting import CPoint,CShift,CCircle
from ..helpers.data.cartesian_plotting import interpolate_between
from ..helpers.data.cartesian_plotting import angle_from_origin

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle,Polygon
from scipy import interpolate
import numpy as np

from dataclasses import dataclass
from typing import Tuple, List, Callable, Union, Literal
from random import choice
from enum import Enum, auto

PLOT_STATE = ChartExtension.UpdateState

@dataclass(init=False)
class DirectlyFollowsState():
    """
    A helpful abstraction for handling the states of the dfg visualisation.
    """

    class StateType(Enum):
        start = auto()
        body = auto()
        end = auto()

        def get_colour(self) -> str:
            """
            Returns a suitable colour for the state type.
            """
            if self == DirectlyFollowsState.StateType.end:
                return "red"
            elif self == DirectlyFollowsState.StateType.start:
                return "green"
            else:
                return "gray"

    origin:CPoint
    radius:float
    label:str 
    type:StateType
    area:CCircle
    
    def __init__(self, origin:CPoint, radius:float, label:str, 
                 type:StateType=StateType.body):
        self.origin = origin
        self.radius = radius
        self.label = label
        self.type = type
        self.area = CCircle(origin, radius)
        self._incoming = []
        self._outcoming = [] 

    def plot(self, ax:Axes) -> None:
        """
        Plots the state on the axes.
        """
        # draw the state
        colour= self.type.get_colour()
        circle =  Circle(
            (self.origin.x,self.origin.y), 
            self.radius, 
            color=colour
        )
        ax.add_patch(circle)
        # add a patch for start (tri) and end (square)?
        if self.type == self.StateType.start:
            self._add_start_symbol(ax, self.area) 
        elif self.type == self.StateType.end:
            self._add_end_symbol(ax, self.area) 
        # add text for label
        tp = self.origin
        ax.text(tp.x, tp.y, self.label, 
                fontsize = 5,
                ma="center",
                verticalalignment="center_baseline",
                horizontalalignment="center")
        # draw the incoming or outgoing arrow for non-body states
        arrow_shift = CShift(
            (self.radius * 2) * -1,
            (self.radius * 2) * -1,
        )
        if self.type == self.StateType.start:
            end_point = self.area.get_point_on_perimeter(225)
            start_point = end_point.add_shift(arrow_shift)
            self._create_arrow(start_point, end_point, ax, "green", 98) 
        elif self.type == self.StateType.end:
            start_point = self.area.get_point_on_perimeter(45)
            end_point = start_point.add_shift(arrow_shift.inverse())
            self._create_arrow(start_point, end_point, ax, "red", 98)

    def _add_start_symbol(self, ax:Axes, circle:CCircle) -> None:
        "Adds a triangle within the starting circle"
        inner = CCircle(
            circle.center,
            circle.radius * 0.7
        )
        p1 = inner.get_point_on_perimeter(225)
        p2 = inner.get_point_on_perimeter(135)
        p3 = inner.get_point_on_perimeter(0)
        triangle = Polygon(
            [ [p1.x,p1.y], [p2.x,p2.y], [p3.x,p3.y]],
            closed=True,
            fill=True,
            facecolor="white"
        )
        ax.add_patch(triangle)


    def _add_end_symbol(self, ax:Axes, circle:CCircle) -> None:
        "Adds a squre within the starting circle"
        inner = CCircle(
            circle.center,
            circle.radius * 0.6
        )
        p1 = inner.get_point_on_perimeter(45)
        p2 = inner.get_point_on_perimeter(135)
        p3 = inner.get_point_on_perimeter(225)
        p4 = inner.get_point_on_perimeter(315)
        square = Polygon(
            [ [p1.x,p1.y],[p2.x,p2.y], [p3.x,p3.y], [p4.x, p4.y], ],
            closed=True,
            fill=True,
            facecolor="white",
            capstyle="round"
        )
        ax.add_patch(square)

    def draw_connection_with(self, other:'DirectlyFollowsState', 
                             ax:Axes, linecolour:str="black"):
        """
        Draw a directed arrow between these two states.
        """
        # find a unit circle between these to curve our line
        if angle_from_origin(self.origin) < angle_from_origin(other.origin):
            degree = np.random.randint(30,150)
            rotation = 1
        else:
            degree = np.random.randint(30,150) * -1
            rotation = -1
        left = self.area.get_point_on_perimeter(degree)
        right = other.area.get_point_on_perimeter(degree)
        difference = left.difference(right)
        bet_origin = left.add_shift(
            difference.magnify(0.5)
        )
        rad_shift = left.difference(bet_origin)
        radius = np.sqrt(
            rad_shift.x ** 2 + rad_shift.y ** 2
        )
        bet_circle = CCircle(
            bet_origin,
            radius
        )
        # now plot a line along the perimeter
        shift = 0.25
        if (rotation > 0):
            starting = 225
            # slowly reduce until y is higher than left
            check = bet_circle.get_point_on_perimeter(starting)
            while (check.difference(left).power() > 0.05):
                starting -= shift
                check = bet_circle.get_point_on_perimeter(starting)
            ending = 15
            # slowly increase until y is higher than right
            check = bet_circle.get_point_on_perimeter(ending)
            while (check.difference(right).power() > 0.05):
                ending += shift
                check = bet_circle.get_point_on_perimeter(ending)
        else:
            starting = -160
            # slowly increase until x is right of left
            check = bet_circle.get_point_on_perimeter(starting)
            while (check.difference(left).power() > 0.05):
                starting += shift
                check = bet_circle.get_point_on_perimeter(starting)
            ending = 115
            # slowly decrease until x is right of right
            check = bet_circle.get_point_on_perimeter(ending)
            while (check.difference(right).power() > 0.05):
                ending -= shift
                check = bet_circle.get_point_on_perimeter(ending)
        xspace = np.linspace(starting, ending, 100)
        points = [ 
            bet_circle.get_point_on_perimeter(d)
            for d 
            in xspace
        ]
        lines = ax.plot( 
            [ p.x for p in points ],
            [ p.y for p in points ],
            linecolour,
            alpha=0.33
        )
        self._add_arrow(lines[0], [ p.x for p in points ][15])
        self._add_arrow(lines[0], [ p.x for p in points ][-5])

    def draw_ending_connection_with(self, other:'DirectlyFollowsState',
                                    ax:Axes):
        """
        Attempts to draw a nice red arrow to other, used to denote the ending
        flow a trace.
        """
        # work out the side to enter on the target
        if angle_from_origin(self.origin) > angle_from_origin(other.origin):
            ldeg = np.random.randint(-45,0)
            rdeg = np.random.randint(-150,-110)
            rotation = 1
        else:
            ldeg = np.random.randint(90,135)
            rdeg = np.random.randint(-130,-90)
            rotation = -1
        left = self.area.get_point_on_perimeter(ldeg)
        right = other.area.get_point_on_perimeter(rdeg)
        # find the mid point between self and other
        difference = left.difference(right)
        bet_origin = left.add_shift(
            difference.magnify(0.5)
        )
        rad_shift = left.difference(bet_origin)
        radius = np.sqrt(
            rad_shift.x ** 2 + rad_shift.y ** 2
        )
        bet_circle = CCircle(
            bet_origin,
            radius
        )
        # now plot a line between self and other with an arrow
        # find the starting degree 
        color = "red"
        shift = 0.25
        if rotation < 0:
            starting = -160
            # slowly increase until x is right of left
            check = bet_circle.get_point_on_perimeter(starting)
            while (check.difference(left).power() > 0.05):
                starting += shift
                check = bet_circle.get_point_on_perimeter(starting)
            ending = 90
            # slowly decrease until x is right of right
            check = bet_circle.get_point_on_perimeter(ending)
            while (check.difference(right).power() > 0.05):
                ending -= shift
                check = bet_circle.get_point_on_perimeter(ending)
            color="purple"
        else:
            starting = 225
            # slowly reduce until y is higher than left
            check = bet_circle.get_point_on_perimeter(starting)
            while (check.difference(left).power() > 0.05):
                starting -= shift
                check = bet_circle.get_point_on_perimeter(starting)
            ending = 360
            # slowly increase until y is higher than right
            check = bet_circle.get_point_on_perimeter(ending)
            while (check.difference(right).power() > 0.05):
                ending -= shift
                check = bet_circle.get_point_on_perimeter(ending)
        # now plot a curved line with arrows
        xspace = np.linspace(starting,ending,100)
        points = [ 
            bet_circle.get_point_on_perimeter(d)
            for d 
            in xspace
        ]
        lines = ax.plot( 
            [ p.x for p in points ],
            [ p.y for p in points ],
            color,
            alpha=0.33
        )
        self._add_arrow(lines[0], [ p.x for p in points ][15])
        self._add_arrow(lines[0], [ p.x for p in points ][-5])


    def draw_starting_connection_with(self, other:'DirectlyFollowsState',
                                      ax:Axes):
        """
        Attempts to draw a nice green arrow to other, used to denote the starting
        flow of a trace.
        """
        # work out the side to enter on the target
        if angle_from_origin(self.origin) > angle_from_origin(other.origin):
            rdeg = np.random.randint(130,160)
            rotation = 1
        else:
            rdeg = np.random.randint(-90,-45)
            rotation = -1
        left = self.area.get_point_on_perimeter(np.random.randint(15,45))
        right = other.area.get_point_on_perimeter(rdeg)
        # find the mid point between self and other
        difference = left.difference(right)
        bet_origin = left.add_shift(
            difference.magnify(0.5)
        )
        rad_shift = left.difference(bet_origin)
        radius = np.sqrt(
            rad_shift.x ** 2 + rad_shift.y ** 2
        )
        bet_circle = CCircle(
            bet_origin,
            radius
        )
        # now plot a line between self and other with an arrow
        # find the starting degree 
        color = "green"
        shift = 0.25
        if rotation < 0:
            starting = -160
            # slowly increase until x is right of left
            check = bet_circle.get_point_on_perimeter(starting)
            while (check.difference(left).power() > 0.05):
                starting += shift
                check = bet_circle.get_point_on_perimeter(starting)
            ending = 115
            # slowly decrease until x is right of right
            check = bet_circle.get_point_on_perimeter(ending)
            while (check.difference(right).power() > 0.05):
                ending -= shift
                check = bet_circle.get_point_on_perimeter(ending)
        else:
            starting = 225
            # slowly reduce until y is higher than left
            check = bet_circle.get_point_on_perimeter(starting)
            while (check.y < left.y):
                starting -= shift
                check = bet_circle.get_point_on_perimeter(starting)
            ending = 15
            # slowly increase until y is higher than right
            check = bet_circle.get_point_on_perimeter(ending)
            while (check.y < right.y):
                ending += shift
                check = bet_circle.get_point_on_perimeter(ending)
        # now plot a curved line with arrows
        xspace = np.linspace(starting,ending,100)
        points = [ 
            bet_circle.get_point_on_perimeter(d)
            for d 
            in xspace
        ]
        lines = ax.plot( 
            [ p.x for p in points ],
            [ p.y for p in points ],
            color,
            alpha=0.33
        )
        self._add_arrow(lines[0], [ p.x for p in points ][15])
        self._add_arrow(lines[0], [ p.x for p in points ][-5])


    def _create_arrow(self, start:CPoint, end:CPoint, ax:Axes, 
                      linecolour="black",                     
                      arrow_cutoff:int=100):
        """
        Plots an arrowhead between start and end, with the head at the end.
        """
        f_lin =  interpolate_between([start,end])
        xpsace = np.linspace(start.x, end.x, 100)
        lines = ax.plot( 
            xpsace,
            f_lin(xpsace),
            linecolour,
            alpha=0.33
        )
        self._add_arrow(lines[0], xpsace[arrow_cutoff])

    
    def _add_arrow(self, line,
                   position=None, direction='right', size=15, color=None):
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
            from pmkoalas.simple import EventLog
            if (isinstance(event_log, ComplexEventLog)):
                self._log_name = event_log.name
            elif (isinstance(event_log, EventLog)):
                self._log_name = event_log.get_name()
            else:
                raise ValueError("not a pmkoalas data structure")
        except:
            try :
                self._log_name = event_log.attributes['concept:name'] 
            except:
                self._debug("Cannot find concept:name in eventlog attributes.")
        # try to build follows languages
        if (isinstance(event_log, ComplexEventLog)):
            self._followers = event_log.simplify().directly_follow_relations(debug=True)
            self._acts = event_log.seen_activities()
        elif(isinstance(event_log, EventLog)):
            self._followers = event_log.directly_follow_relations(debug=True)
            self._acts = event_log.seen_activities()
        else:
            raise ValueError("Directly follows construction not implemented for"
                             +" logs of ::" + type(event_log))


    def plot(self) -> Figure:
        self._ax = self._adjust_for_extensions(self._fig)
        self.update_plot_state(PLOT_STATE.DRAWING)
        self.update_extensions(followers=self._followers) 
        self._create_dfg_frame(self._followers)
        self._debug("Cleaning up plot...")
        xers = [ pos.origin.x for pos in self._pos_store.values()]
        max_x = np.max(xers) + np.max(xers) * 0.1
        self._ax.set_xlim(0, max_x)
        self._ax.set_ylim(0, max_x)
        self._ax.set_axis_off()
        # self._ax.grid()
        self._debug("Cleaning up ready to show...")

    def _create_dfg_frame(self, followers:FollowLanguage):
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
        pairs = [
            pair
            for pair 
            in followers.pairs()
            if pair not in starters and pair not in enders
        ]
        body = [ p.left() for p in pairs ] + [ p.right() for p in pairs]
        body = list(set(body))
        body = sorted(body)
        # work out starting spline
        r = .5
        curver = CCircle(
            CPoint(0,0),
            4
        )
        # find a nice set of points on curve  
        for start in starters[1:]:
            curver = curver.change_radius(r * 2)
        num_points = len(starters) + 2 + 2
        starting = curver.find_equal_distance_points(
            10,
            80,
            num_points
        )
        starting.pop(int(len(starting)/ 2))
        starting.pop(int(len(starting)/ 2))
        # store dfg positions 
        self._pos_store = {}
        for start,point in zip(starters,starting[1:-1]):
            # plot starting dfg state
            state = DirectlyFollowsState(
                point,
                r,
                imputer.get_label(start.right()),
                DirectlyFollowsState.StateType.start
            )
            self._pos_store[start] = state
            state.plot(self._ax)
        # order bodies by their proximity to starts and ends
        print("ordering bodies")
        bodies = [
            (letter, 
             sum([ letter in start.proceeding() for start in starters]) 
             - sum([ (letter in end.preceding()) * 1.2 for end in enders])
             )
            for letter
            in body
        ]
        bodies.sort(
            key=lambda x: x[1],
            reverse=True
        )
        print(bodies)
        body = [
            letter
            for letter,_
            in bodies
        ]        
        # add arcs and inbetween starts and ends
        for letter in body:
            curver = curver.change_radius(r * 4)
            # point =  choice(curver.find_equal_distance_points(10,80,9)[2:-2])
            point =  curver.find_equal_distance_points(10,80,3)[1]
            state = DirectlyFollowsState(
                point, r, imputer.get_label(letter)
            )
            self._pos_store[letter] = state
            state.plot(self._ax)

        for pair in pairs:
                # skip flows where proceeding is only end (will be added later)
                if (pair.proceeding() == set(["END"])):
                    continue
                # skip flows whee preceding is only source (will be added later)
                if (pair.preceding() == set(["SOURCE"])):
                    continue
                start = self._pos_store[pair.left()]
                end = self._pos_store[pair.right()]
                start.draw_connection_with(
                    end,
                    self._ax
                )

        curver = curver.change_radius(r * 6)
        # find a nice set of points on curve  for enders
        num_points = len(enders) + 2 + 2
        ending = curver.find_equal_distance_points(
            10,
            80,
            num_points
        ) 
        ending.pop(int(len(ending)/ 2))
        ending.pop(int(len(ending)/ 2))
        for end,point in zip(enders,ending[1:-1]):
            # plot starting dfg state
            state = DirectlyFollowsState(
                point, r, imputer.get_label(end.left()), 
                DirectlyFollowsState.StateType.end
            )
            self._pos_store[end] = state
            state.plot(self._ax)

        # plot directly preceeding activites from starts
        for start in starters:
            state = self._pos_store[start]
            for prec in start.proceeding():
                if (prec == "END"):
                    continue
                other = self._pos_store[prec]
                state.draw_starting_connection_with(other, self._ax,)

        # plot directly preceeding activites from ends
        for end in enders:
            state = self._pos_store[end]
            for prec in end.preceding():
                if (prec == "SOURCE"):
                    continue
                other = self._pos_store[prec]
                other.draw_ending_connection_with(
                    state,
                    self._ax
                )

    def get_axes(self) -> Axes:
        return self._ax 

    def get_figure(self) -> Figure:
        return self._fig 

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
                      linecolour="black",
                      arrow_cutoff:int=100):
        """
        Plots an arrowhead between start and end, with the head at the end.
        """
        f_lin =  interpolate_between([start,end])
        xpsace = np.linspace(start.x, end.x, 100)
        lines = self._ax.plot( 
            xpsace,
            f_lin(xpsace),
            linecolour,
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

    

