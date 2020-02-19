#!/usr/bin/env python
# -*- coding: utf-8 -*-
# jupyter_cells.py

# Copyright (c) 2016-2020, Richard Gerum
#
# This file is part of Pylustrator.
#
# Pylustrator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pylustrator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pylustrator. If not, see <http://www.gnu.org/licenses/>

"""
This file implements pylustrator for jupyter notebooks. Basically it provides an file open function that checks if
the file is instead of a normal file a jupyter notebook and redirects writes accordingly.
"""

def setJupyterCellText(text: str):
    """ the function replaces the text in the current jupyter cell with the given text """
    from IPython.display import Javascript, display
    text = text.replace("\n", "\\n").replace("'", "\\'")
    js = """
    var output_area = this;
    // find my cell element
    var cell_element = output_area.element.parents('.cell');
    // which cell is it?
    var cell_idx = Jupyter.notebook.get_cell_elements().index(cell_element);
    // get the cell object
    var cell = Jupyter.notebook.get_cell(cell_idx);
    cell.get_text();
    cell.set_text('"""+text+"""');
    console.log('"""+text+"""');
    """
    display(Javascript(js))


def getIpythonCurrentCell() -> str:
    """ this function returns the text of the current jupyter cell """
    import inspect
    # get the first stack which has a filename starting with "<ipython-input" (e.g. an ipython cell) and from
    # this stack get the globals, there get the executed cells history and the last element from it
    return [stack for stack in inspect.stack() if stack.filename.startswith("<ipython-input")][0][0].f_globals["_ih"][-1]


global_files = {}
build_in_open = open
def open(filename: str, *args, **kwargs):
    """ open a file and if its a jupyter cell then mock a filepointer to that cell """
    if filename.startswith("<ipython"):
        class IPythonCell:
            text = None
            write_text = None
            is_cell = False

            def __init__(self, filename, mode, **kwargs):
                self.filename = filename.strip()

                if mode == "r":
                    if self.filename[0] == "<" and self.filename[-1] == ">":
                        self.is_cell = True
                        self.text = getIpythonCurrentCell()
                    else:
                        self.text = global_files[filename]
                if mode == "w":
                    self.write_text = ""

            def __iter__(self):
                text = self.text
                while len(text):
                    pos = text.find("\n")
                    if pos == -1:
                        yield text
                        break
                    yield text[:pos+1]
                    text = text[pos+1:]

            def write(self, line):
                if self.write_text is None:
                    self.write_text = ""
                self.write_text += line

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.write_text is not None:
                    if self.filename[0] == "<" and self.filename[-1] == ">":
                        setJupyterCellText(self.write_text)
                    else:
                        global_files[self.filename] = self.write_text

        return IPythonCell(filename, *args, **kwargs)
    else:
        return build_in_open(filename, *args, **kwargs)
