
.. figure:: images/logo.png
    :align: left

Welcome to the Pylustrator Documentation
========================================

Pylustrator is a software to prepare your figures for publication in a reproducible way. This means you receive a figure
representing your data and alongside a generated code file that can exactly reproduce the figure as you put them in the
publication, without the need to readjust things in external programs.

Pylustrator offers an interactive interface to find the best way to present your data in a figure for publication.
Added formatting an styling can be saved by automatically generated code. To compose multiple figures to panels,
pylustrator can compose different subfigures to a single figure.


.. raw:: html

    <div style="clear:both"></div>
    <hr>

Installation
------------

Just get pylustrator over the pip installation:

    ``pip install pylustrator``

The package depends on:

numpy, matplotlib, pyqt5, qtpy, qtawesome, scikit-image, natsort

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

You can test pylustrator with the following example code `example_pylustrator.py <https://raw.githubusercontent.com/rgerum/pylustrator/master/docs/example_pylustrator.py>`_:

.. literalinclude:: example_pylustrator.py
   :language: python
   :emphasize-lines: 6,9
   :linenos:

Saving by pressing ``Ctrl+S`` or confirming to save when closing the window will add some lines of code at the end of your
python script (before your ``plt.show()``) that defines these changes:

.. code-block:: python
    :linenos:

    #% start: automatic generated code from pylustrator
    plt.figure(1).ax_dict = {ax.get_label(): ax for ax in plt.figure(1).axes}
    import matplotlib as mpl
    getattr(plt.figure(1), '_pylustrator_init', lambda: ...)()
    plt.figure(1).set_size_inches(9.980000/2.54, 11.660000/2.54, forward=True)
    plt.figure(1).axes[0].set(position=[0.1531, 0.1557, 0.7968, 0.3141], xlabel='time', ylabel='amplitude')
    plt.figure(1).axes[0].set_position([0.151600, 0.127337, 0.788696, 0.324652])
    plt.figure(1).axes[0].spines[['right', 'top']].set_visible(False)
    plt.figure(1).axes[0].text(-0.0934, 0.9934, 'c', transform=plt.figure(1).axes[0].transAxes, ha='center', weight='bold')  # id=plt.figure(1).axes[0].texts[0].new
    plt.figure(1).axes[1].set(position=[0.5784, 0.5555, 0.3714, 0.3779], xlabel='A', ylabel='B')
    plt.figure(1).axes[1].set_position([0.572546, 0.540568, 0.367654, 0.390595])
    plt.figure(1).axes[1].spines[['right', 'top']].set_visible(False)
    plt.figure(1).axes[1].text(-0.1648, 0.9934, 'b', transform=plt.figure(1).axes[1].transAxes, weight='bold')  # id=plt.figure(1).axes[1].texts[0].new
    plt.figure(1).axes[2].set(position=[0.1531, 0.5555, 0.2741, 0.3779], xticks=[0., 1.], xticklabels=['A', 'B'], ylabel='mean value')
    plt.figure(1).axes[2].set_position([0.151600, 0.540568, 0.271293, 0.390595])
    plt.figure(1).axes[2].spines[['right', 'top']].set_visible(False)
    plt.figure(1).axes[2].text(-0.2717, 0.9934, 'a', transform=plt.figure(1).axes[2].transAxes, ha='center', weight='bold')  # id=plt.figure(1).axes[2].texts[0].new
    #% end: automatic generated code from pylustrator

.. note::
   Because pylustrator can optionally save changes you've made in the GUI to update your source
   code, it cannot be used from a shell. To use pylustrator, call it directly from a
   python file and use the command line to execute.

.. note::
    In case you import matplotlib.pyplot to the global namespace (e.g. `from matplotlib.pyplot import *`), pylustrator has
    to be started before this import to be able to overload the `show` command.

    Also using the `show` from the `pylab` import does not work. And is anyways discouraged, see https://matplotlib.org/stable/api/index.html?highlight=pylab#module-pylab

The good thing is that this generated code is plain matplotlib code, so it will still work when you remove pylustrator
from your code! This is especially useful if you want to distribute your code and do not want to require pylustrator as
a dependency.

Can styling plots be any easier?

Note
----

If you encounter any bugs or unexpected behaviour, you are encouraged to report a bug in our
Github `bugtracker <https://github.com/rgerum/pylustrator/issues>`_.


Citing Pylustrator
------------------

If you use Pylustrator for your publications I would highly appreciate it if you cite the Pylustrator:

* Gerum, R., (2020). **pylustrator: code generation for reproducible figures for publication**. Journal of Open Source Software, 5(51), 1989. `doi:10.21105/joss.01989 <https://doi.org/10.21105/joss.01989>`_


License
-------

Pylustrator is released under the `GPLv3 <https://choosealicense.com/licenses/gpl-3.0/>`_ license. The generated output
code of Pylustrator can be freely used according to the `MIT <https://choosealicense.com/licenses/mit/>`_ license, but as
it relys on Matplotlib also the `Matplotlib License <https://matplotlib.org/users/license.html>`_ has to be taken into
account.

.. toctree::
   :caption: Contents
   :maxdepth: 2

   styling
   composing
   api
