.. _styling:

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
to the figure and paste it into your script file or your jupyter notebook cell. The code will be pasted directly over the
`plt.show()` command that started the editor or, if there already is a generated code block for this figure, it will replace
the existing code block.

Increasing Performance
----------------------
Often plots with lots of elements can slow down the performance of pylustrator as with every edit, the whole plot is
rerendered. To circumvent this problem, pylustrator offers a function to calculate a rasterized representation (e.g. pixel data)
of the contents of each axes and only display the pixel data instead of rendering the vector data with every draw.

It can be activated with the button "rasterize". It can be clicked again to update the rasterisation or deactivated with
a click on the button "derasterize" next to it.

Color editor
------------
Pylustrator comes with a powerful color editor which allows to test different color configurations for your figure easily.
On the right hand side of the window you see a list of all currently used colors. You can right click on any color to open
a color choosed dialog. You can also directly edit the color using the html notation (e.g. #FF0000) provided on the button.
You can drag and drop colors to different slots to test different configurations for your figure.

The field below allows to copy and paste color lists from different sources. For example using color palette generators on the
internet, e.g. `<https://medialab.github.io/iwanthue/>`_.

Additionally, if you generate plot lines with colors from a colormap, pylustrator can recognize that and allow you to
choose different colormaps for the set of plot lines.

Tick Editor
-----------

.. |the tick icon| image:: ../pylustrator/icons/ticks.ico

To edit the ticks of an axes click on |the tick icon|. There, a windows opens that allows to set major and minor ticks
every line in the edit window corresponds to one tick. Texts are directly interpreted as float values if possible and the
text used as tick label, e.g. you can but a tick at 5.0 with the text "5" (e.g. formated without decimal point).
To specify an exponent, it is also possible to write e.g. 5*10^2 (to put a tick at 500 with the label :math:`5\cdot10^2`).
If the label cannot be directly writen as a number, add the label after the number enclosed in tick marks e.g. 5 "start",
to add a tick at position 5 with the label "start".
