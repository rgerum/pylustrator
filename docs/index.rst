
.. figure:: images/logo.png
    :align: left

Welcome to the Pylustrator Documentation
========================================

Pylustrator is a program to style your matplotlib plots for publication. Subplots can be resized and dragged around by
the mouse, text and annotations can be added. The changes can be saved to the initial plot file as python code.

.. raw:: html

    <div style="clear:both"></div>
    <hr>

Installation
------------

Just get pylustrator over the pip installation:

    ``pip install pylustrator``

Usage
-----

Using pylustrator is very easy and does not require substantial modifications to your code. Just add

.. code-block:: python
    :linenos:

    import pylustrator
    pylustrator.start()

before creating your first figure in your code. When calling ``plt.show()`` the plot will be displayed in a pylustrator
window.

You can test pylustrator with the following example code:

.. code-block:: python
    :linenos:

    # import matplotlib and numpy as usual
    import matplotlib.pyplot as plt
    import numpy as np

    # now import pylustrator
    import pylustrator

    # activate pylustrator
    pylustrator.start()

    # some test data
    x = np.arange(100)
    y1 = plt.plot(x, x**2)
    y2 = plt.plot(x, 0.5*x**2+x)

    # create a plot
    plt.subplot(121)
    plt.plot(x, y1)

    # create another plot
    plt.subplot(122)
    plt.plot(x, x**3)

    # show the plot in a pylustrator window
    plt.show()

Saving by pressing ``Ctrl+S`` or confirming to save when closing the window will add some lines of code at the end of your
python script (before your ``plt.show()``) that defines these changes:

.. code-block:: python
    :linenos:

    #% start: automatic generated code from pylustrator
    fig = plt.figure(1)
    fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}
    fig.set_size_inches(8.000000/2.54, 8.000000/2.54, forward=True)
    fig.axes[0].set_position([0.191879, 0.148168, 0.798133, 0.742010])
    fig.axes[0].set_xlabel("data x")
    fig.axes[0].set_ylabel("data y")
    fig.axes[1].set_position([0.375743, 0.603616, 0.339534, 0.248372])
    fig.axes[1].set_xlabel("data x")
    fig.axes[1].set_ylabel("data y")
    fig.axes[1].set_ylim(-40.0, 90.0)
    #% end: automatic generated code from pylustrator

The good thing is that this generated code is plain matplotlib code, so it will still work when you remove pylustrator
from your code! This is especially useful if you want to distribute your code and do not want to require pylustrator as
a dependency.

Can styling plots be any easier?

Note
----

If you encounter any bugs or unexpected behaviour, you are encouraged to report a bug in our
Bitbucket `bugtracker <https://bitbucket.org/fabry_biophysics/pylustrator/issues?status=new&status=open>`_.


Citing Pylustrator
------------------

If you use Pylustrator for your publications I would highly appreciate it if you cite the Pylustrator:

* Richard Gerum. (2018, June 21). `"Pylustrator: An interactive interface to style matplotlib plots." <https://zenodo.org/record/1294663>`_ Zenodo. doi:10.5281/zenodo.1294663
