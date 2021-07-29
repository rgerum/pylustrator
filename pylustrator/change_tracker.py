#!/usr/bin/env python
# -*- coding: utf-8 -*-
# change_tracker.py

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

import re
import sys
import traceback
from typing import IO

import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers
from matplotlib.artist import Artist
from matplotlib.axes._subplots import Axes
from matplotlib.collections import Collection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from natsort import natsorted

from .exception_swallower import Dummy
from .jupyter_cells import open


""" External overload """
class CustomStackPosition:
    filename = None
    lineno = None
    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno
custom_stack_position = None
custom_prepend = ""
custom_append = ""

escape_pairs = [
    ("\\", "\\\\"),
    ("\n", "\\n"),
    ("\r", "\\r"),
    ("\"", "\\\""),
]
def escape_string(str):
    for pair in escape_pairs:
        str = str.replace(pair[0], pair[1])
    return str

def unescape_string(str):
    for pair in escape_pairs:
        str = str.replace(pair[1], pair[0])
    return str

def getReference(element: Artist, allow_using_variable_names=True):
    """ get the code string that represents the given Artist. """
    if element is None:
        return ""
    if isinstance(element, Figure):
        if allow_using_variable_names:
            name = getattr(element, "_variable_name", None)
            if name is not None:
                return name
        if isinstance(element.number, (float, int)):
            return "plt.figure(%s)" % element.number
        else:
            return "plt.figure(\"%s\")" % element.number
    if isinstance(element, matplotlib.lines.Line2D):
        index = element.axes.lines.index(element)
        return getReference(element.axes) + ".lines[%d]" % index
    if isinstance(element, matplotlib.collections.Collection):
        index = element.axes.collections.index(element)
        return getReference(element.axes) + ".collections[%d]" % index
    if isinstance(element, matplotlib.patches.Patch):
        if element.axes:
            index = element.axes.patches.index(element)
            return getReference(element.axes) + ".patches[%d]" % index
        index = element.figure.patches.index(element)
        return getReference(element.figure) + ".patches[%d]" % (index)

    if isinstance(element, matplotlib.text.Text):
        if element.axes:
            try:
                index = element.axes.texts.index(element)
            except ValueError:
                for attribute_name in ["title", "_left_title", "_right_title"]:
                    if getattr(element.axes, attribute_name, None) == element:
                        return getReference(element.axes) + "." + attribute_name
                pass
            else:
                return getReference(element.axes) + ".texts[%d]" % index
        try:
            index = element.figure.texts.index(element)
            return getReference(element.figure) + ".texts[%d]" % (index)
        except ValueError:
            pass
        for axes in element.figure.axes:
            if element == axes.get_xaxis().get_label():
                return getReference(axes) + ".get_xaxis().get_label()"
            if element == axes.get_yaxis().get_label():
                return getReference(axes) + ".get_yaxis().get_label()"

            for index, label in enumerate(axes.get_xaxis().get_major_ticks()):
                if element == label.label1:
                    return getReference(axes) + ".get_xaxis().get_major_ticks()[%d].label1" % index
                if element == label.label2:
                    return getReference(axes) + ".get_xaxis().get_major_ticks()[%d].label2" % index
            for index, label in enumerate(axes.get_xaxis().get_minor_ticks()):
                if element == label.label1:
                    return getReference(axes) + ".get_xaxis().get_minor_ticks()[%d].label1" % index
                if element == label.label2:
                    return getReference(axes) + ".get_xaxis().get_minor_ticks()[%d].label2" % index

            for axes in element.figure.axes:
                for index, label in enumerate(axes.get_yaxis().get_major_ticks()):
                    if element == label.label1:
                        return getReference(axes) + ".get_yaxis().get_major_ticks()[%d].label1" % index
                    if element == label.label2:
                        return getReference(axes) + ".get_yaxis().get_major_ticks()[%d].label2" % index
                for index, label in enumerate(axes.get_yaxis().get_minor_ticks()):
                    if element == label.label1:
                        return getReference(axes) + ".get_yaxis().get_minor_ticks()[%d].label1" % index
                    if element == label.label2:
                        return getReference(axes) + ".get_yaxis().get_minor_ticks()[%d].label2" % index

    if isinstance(element, matplotlib.axes._axes.Axes):
        if element.get_label():
            return getReference(element.figure) + ".ax_dict[\"%s\"]" % escape_string(element.get_label())
        return getReference(element.figure) + ".axes[%d]" % element.number

    if isinstance(element, matplotlib.legend.Legend):
        return getReference(element.axes) + ".get_legend()"
    raise TypeError(str(type(element)) + " not found")


