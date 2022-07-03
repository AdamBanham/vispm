from matplotlib.cm import get_cmap
from matplotlib.colors import ListedColormap,Colormap

import numpy as np

CATEGORICAL = get_cmap("Accent")
HIGH_CONTRAST_COOL = get_cmap("viridis", 26)
HIGH_CONTRAST_WARM = get_cmap("plasma", 26)
COOL_WINTER = get_cmap("YlGnBu",26)

earth_top = get_cmap('Greens', 25)
earth_bottom = get_cmap('copper', 100)

newcolors = np.vstack((earth_top(np.linspace(0.75, 0.25, 6)),
                       earth_bottom(np.linspace(1, .25, 12))))
EARTH = ListedColormap(newcolors, name='EARTH')