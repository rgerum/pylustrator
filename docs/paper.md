---
title: 'pylustrator: code generation for reproducible figures for publication'
tags:
  - reproducibility
  - code generation
  - interactive
  - Python
  - matplotlib
  - plotting
  - drag
  - style
authors:
  - name: Richard Gerum
    orcid: 0000-0001-5893-2650
    affiliation: 1
affiliations:
 - name: Department of Physics, University of Erlangen-Nürnberg, Germany
   index: 1
date: 06 September 2019
bibliography: paper.bib
---


# Background

In recent years, more and more researchers have called attention to a growing "reproducibility crisis" [@CRL16846]. An important factor that contributes to problems in reproducing results from published studies is the unavailability of the raw data from the original experiment as well as the unavailability of the methods or the code used for the evaluation the raw data [@Baker2016]. 
One major step to overcome these shortcomings is the publication of all raw data as well as a documented version of the code used for evaluation [@baker2016scientists]. The ideal case would be that anyone interested can download the raw data and exactly reproduce the figures of the publication.

To address the issue of data availability, researchers are encouraged to provide their data in online repositories, e.g. dryad [@dryad]. However, this data is useless unless the complete evaluation procedure in the terms of all evaluation and visualisation steps
can be comprehended by other scientists. The best way to do so is to provide a complete well documented evaluation code, 
including all important steps from basic artifact corrections up to the final plot to be published. Open Source scripting languages like Python [@Rossum1995] or R [@R] are ideal for such code as open source languages are accessible for everyone. Furthermore, interpreted languages do not need to be compiled, therefore have less obstacles for the user to run the code. The last part of the evaluation of the data is the visualisation, which is crucial to communicate the results [@Tufte1893]. 
This paper deals with the visualization step which consists of two parts: the generation of simple plots from data and composing meaningful figures from these plots.

The first part of generating the building blocks of figures, the plots, is already covered in various toolkits, e.g. Matplotlib [@Hunter2007], Bokeh [@Bokeh] or Seaborn [@seaborn]. There, already exist some software that records user interactions to generate
3D plots ([@ahrens2005paraview], [@westenberger2008avizo], [@dragonfly]), but to generate reproducible figures from simple plots scripts, no convenient toolkit is yet available for Python. Matplotlib already offers figures composed of multiple subplots, but to generate a complete figure ready for publication a lot of code is needed to add all formatting, annotations and styling commands. Therefore, this approach is often not followed as it is impractical for real applications. Users often prefer graphical tools such as image manipulation software, e.g. GIMP [@GIMP] or Inkscape [@Inkscape]. These offer great flexibility, but cannot provide a reproducible way of generating figures and bear the danger of accidentally changing data points. Also important to note is that by using an image manipulation software, any small change to the evaluation requires to re-edit the figure in the image manipulation software. A process that slows down the creation of figures and is prone to errors.

# Algorithm and Exemplary Results

``pylustrator`` was developed to address this issue. A tool to fill the gap from single plots to complete figures, by a code generation algorithm, that turns user input into python code for reproducible figure assembly (Fig.~\ref{fig:Visualisation}).  Small changes to the evaluation or new data only require to run the code again to update the figure.

![Example how code for composing a figure can be generated with pylustrator.](figure1.pdf)

Using ``pylustrator`` in any given Python file that uses Matplotlib do plot data, simply requires the addition of only two lines of code:

    import pylustrator
    pylustrator.start()

The Matplotlib figure is then displayed in an interactive window (Fig. 2) when the `plt.show()` command is called. In this interactive window, ``pylustrator`` enables the user to:

- resize and position plots by mouse-dragging 
- adjust the position of plots legends
- align elements easily by automatic "snapping"
- resize the complete figure in cm/inches
- add text and annotations, and change their style and color
- adjust plot ticks and tick labels

![The interface of ``pylustrator``. The user can view the elements of the plot, edit their properties, edit them in the plot preview and experiment with different color schemes.](figure2.pdf)

``pylustrator`` tracks all these changes to translate them into python code. Every change is split in four parts: the command object, the command text, the target object and the target command. The command object is the object instance (e.g. the Axes object) that has a method to call for this change and the command text is the methods name together with the parameters (e.g. ".annotate('New Annotation')"). The target object is the object that is affected by the command. In most cases this is the same as the command object, but in some cases when new child objects are created the target object is the child object. The target command is the methods name without the parameters.
 
 Command objects are "serialized" by iteratively going up the parent-child tree from e.g. a text to the axis to the figure and generating a python command from this dependency (e.g. `plt.figure(1).axes[0].texts[0]`, the first text of the first axes of figure 1). When saving, ``pylustrator`` introspects its current stack to find the line of code from where it was called and inserts the automatically generated code directly before the command calling ``pylustrator``.
 
 When loading a file with automatically generated code, ``pylustrator`` splits all the automatically generated lines into reference objects and reference commands. New changes where both the reference object and the reference command match a previous change, the previous change is overwritten. This ensures that previously generated code can be loaded appropriately and saving the same figure multiple times generates the code only once.
  
It is important to note that the automatically generated code only relies on Matplotlib and does not need the ``pylustrator`` package anymore. Thus, the ``pylustrator`` import can later be removed to allow to share the code without an additional introduced dependency. 

The documentation of ``pylustrator`` can be found on https://pylustrator.readthedocs.org.

# Conclusion
This packages offers an improvement to create publishable figures from single plots based on an open source Python library called ``pylustrator``. The figures can be arranged by drag and drop and the ``pylustrator`` library produces the according code. Thus, this library provides a valuable contribution to increase the reproducibility of scientific results.

# Acknowledgements 

We acknowledge testing, support and feedback from Christoph Mark, Sebastian Richter, and Achim Schilling and Ronny Reimann for the design of the Pylustrator Logo.

# References
