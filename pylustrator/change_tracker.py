from __future__ import division, print_function
import numpy as np
import traceback
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Ellipse
from matplotlib.figure import Figure
from matplotlib.axes._subplots import Axes
import matplotlib
import uuid
import re
from natsort import natsorted


def getReference(element):
    if element is None:
        return ""
    if isinstance(element, Figure):
        return "fig"
    if isinstance(element, matplotlib.lines.Line2D):
        index = element.axes.lines.index(element)
        return getReference(element.axes) + ".lines[%d]" % index
    if isinstance(element, matplotlib.patches.Patch):
        if element.axes:
            index = element.axes.patches.index(element)
            return getReference(element.axes) + ".patches[%d]" % index
        print("rect, ", element.get_label())
        index = element.figure.patches.index(element)
        return "fig.patches[%d]" % (index)
    if isinstance(element, matplotlib.text.Text):
        if element.axes:
            try:
                index = element.axes.texts.index(element)
            except ValueError:
                pass
            else:
                return getReference(element.axes) + ".texts[%d]" % index
        try:
            index = element.figure.texts.index(element)
            return "fig.texts[%d]" % (index)
        except ValueError:
            pass
        for axes in element.figure.axes:
            if element == axes.get_xaxis().get_label():
                return getReference(axes) + ".get_xaxis().get_label()"
            if element == axes.get_yaxis().get_label():
                return getReference(axes) + ".get_yaxis().get_label()"
    if isinstance(element, matplotlib.axes._axes.Axes):
        if element.get_label():
            return "fig.ax_dict[\"%s\"]" % element.get_label()
        return "fig.axes[%d]" % element.number
    if isinstance(element, matplotlib.legend.Legend):
        return getReference(element.axes) + ".get_legend()"
    raise (TypeError(str(type(element)) + " not found"))


class ChangeTracker:
    changes = None
    saved = True

    def __init__(self, figure):
        self.figure = figure
        self.edits = []
        self.last_edit = -1
        self.changes = {}

        # make all the subplots pickable
        for index, axes in enumerate(self.figure.axes):
            # axes.set_title(index)
            axes.number = index

        # store the position where StartPylustrator was called
        self.stack_position = traceback.extract_stack()[-4]

        self.fig_inch_size = self.figure.get_size_inches()

        self.load()

    def addChange(self, command_obj, command, reference_obj=None, reference_command=None):
        command = command.replace("\n", "\\n")
        if reference_obj is None:
            reference_obj = command_obj
        if reference_command is None:
            reference_command, = re.match(r"(\.[^(=]*)", command).groups()
        self.changes[reference_obj, reference_command] = (command_obj, command)
        self.saved = False

    def removeElement(self, element):
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

    def addEdit(self, edit):
        if self.last_edit < len(self.edits) - 1:
            self.edits = self.edits[:self.last_edit + 1]
        self.edits.append(edit)
        self.last_edit = len(self.edits) - 1

    def backEdit(self):
        if self.last_edit < 0:
            return
        edit = self.edits[self.last_edit]
        edit[0]()
        self.last_edit -= 1
        self.figure.canvas.draw()

    def forwardEdit(self):
        if self.last_edit >= len(self.edits) - 1:
            return
        edit = self.edits[self.last_edit + 1]
        edit[1]()
        self.last_edit += 1
        self.figure.canvas.draw()

    def load(self):
        regex = re.compile(r"(\.[^\(= ]*)(.*)")
        command_obj_regexes = [r"fig",
                               r"\.ax_dict\[\"[^\"]*\"\]",
                               r"\.axes\[\d*\]",
                               r"\.texts\[\d*\]",
                               r"\.patches\[\d*\]",
                               r"\.get_legend()",
                               ]
        command_obj_regexes = [re.compile(r) for r in command_obj_regexes]

        fig = self.figure
        header = ["fig = plt.figure(%s)" % self.figure.number, "import matplotlib as mpl", "fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}"]

        block = getTextFromFile(header[0], self.stack_position)
        for lineno, line in block:
            line = line.strip()
            if line == "" or line in header or line.startswith("#"):
                continue

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

            if command == ".set_xticks" or command == ".set_yticks" or command == ".set_xlabels" or command == ".set_ylabels":
                if line.find("minor=True"):
                    reference_command = command+"_minor"

            if command == ".text" or command == ".annotate" or command == ".add_patch":
                # if lineno in plt.keys_for_lines:
                #    key = plt.keys_for_lines[lineno]
                #    print("linoeno", key)
                reference_obj, _ = re.match(r"(.*)(\..*)", key).groups()
                reference_command = ".new"
            else:
                reference_obj = command_obj
                reference_command = command

            command_obj = eval(command_obj)
            reference_obj = eval(reference_obj)

            self.changes[reference_obj, reference_command] = (command_obj, command + parameter)
        self.sorted_changes()

    def sorted_changes(self):
        indices = []
        for reference_obj, reference_command in self.changes:
            obj_indices = ("", "", "")
            if isinstance(reference_obj, Figure):
                obj_indices = ("", "", "")
            if isinstance(reference_obj, matplotlib.axes._axes.Axes):
                obj_indices = (getReference(reference_obj), "", "")
            if isinstance(reference_obj, matplotlib.text.Text) or isinstance(reference_obj, matplotlib.patches.Patch):
                if reference_command == ".new":
                    index = "0"
                else:
                    index = "1"
                obj_indices = (getReference(reference_obj.axes), getReference(reference_obj), index)
            indices.append(
                [(reference_obj, reference_command), self.changes[reference_obj, reference_command], obj_indices])

        srt = natsorted(indices, key=lambda a: a[2])
        output = []
        for s in srt:
            command_obj, command = s[1]
            try:
                output.append(getReference(command_obj) + command)
            except TypeError as err:
                print(err)
        return output

    def save(self):
        header = ["fig = plt.figure(%s)" % self.figure.number, "import matplotlib as mpl", "fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}"]

        # block = getTextFromFile(header[0], self.stack_position)
        output = ["#% start: automatic generated code from pylustrator"]
        for line in header:
            output.append(line)
        """
        for lineno, line in block:
            line = line.strip()
            if line == "":
                continue
            if line in header:
                continue
            for key in self.changes:
                if line.startswith(key) or line.endswith(key):
                    break
            else:
                output.append(line)
        """
        for line in self.sorted_changes():
            output.append(line)
            if line.startswith("fig.add_axes"):
                output.append(header[1])
        output.append("#% end: automatic generated code from pylustrator")
        print("\n".join(output))
        insertTextToFile(output, self.stack_position)
        self.saved = True
        
        