def setFigureVariableNames(figure: Figure):
    """ get the global variable names that refer to the given figure """
    import inspect
    mpl_figure = _pylab_helpers.Gcf.figs[figure].canvas.figure
    calling_globals = inspect.stack()[2][0].f_globals
    fig_names = [
        name
        for name, val in calling_globals.items()
        if isinstance(val, mpl.figure.Figure) and hash(val) == hash(mpl_figure)
    ]
    print("fig_names", fig_names)
    if len(fig_names):
        globals()[fig_names[0]] = mpl_figure
        setattr(mpl_figure, "_variable_name", fig_names[0])


class ChangeTracker:
    """ a class that records a list of the change to the figure """
    changes = None
    saved = True

    def __init__(self, figure: Figure):
        global stack_position
        self.figure = figure
        self.edits = []
        self.last_edit = -1
        self.changes = {}

        # make all the subplots pickable
        for index, axes in enumerate(self.figure.axes):
            # axes.set_title(index)
            axes.number = index

        # store the position where StartPylustrator was called
        if custom_stack_position is None:
            stack_position = traceback.extract_stack()[-4]
        else:
            stack_position = custom_stack_position

        self.fig_inch_size = self.figure.get_size_inches()

        self.load()

    def addChange(self, command_obj: Artist, command: str, reference_obj: Artist = None, reference_command: str = None):
        """ add a change """
        command = command.replace("\n", "\\n")
        if reference_obj is None:
            reference_obj = command_obj
        if reference_command is None:
            reference_command, = re.match(r"(\.[^(=]*)", command).groups()
        self.changes[reference_obj, reference_command] = (command_obj, command)
        self.saved = False

    def removeElement(self, element: Artist):
        """ remove an Artis from the figure """
        # create_key = key+".new"
        created_by_pylustrator = (element, ".new") in self.changes
        # delete changes related to this element
        keys = [k for k in self.changes]
        for reference_obj, reference_command in keys:
            if reference_obj == element:
                del self.changes[reference_obj, reference_command]
        if not created_by_pylustrator:
            self.addChange(element, ".set_visible(False)")
            element.set_visible(False)
        else:
            element.remove()
        self.figure.selection.remove_target(element)

    def addEdit(self, edit: list):
        """ add an edit to the stored list of edits """
        if self.last_edit < len(self.edits) - 1:
            self.edits = self.edits[:self.last_edit + 1]
        self.edits.append(edit)
        self.last_edit = len(self.edits) - 1

    def backEdit(self):
        """ undo an edit in the list """
        if self.last_edit < 0:
            return
        edit = self.edits[self.last_edit]
        edit[0]()
        self.last_edit -= 1
        self.figure.canvas.draw()

    def forwardEdit(self):
        """ redo an edit """
        if self.last_edit >= len(self.edits) - 1:
            return
        edit = self.edits[self.last_edit + 1]
        edit[1]()
        self.last_edit += 1
        self.figure.canvas.draw()

    def load(self):
        """ load a set of changes from a script file. The changes are the code that pylustrator generated """
        regex = re.compile(r"(\.[^\(= ]*)(.*)")
        command_obj_regexes = [getReference(self.figure),
                               r"plt\.figure\([^)]*\)",
                               r"fig",
                               r"\.ax_dict\[\"[^\"]*\"\]",
                               r"\.axes\[\d*\]",
                               r"\.texts\[\d*\]",
                               r"\.{title|_left_title|_right_title}",
                               r"\.lines\[\d*\]",
                               r"\.collections\[\d*\]",
                               r"\.patches\[\d*\]",
                               r"\.get_[xy]axis\(\)\.get_(major|minor)_ticks\(\)\[\d*\]",
                               r"\.get_[xy]axis\(\)\.get_label\(\)",
                               r"\.get_legend\(\)",
                               ]
        command_obj_regexes = [re.compile(r) for r in command_obj_regexes]

        fig = self.figure
        header = []
        header += ["fig = plt.figure(%s)" % self.figure.number]
        header += ["import matplotlib as mpl"]

        self.get_reference_cached = {}

        block = getTextFromFile(getReference(self.figure), stack_position)
        if not block:
            block = getTextFromFile(getReference(self.figure, allow_using_variable_names=False), stack_position)
        for line in block:
            line = line.strip()
            if line == "" or line in header or line.startswith("#"):
                continue
            if re.match(".*\.ax_dict =.*", line):
                continue

            raw_line = line

            # try to identify the command object of the line
            command_obj = ""
            for r in command_obj_regexes:
                try:
                    found = r.match(line).group()
                    line = line[len(found):]
                    command_obj += found
                except AttributeError:
                    pass

            try:
                command, parameter = regex.match(line).groups()
            except AttributeError:  # no regex match
                continue

            m = re.match(r".*# id=(.*)", line)
            if m:
                key = m.groups()[0]
            else:
                key = command_obj + command

            # by default reference and command object are the same
            reference_obj = command_obj
            reference_command = command

            if command == ".set_xticks" or command == ".set_yticks" or command == ".set_xlabels" or command == ".set_ylabels":
                if line.find("minor=True") != -1:
                    reference_command = command + "_minor"

            # for new created texts, the reference object is the text and not the axis/figure
            if command == ".text" or command == ".annotate" or command == ".add_patch":
                reference_obj, _ = re.match(r"(.*)(\..*)", key).groups()
                reference_command = ".new"

            command_obj = eval(command_obj)
            reference_obj_str = reference_obj
            reference_obj = eval(reference_obj)

            # if the reference object is just a dummy, we ignore it
            if isinstance(reference_obj, Dummy):
                print("WARNING: line references a missing object, will remove line on save:", raw_line, file=sys.stderr)
                continue

            self.get_reference_cached[reference_obj] = reference_obj_str

            #print("---", [reference_obj, reference_command], (command_obj, command + parameter))
            self.changes[reference_obj, reference_command] = (command_obj, command + parameter)
        self.sorted_changes()

    def sorted_changes(self):
        """ sort the changes by their priority. For example setting to logscale needs to be executed before xlim. """
        def getRef(obj):
            try:
                return getReference(obj)
            except (ValueError, TypeError):
                # the ticks objects can for some reason not be referenced properly in the next code run
                # they are somehow XTicks objects when loading but when saving they are Text objects
                if obj in self.get_reference_cached:
                    return self.get_reference_cached[obj]
                raise

        indices = []
        for reference_obj, reference_command in self.changes:
            try:
                if isinstance(reference_obj, Figure):
                    obj_indices = ("", "", "", "")
                else:
                    if getattr(reference_obj, "axes", None) is not None:
                        if reference_command == ".new":
                            index = "0"
                        elif reference_command == ".set_xscale" or reference_command == ".set_yscale":
                            index = "1"
                        elif reference_command == ".set_xlim" or reference_command == ".set_ylim":
                            index = "2"
                        elif reference_command == ".set_xticks" or reference_command == ".set_yticks":
                            index = "3"
                        elif reference_command == ".set_xticklabels" or reference_command == ".set_yticklabels":
                            index = "4"
                        else:
                            index = "5"
                        obj_indices = (getRef(reference_obj.axes), getRef(reference_obj), index, reference_command)
                    else:
                        obj_indices = (getRef(reference_obj), "", "", reference_command)
                indices.append(
                    [(reference_obj, reference_command), self.changes[reference_obj, reference_command], obj_indices])
            except (ValueError, TypeError) as err:
                print(err, file=sys.stderr)

        srt = natsorted(indices, key=lambda a: a[2])
        output = []
        for s in srt:
            command_obj, command = s[1]
            try:
                output.append(getRef(command_obj) + command)
            except TypeError as err:
                print(err, file=sys.stderr)

        return output

    def save(self):
        """ save the changes to the .py file """
        header = [getReference(self.figure) + ".ax_dict = {ax.get_label(): ax for ax in " + getReference(
            self.figure) + ".axes}", "import matplotlib as mpl"]

        # block = getTextFromFile(header[0], self.stack_position)
        output = [custom_prepend + "#% start: automatic generated code from pylustrator"]
        # add the lines from the header
        for line in header:
            output.append(line)
        # add all lines from the changes
        for line in self.sorted_changes():
            output.append(line)
            if line.startswith("fig.add_axes"):
                output.append(header[1])
        output.append("#% end: automatic generated code from pylustrator" + custom_append)
        # print("\n".join(output))

        block_id = getReference(self.figure)
        block = getTextFromFile(block_id, stack_position)
        if not block:
            block_id = getReference(self.figure, allow_using_variable_names=False)
            block = getTextFromFile(block_id, stack_position)
        insertTextToFile(output, stack_position, block_id)
        self.saved = True


