
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

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="//www.youtube.com/embed/xXPI4LLrNuM" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>
    <br/>


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

    # build plots as you normally would
    np.random.seed(1)
    t = np.arange(0.0, 2, 0.001)
    y = 2 * np.sin(np.pi * t)
    a, b = np.random.normal(loc=(5., 3.), scale=(2., 4.), size=(100,2)).T
    b += a

    plt.figure(1)
    plt.subplot(131)
    plt.plot(t, y)

    plt.subplot(132)
    plt.plot(a, b, "o")

    plt.subplot(133)
    plt.bar(0, np.mean(a))
    plt.bar(1, np.mean(b))

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

.. note::
   Because pylustrator can save optionally save changes you've made in the GUI to update your source
   code, it cannot be used from a shell or a notebook. To use pylustrator, call it directly from a
   python file and use the command line to execute.

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
