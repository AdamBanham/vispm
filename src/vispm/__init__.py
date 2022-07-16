
__version__ = "0.0.6.2"


# dotted chart presentors
## static presentors
from .static.dotted import StaticDottedChartPresentor


# Extensions
## dotted chart extensions
from .extensions.dotted.colour_histogram import DottedColourHistogramExtension
from .extensions.dotted.event_histogram import DottedEventHistogramExtension
from.extensions.dotted.description_histogram import DescriptionHistogramExtension
