from __future__ import division, print_function

import re
import traceback

import matplotlib
from matplotlib.axes._subplots import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
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
        stack_position = traceback.extract_stack()[-4]

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
        header = ["fig = plt.figure(%s)" % self.figure.number, "import matplotlib as mpl",
                  "fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}"]

        block = getTextFromFile(header[0], stack_position)
        for line in block:
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

            # by default reference and command object are the same
            reference_obj = command_obj
            reference_command = command

            if command == ".set_xticks" or command == ".set_yticks" or command == ".set_xlabels" or command == ".set_ylabels":
                if line.find("minor=True"):
                    reference_command = command + "_minor"

            # for new created texts, the reference object is the text and not the axis/figure
            if command == ".text" or command == ".annotate" or command == ".add_patch":
                reference_obj, _ = re.match(r"(.*)(\..*)", key).groups()
                reference_command = ".new"

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
        header = ["fig = plt.figure(%s)" % self.figure.number, "import matplotlib as mpl",
                  "fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}"]

        # block = getTextFromFile(header[0], self.stack_position)
        output = ["#% start: automatic generated code from pylustrator"]
        # add the lines from the header
        for line in header:
            output.append(line)
        # add all lines from the changes
        for line in self.sorted_changes():
            output.append(line)
            if line.startswith("fig.add_axes"):
                output.append(header[1])
        output.append("#% end: automatic generated code from pylustrator")
        # print("\n".join(output))
        insertTextToFile(output, stack_position, header[0])
        self.saved = True


def getTextFromFile(block_id, stack_pos):
    block = None
    with open(stack_pos.filename, 'r', encoding="utf-8") as fp1:
        for lineno, line in enumerate(fp1, start=1):
            # if we are currently reading a pylustrator block
            if block is not None:
                # add the line to the block
                block.add(line)
                # and see if we have found the end
                if line.strip().startswith("#% end:"):
                    block.end()
            # if there is a new pylustrator block
            elif line.strip().startswith("#% start:"):
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
    id = None
    finished = False

    def __init__(self, line):
        self.text = line
        self.size = 1
        self.indent = getIndent(line)

    def add(self, line):
        if self.id is None:
            self.id = line.strip()
        self.text += line
        self.size += 1

    def end(self):
        self.finished = True

    def __iter__(self):
        return iter(self.text.split("\n"))


def getIndent(line):
    i = 0
    for i in range(len(line)):
        if line[i] != " " and line[i] != "\t":
            break
    indent = line[:i]
    return indent


def addLineCounter(fp):
    fp.lineno = 0
    write = fp.write

    def write_with_linenumbers(line):
        write(line)
        fp.lineno += line.count("\n")

    fp.write = write_with_linenumbers


def insertTextToFile(new_block, stack_pos, figure_id_line):
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
                    if line.strip().startswith("#% end:"):
                        block.end()
                        line = ""
                # if there is a new pylustrator block
                elif line.strip().startswith("#% start:"):
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
