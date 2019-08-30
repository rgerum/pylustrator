
Styling Figures
===============

Opening
-------
To open the pylustrator editor to style a figure, you just have to call the function `pylustrator.start()` before any figure is
created in your code.

.. code-block:: python
    :linenos:

    import pylustrator
    pylustrator.start()

This will overload the commands `plt.figure()` and `plt.show()`. `plt.figure()` (which is often indirectly called when
creating plots) now initializes a figure in a GUI window and `plt.show()` then shows this GUI window.

In the GUI window elements can be dragged around using a click and drag with the left mouse button. If you want to cycle
though different elements on the same spot double click on the same position multiple times. To zoom in in the plot window
use `strg+mousewheel` and you can pan the figure with holding the middle mouse button.

To select multiple elements hold shift while clicking on multiple elements.

Saving
------

To save the figure press `ctrl+s` or select `File->Save`. This will generate code that corresponds to the changes you made
to the figure and past it into your script file or your jupyter notebook cell. The code will be pasted directly over the
`plt.show()` command that started the editor or, if there already is a generated code block for this figure, it will replace
the existing code block.