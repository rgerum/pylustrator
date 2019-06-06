---
title: 'Pylustrator: An interactive interface to style matplotlib figures'
tags:
  - Python
  - matplotlib
  - plotting
  - interactive
  - code generation
  - drag
  - style
authors:
  - name: Richard Gerum
    orcid: 0000-0001-5893-2650
    affiliation: 1
affiliations:
 - name: Department of Physics, University of Erlangen-Nürnberg, Germany
   index: 1
date: 06 June 2018
bibliography: paper.bib
---

# Summary

Visualisations of data are at the core of every scientific publication [@Tufte1893]. They have 
to be as clear as possible to facilitate the communication of scientific insights. As data 
sets come in very different formats and shapes, the corresponding visualisations often have 
to be specifically tailored to present the major insights in an intuitive way.
 
The widely used Matplotlib libary [@Hunter2007], based on the general-purpose programming 
language Python [@Rossum1995], offers a powerful engine to present data in flexible ways.
However, designing a composite figure for a publication often requires the combination of
multiple plots. The exact arrangement of those individual plots can be tedious and result in overly 
complex code if the figure deviates from a default grid-style layout. Some researchers therefore 
combine individual plots in external graphics program. While this offers more flexibility, 
the figure cannot be easily reproduced easily if the underlying data is updated.

![Example how pylustrator can be used to style a figure.](figure1.pdf)

We developed ``Pylustrator`` to combine an easy-to-use interactive way to design the figure layout 
with the Python code that processes the underlying data. ``Pylustrator`` is an interface to directly edit 
Python-generated Matplotlib figures to finalize them for publication. Therefore, subplots can be resized 
and positioned dynamically (by mouse dragging), and text as well as annotations can be added. The layout 
changes are directly appended to the original Python file as native Python code.

Using ``Pylustrator`` in any given Python file simply requires the addition of only two lines of code:

    import pylustrator
    pylustrator.start()
    
The Matplotlib figure is then displayed in an interactive window when the `plt.show()` command is called. In 
this interactive window, ``Pylustrator`` enables the user to:

- resize and position plots by mouse-dragging 
- adjust the position of plots legends
- align elements easily by automatic "snapping"
- resize the complete figure in cm/inches
- add text and annotations, and change their style and color
- adjust plot ticks and tick labels

After the user completes the layout and closes the interactive window, the layout changes are translated into 
Python code and appended to the source file. It is important to note that the automatically generated code 
only relies on Matplotib and does not need the ``Pylustrator`` package anymore. Thus, the ``Pylustrator`` 
dependency can later be removed to allow users who do not have``Pylustrator`` installed to generate the figure. 

# Acknowledgements

We acknowledge testing, support and feedback from Christoph Mark, Sebastian Richter, 
and Achim Schilling and Ronny Reimann for the design of the Pylustrator Logo.

# References