def getTextFromFile(block_id: str, stack_pos: traceback.FrameSummary):
    """ get the text which corresponds to the block_id (e.g. which figure) at the given position sepcified by stack_pos. """
    block_id = lineToId(block_id)
    block = None

    if not custom_stack_position:
        if not stack_pos.filename.endswith('.py') and not stack_pos.filename.startswith("<ipython-input-"):
            raise RuntimeError("pylustrator must used in a python file (*.py) or a jupyter notebook; not a shell session.")

    with open(stack_pos.filename, 'r', encoding="utf-8") as fp1:
        for lineno, line in enumerate(fp1, start=1):
            # if we are currently reading a pylustrator block
            if block is not None:
                # add the line to the block
                block.add(line)
                # and see if we have found the end
                if line.strip().startswith("#% end:") and line.strip().endswith(custom_append):
                    block.end()
            # if there is a new pylustrator block
            elif line.strip().startswith(custom_prepend + "#% start:"):
                block = Block(line)

            # if we are currently reading a block, continue with the next line
            if block is not None and not block.finished:
                continue

            if block is not None and block.finished:
                if block.id == block_id:
                    return block
            block = None
    return []


class Block:
    """ an object to represent the code block generated by a pylustrator save """
    id = None
    finished = False

    def __init__(self, line: str):
        """ initialize the block with its first line """
        self.text = line
        self.size = 1
        self.indent = getIndent(line)

    def add(self, line: str):
        """ add a line to the block """
        if self.id is None:
            self.id = lineToId(line)
        self.text += line
        self.size += 1

    def end(self):
        """ end the block """
        self.finished = True

    def __iter__(self):
        """ iterate over all the lines of the block """
        return iter(self.text.split("\n"))