def getTextFromFile(marker, stack_pos):
    block_active = False
    block = []
    last_block = -10
    written = False
    with open(stack_pos.filename, 'r', encoding="utf-8") as fp1:
        for lineno, line in enumerate(fp1):
            if block_active:
                if line.strip().startswith("#% end:"):
                    block_active = False
                    last_block = lineno
                    if block[0][1].strip() == marker.strip():
                        break
                    block = []
                block.append([lineno+1, line])
            elif line.strip().startswith("#% start:"):
                #block = block + line
                block_active = True
            if block_active:
                continue
    return block


def insertTextToFile(text, stack_pos):
    block_active = False
    block = ""
    last_block = -10
    written = False
    with open(stack_pos.filename + ".tmp", 'w', encoding="utf-8") as fp2:
        with open(stack_pos.filename, 'r', encoding="utf-8") as fp1:
            for lineno, line in enumerate(fp1):
                if block_active:
                    block = block + line
                    if line.strip().startswith("#% end:"):
                        block_active = False
                        last_block = lineno
                        continue
                elif line.strip().startswith("#% start:"):
                    block = block + line
                    block_active = True
                if block_active:
                    continue
                # print(lineno, stack_pos.lineno, last_block)
                if not written and (lineno == stack_pos.lineno - 1 or last_block == lineno - 1):
                    for i in range(len(line)):
                        if line[i] != " " and line[i] != "\t":
                            break
                    indent = line[:i]
                    for line_text in text:
                        fp2.write(indent + line_text + "\n")
                    written = True
                    last_block = -10
                    block = ""
                elif last_block == lineno - 1:
                    fp2.write(block)
                fp2.write(line)

    with open(stack_pos.filename + ".tmp", 'r', encoding="utf-8") as fp2:
        with open(stack_pos.filename, 'w', encoding="utf-8") as fp1:
            for line in fp2:
                fp1.write(line)
    print("Save to", stack_pos.filename, "line", stack_pos.lineno)

