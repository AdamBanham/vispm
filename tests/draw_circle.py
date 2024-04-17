from vispm.helpers.data.cartesian_plotting import CCircle, CPoint, CShift

from matplotlib import pyplot as plt
import numpy as np

def draw(ax, circle):
    points = np.linspace(0, 360, 15)
    points = [
        circle.get_point_on_perimeter(d)
        for d 
        in points
    ]

    ax.plot(
        [circle.center.x],
        [circle.center.y]
        ,
        "ro",
    )

    ax.plot(
        [ p.x for p in points ],
        [ p.y for p in points ],
        "-o"
    )

if __name__ == "__main__":
    fig = plt.figure(figsize=(3,3))

    circle = CCircle(
        CPoint(0, 0), 2 
    )

    ax = fig.subplots(1,1)
    draw(ax, circle)
    circle = circle.change_radius(2)
    draw(ax, circle)
    circle = CCircle(
        circle.center.add_shift(
            CShift(
                3, 3
            )
        ),
        circle.radius
    )
    draw(ax, circle)
    circle = CCircle(
        circle.center.add_shift(
            CShift(
                -6, -6
            )
        ),
        circle.radius
    )
    draw(ax, circle)
    circle = CCircle(
        circle.center.add_shift(
            CShift(
                0, 6
            )
        ),
        circle.radius
    )
    draw(ax, circle)
    circle = CCircle(
        circle.center.add_shift(
            CShift(
                6, -6
            )
        ),
        circle.radius
    )
    draw(ax, circle)
    



    plt.show()