def getIndent(line: str):
    """ get the indent part of a line of code """
    i = 0
    for i in range(len(line)):
        if line[i] != " " and line[i] != "\t":
            break
    indent = line[:i]
    return indent


def addLineCounter(fp: IO):
    """ wrap a file pointer to store th line numbers """
    fp.lineno = 0
    write = fp.write

    def write_with_linenumbers(line: str):
        write(line)
        fp.lineno += line.count("\n")

    fp.write = write_with_linenumbers


def lineToId(line: str):
    """ get the id of a line, e.g. part which specifies which figure it refers to """
    line = line.strip()
    line = line.split(".ax_dict")[0]
    if line.startswith("fig = "):
        line = line[len("fig = "):]
    return line


def insertTextToFile(new_block: str, stack_pos: traceback.FrameSummary, figure_id_line: str):
    """ insert a text block into a file """
    figure_id_line = lineToId(figure_id_line)
    block = None
    written = False
    written_end = False
    lineno_stack = None
    # open a temporary file with the same name for writing
    with open(stack_pos.filename + ".tmp", 'w', encoding="utf-8") as fp2:
        addLineCounter(fp2)
        # open the current python file for reading
        with open(stack_pos.filename, 'r', encoding="utf-8") as fp1:
            # iterate over all lines and line numbers
            for fp1.lineno, line in enumerate(fp1, start=1):
                # if we are currently reading a pylustrator block
                if block is not None:
                    # add the line to the block
                    block.add(line)
                    # and see if we have found the end
                    if line.strip().startswith("#% end:") and line.strip().endswith(custom_append):
                        block.end()
                        line = ""
                # if there is a new pylustrator block
                elif line.strip().startswith(custom_prepend + "#% start:"):
                    block = Block(line)

                # if we are currently reading a block, continue with the next line
                if block is not None and not block.finished:
                    continue

                # the current block is finished
                if block is not None:
                    # either it is the block we want to save, then replace the old block with the new
                    if block.id == figure_id_line:
                        # remember that we wrote the new block
                        written = fp2.lineno + 1
                        # write the new block to the target file instead of the current block
                        indent = block.indent
                        for line_text in new_block:
                            fp2.write(indent + line_text + "\n")
                        written_end = fp2.lineno
                    # or it is another block, then we just write it
                    else:
                        # the we just copy the current block into the new file
                        fp2.write(block.text)
                    # we already handled this block
                    block = None

                # if we are at the entry point (e.g. plt.show())
                if fp1.lineno == stack_pos.lineno:
                    # and if we not have written the new block
                    if not written:
                        written = fp2.lineno + 1
                        # we write it now to the target file
                        indent = getIndent(line)
                        for line_text in new_block:
                            fp2.write(indent + line_text + "\n")
                        written_end = fp2.lineno
                    # and we store the position where we will write the entry point (e.g. the plt.show())
                    lineno_stack = fp2.lineno + 1
                # transfer the current line to the new file
                fp2.write(line)

    # update the position of the entry point, as we have inserted stuff in the new file which can change the position
    stack_pos.lineno = lineno_stack

    # now copy the temporary file over the old file
    with open(stack_pos.filename + ".tmp", 'r', encoding="utf-8") as fp2:
        with open(stack_pos.filename, 'w', encoding="utf-8") as fp1:
            for line in fp2:
                fp1.write(line)
    print("save", figure_id_line, "to", stack_pos.filename, "line %d-%d" % (written, written_end))
