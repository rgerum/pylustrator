
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
    plt.figure(1).set_size_inches(8.000000/2.54, 8.000000/2.54, forward=True)
    plt.figure(1).axes[0].set_position([0.191879, 0.148168, 0.798133, 0.742010])
    plt.figure(1).axes[0].set_xlabel("data x")
    plt.figure(1).axes[0].set_ylabel("data y")
    plt.figure(1).axes[1].set_position([0.375743, 0.603616, 0.339534, 0.248372])
    plt.figure(1).axes[1].set_xlabel("data x")
    plt.figure(1).axes[1].set_ylabel("data y")
    plt.figure(1).axes[1].set_ylim(-40.0, 90.0)
    #% end: automatic generated code from pylustrator

.. note::
   Because pylustrator can optionally save changes you've made in the GUI to update your source
   code, it cannot be used from a shell. To use pylustrator, call it directly from a
   python file and use the command line to execute.

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

* Gerum, R., (2020). **pylustrator: code generation for reproducible figures for publication**. Journal of Open Source Software, 5(51), 1989.
`doi.org/10.21105/joss.01989 <https://doi.org/10.21105/joss.01989>`_.


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
