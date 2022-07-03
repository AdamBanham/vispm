
<p align="center">
    <img src="https://vispm.s3.ap-southeast-2.amazonaws.com/_logo.svg" style="transform: scale(2.0)">
</p>

# VISPM: Visualisations for Process Mining

A python library for creating visualisations related to process mining, all graphs are generated using [matplotlib](https://pypi.org/project/matplotlib/).

## What is it?
This package provides an interface for making exciting visualisations about process mining. Process mining can be a purely technical endeavour at times, and having an easy way to visualise concepts is essential. To encourage others to overcome the technical components of process mining, sometimes having an engaging animation will do just that. A key difference between other data science domains and process mining, is that process mining outcomes often will have a visual interpretation that others don’t. We need more ways to emphasise this aspect, and this project is one such way.

The goal of vispm is to:
- Have fun and create some cool stuff.
- Make exciting process mining visualisation that would aspire others.
- Create a layered interface supporting three levels: quick-easy access, general templates for specific use cases, super customisation via class objects. 

## Main Features

Here is a list of supported process mining visualisations:
### Dotted Charts

This chart is the only visualisation available within the project so far. In this visualisation, we plot events across a time axis, and we can change how events are coloured depending on the type analysis. We currently support colouring events via trace or event label but offer a template for customer colourers.

#### Static Presentors

This section is currently being worked on and is unstable.

Below is an example of generating a dotted chart from an event log. While we do not require that you use pm4py as the importer, we suggest you use the library to handle xes or xes.gz files. The StaticDottedChartPresentor has several optional parameters that allow users to change the type of colourer used (trace, event label or custom), figure parameters (dpi, size, markersize) and the colourmap used for colouring. See the doc string for more information.

```python
from vispm import StaticDottedChartPresentor
from matplotlib import pyplot as plt

# not required but a very helpful and cool library
from pm4py import read_xes

from os.path import join 

LOG_FILE = join(".","BPI_Challenge_2012.xes.gz")

def main():
    log = read_xes(LOG_FILE)
    presentor = StaticDottedChartPresentor(log)
    presentor.plot()
    plt.show()

if __name__ == "__main__":
    main()
```

Below are some examples of using this class and playing around with custom colourers.

<div style="width:100%;display:inline-block">
    <img src="https://vispm.s3.ap-southeast-2.amazonaws.com/Dotted_Chart_of_BPI_Challenge_2012.png"  style="width:48%" alt="Dotted Chart for BPIC 2012">
    <img src="https://vispm.s3.ap-southeast-2.amazonaws.com/Dotted_Chart_of_BPI_Challenge_2017.png"  style="width:48%" alt="Dotted Chart for BPIC 2017">
</div>

##### Extensions

Below are some examples of extensions that can be added to this extension before ploting.

###### DottedColourHistogramExtension

This extension plots a histogram based on the events within a dotted chart. Events will be broken down by colour for each bin.

```python
from vispm import StaticDottedChartPresentor,DottedColourHistogramExtension

presentor = StaticDottedChartPresentor(log,dpi=100,
    event_colour_scheme=StaticDottedChartPresentor.EventColourScheme.EventLabel,
    colormap=HIGH_CONTRAST_COOL
)
ext = DottedColourHistogramExtension(direction=DottedColourHistogramExtension.Direction.NORTH)
presentor.add_extension(ext)
ext = DottedColourHistogramExtension(direction=DottedColourHistogramExtension.Direction.SOUTH,
         bin_axes=DottedColourHistogramExtension.PlotAxes.X)
presentor.add_extension(ext)
ext = DottedColourHistogramExtension(direction=DottedColourHistogramExtension.Direction.WEST)
presentor.add_extension(ext)
ext = DottedColourHistogramExtension(direction=DottedColourHistogramExtension.Direction.EAST,
         bin_axes=DottedColourHistogramExtension.PlotAxes.X)
presentor.add_extension(ext)
presentor.plot()
```

<div style="width:100%;display:inline-block">
    <img src="https://vispm.s3.ap-southeast-2.amazonaws.com/Dotted_ext_clrhist.png" alt="Dotted Chart with Colour Histogram" style="transform: scale(0.5);width: 48%">
    <img src="https://vispm.s3.ap-southeast-2.amazonaws.com/Dotted_ext_clrhist_2.png" alt="Dotted Chart with Colour Histogram" style="transform: scale(0.5);width: 48%">
</div>

###### DottedEventHistogramExtension

This extension plots a histogram based on the events within a dotted chart. Events will be broken down by the label for each event in each bin. This extension uses a colour imputer that is independent of the graph, meaning different colour schemes can be used for each extension.

1. setup up colour schemes to use
```python
colourmaps = [COOL_WINTER,EARTH,HIGH_CONTRAST_COOL,HIGH_CONTRAST_WARM]
seq_colourmap = np.vstack(
    (
    colourmaps[0](np.linspace(0.20,1,8)),
    colourmaps[1](np.linspace(0.20,1,8)),
    colourmaps[2](np.linspace(0.20,1,8)),
    colourmaps[3](np.linspace(0.20,1,8))
    )
)
seq_colourmap = ListedColormap(seq_colourmap, name='VARIANCE')
cmap = get_cmap(HIGH_CONTRAST_COOL, 26)
```

2. create a presentor and add extensions
```python
presentor = StaticDottedChartPresentor(log,dpi=100,
    event_colour_scheme=StaticDottedChartPresentor.EventColourScheme.EventLabel,
    colormap=cmap
)

ext = DottedEventHistogramExtension(
    direction=DottedEventHistogramExtension.Direction.SOUTH,
    bin_axes=DottedEventHistogramExtension.PlotAxes.X,
    colourmap=seq_colourmap
)
presentor.add_extension(ext)
ext = DottedEventHistogramExtension(
    direction=DottedEventHistogramExtension.Direction.NORTH,
    bin_axes=DottedEventHistogramExtension.PlotAxes.Y,
    colourmap=seq_colourmap
)
presentor.add_extension(ext)
ext = DottedEventHistogramExtension(
    direction=DottedEventHistogramExtension.Direction.WEST,
    bin_axes=DottedEventHistogramExtension.PlotAxes.Y,
    colourmap=cmap
)
presentor.add_extension(ext)
ext = DottedEventHistogramExtension(
    direction=DottedEventHistogramExtension.Direction.EAST,
    bin_axes=DottedEventHistogramExtension.PlotAxes.X,
    colourmap=cmap
)
presentor.add_extension(ext)

presentor.plot()
```

<div style="width:100%;display:inline-block">
    <img src="https://vispm.s3.ap-southeast-2.amazonaws.com/Dotted_ext_evhist.png" alt="Dotted Chart with Event Histogram" style="transform: scale(0.5);width: 48%">
</div>

#### Running Presentors

More on these in upcoming updates.

#### Complex Template Presentors

More on these in upcoming updates.

## Where to get it 

The source code is currently available on GitHub: https://github.com/AdamBanham/vispm

Installers for the latest released versions are available at the Python Package Index (PyPI): https://pypi.org/project/vispm/

To install the package, use the following command.
```
pip install vispm
```
