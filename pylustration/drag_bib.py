from __future__ import division, print_function
import numpy as np
import traceback
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Ellipse

DIR_X0 = 1
DIR_Y0 = 2
DIR_X1 = 4
DIR_Y1 = 8


class FigureDragger:
    last_picked = False
    active_object = None
    drag_object = None
    fig = None
    first_resize = True
    displaying = False
    snaps = None

    def __init__(self, fig, xsnaps=None, ysnaps=None, unit="cm"):
        self.fig = fig
        # store dragger, so that it is not eaten by the garbage collector
        fig.figure_dragger = self
        self.grabbers = []

        # make all the subplots pickable
        for axes in self.fig.axes:
            axes.set_picker(True)
            leg = axes.get_legend()
            if leg:
                leg.draggable(use_blit=True)
            for text in axes.texts:
                dragger = DraggableText(text, use_blit=True)
                text._draggable = dragger

            dragger = DraggableAxes(axes, use_blit=True)
            axes._draggable = dragger

        # store the position where StartPylustration was called
        self.stack_position = traceback.extract_stack()[-3]

        self.fig_inch_size = fig.get_size_inches()

        self.snaps = []
        if xsnaps is not None:
            for x in xsnaps:
                if unit == "cm":
                    x = x / 2.54 / fig.get_size_inches()[0]
                if x < 0:
                    x = 1 + x
                plt.plot([x, x], [0, 1], '-', color=[0.8, 0.8, 0.8], transform=fig.transFigure, clip_on=False, lw=1,
                         zorder=-10)
                self.snaps.append(Snap(x, None, [x, x], [0, 1]))
        if ysnaps is not None:
            for y in ysnaps:
                if unit == "cm":
                    y = y / 2.54 / fig.get_size_inches()[1]
                if y < 0:
                    y = 1 + y
                plt.plot([0, 1], [y, y], '-', color=[0.8, 0.8, 0.8], transform=fig.transFigure, clip_on=False, lw=1,
                         zorder=-10)
                self.snaps.append(Snap(None, y, [0, 1], [y, y]))

        # add a text showing the figure size
        self.text = plt.text(0, 0, "", transform=self.fig.transFigure, clip_on=False, zorder=100)

        # connect event callbacks
        #fig.canvas.mpl_connect("pick_event", self.on_pick_event)
        #fig.canvas.mpl_connect('button_press_event', self.mouse_down_event)
        #fig.canvas.mpl_connect('motion_notify_event', self.mouse_move_event)
        #fig.canvas.mpl_connect('button_release_event', self.mouse_up_event)
        fig.canvas.mpl_connect('key_press_event', self.key_press_event)
        #fig.canvas.mpl_connect('draw_event', self.draw_event)
        fig.canvas.mpl_connect('resize_event', self.resize_event)
        #fig.canvas.mpl_connect('scroll_event', self.scroll_event)

    def draw(self):
        # only draw if the canvas is not already drawing
        if not self.displaying:
            # store the drawing state
            self.displaying = True
            # remove events
            self.fig.canvas.flush_events()
            # draw the canvas
            self.fig.canvas.draw()

    def draw_event(self, event):
        # set the drawing state back to false
        self.displaying = False

    def key_press_event(self, event):
        # space: print code to restore current configuration
        if event.key == ' ':
            # print comment that the block starts
            save_text = "#% start: automatic generated code from pylustration\n"
            # get the figure by its name
            save_text += "fig = plt.figure(%s)\n" % self.fig.number
            # set the size of the figure
            save_text += "fig.set_size_inches(%f/2.54, %f/2.54, forward=True)\n" % (
                (self.fig.get_size_inches()[0] - self.inch_offset[0]) * 2.54,
                (self.fig.get_size_inches()[1] - self.inch_offset[1]) * 2.54)
            # iterate over all axes
            for index, ax in enumerate(self.fig.axes):
                # get the position of the axes
                pos = ax.get_position()
                # and set the position
                save_text += "fig.axes[%d].set_position([%f, %f, %f, %f])\n" % (
                    index, pos.x0, pos.y0, pos.width, pos.height)
                # set the zorder of the figure
                if ax.get_zorder() != 0:
                    save_text += "fig.axes[%d].set_zorder(%d)\n" % (index, ax.get_zorder())

                # check if the axes has a legend
                leg = ax.get_legend()
                if leg:
                    # if the location is a tuple
                    loc = leg._get_loc()
                    if isinstance(loc, tuple):
                        # set the position of the legend
                        save_text += "fig.axes[%d].get_legend()._set_loc(%s)\n" % (index, loc)

                # iterate over the texts in the axes
                for index2, txt in enumerate(ax.texts):
                    # if the text is pickable...
                    if txt.pickable():
                        # ...store its position
                        pos = txt.get_position()
                        save_text += "fig.axes[%d].texts[%d].set_position([%f, %f])\n" % (index, index2, pos[0], pos[1])
            for index, txt in enumerate(self.fig.texts):
                if txt.pickable():
                    pos = txt.get_position()
                    save_text += "fig.texts[%d].set_position([%f, %f])\n" % (index, pos[0], pos[1])
            save_text += "#% end: automatic generated code from pylustration"
            print(save_text)
            insertTextToFile(save_text, self.stack_position)

    def resize_event(self, event):
        # on the first resize (when the figure window plops up) store the additional size (edit toolbar and stuff)
        if self.first_resize:
            self.first_resize = False
            # store the offset of the figuresize
            self.inch_offset = np.array(self.fig.get_size_inches()) - np.array(self.fig_inch_size)
        # draw the text with the figure size
        offx, offy = self.fig.transFigure.inverted().transform([5, 5])
        self.text.set_position([offx, offy])
        self.text.set_text("%.2f x %.2f cm" % (
            (self.fig.get_size_inches()[0] - self.inch_offset[0]) * 2.54,
            (self.fig.get_size_inches()[1] - self.inch_offset[1]) * 2.54))

    def scroll_event(self, event):
        inches = np.array(self.fig.get_size_inches()) - self.inch_offset
        old_dpi = self.fig.get_dpi()
        new_dpi = self.fig.get_dpi() + 10 * event.step
        self.inch_offset /= old_dpi / new_dpi
        self.fig.set_dpi(self.fig.get_dpi() + 10 * event.step)
        self.fig.canvas.draw()
        self.fig.set_size_inches(inches + self.inch_offset, forward=True)
        print(self.fig_inch_size, self.fig.get_size_inches())
        self.resize_event(None)
        print(self.fig_inch_size, self.fig.get_size_inches())
        print("---")
        self.draw()
        print(self.fig_inch_size, self.fig.get_size_inches())
        self.resize_event(None)
        print(self.fig_inch_size, self.fig.get_size_inches())
        print("###")


def moveArtist(index, x1, y1, x2, y2):
    positions = []
    artists = []
    for index2, artist in enumerate(plt.gcf().axes[index].get_children()):
        if artist.pickable():
            try:
                positions.append(artist.original_pos)
            except:
                positions.append(artist.get_position())
            artists.append(artist)
    distance = np.linalg.norm(np.array([x1, y1]) - np.array(positions), axis=1)
    print(np.min(distance), np.array([x2, y2]), np.array(positions).shape)
    index = np.argmin(distance)
    try:
        artists[index].original_pos
    except:
        artists[index].original_pos = [x1, y1]
    print("########", artist)
    artists[index].set_position([x2, y2])


def insertTextToFile(text, stack_pos):
    block_active = False
    block = ""
    last_block = -10
    written = False
    with open(stack_pos.filename + ".tmp", 'w') as fp2:
        with open(stack_pos.filename, 'r') as fp1:
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
                    for line_text in text.split("\n"):
                        fp2.write(indent + line_text + "\n")
                    written = True
                    last_block = -10
                    block = ""
                elif last_block == lineno - 1:
                    fp2.write(block)
                fp2.write(line)

    with open(stack_pos.filename + ".tmp", 'r') as fp2:
        with open(stack_pos.filename, 'w') as fp1:
            for line in fp2:
                fp1.write(line)
    print("Save to", stack_pos.filename, "line", stack_pos.lineno)


class Snap(Line2D):
    def __init__(self, x, y, draw_x, draw_y, transform=-1):
        if transform == -1:
            transform = plt.gcf().transFigure
            self.x, _ = plt.gcf().transFigure.transform((x, 1))
            _, self.y = plt.gcf().transFigure.transform((1, y))
        else:
            self.x, self.y = x, y
        self.draw_x = draw_x
        self.draw_y = draw_y
        Line2D.__init__(self, [], [], transform=transform, clip_on=False, lw=1, zorder=100, linestyle="dashed",
                        color="r", marker="o", ms=1)
        plt.gca().add_artist(self)

    def checkSnap(self, x, y):
        if self.x is not None and abs(x - self.x) < 10:
            x = self.x
        if self.y is not None and abs(y - self.y) < 10:
            y = self.y
        return x, y

    def checkSnapActive(self, *args):
        for x, y in args:
            if self.x is not None and abs(x - self.x) < 1:
                self.set_data((self.draw_x, self.draw_y))
                break
            if self.y is not None and abs(y - self.y) < 1:
                self.set_data((self.draw_x, self.draw_y))
                break
        else:
            self.set_data((), ())

    def hide(self):
        self.set_data((), ())

    def remove(self):
        self.set_data((), ())
        try:
            self.axes.artists.remove(self)
        except ValueError:
            pass


def getSnaps(target, dir, no_height=False):
    snaps = []
    pos0 = target.get_position()
    for axes in target.figure.axes:
        if axes != target:
            pos1 = axes.get_position()
            # axes edged
            snaps.append(Snap(pos1.x0, None, (pos1.x0, pos1.x0), (0, 1)))
            snaps.append(Snap(pos1.x1, None, (pos1.x1, pos1.x1), (0, 1)))
            snaps.append(Snap(None, pos1.y0, (0, 1), (pos1.y0, pos1.y0)))
            snaps.append(Snap(None, pos1.y1, (0, 1), (pos1.y1, pos1.y1)))
            # same height or width
            if not no_height:
                if dir & DIR_X1:
                    snaps.append(
                        Snap(pos0.x0 + pos1.width, None, (pos0.x0, pos0.x0 + pos1.width, np.nan, pos1.x0, pos1.x1), (
                            pos0.y0 + pos0.height / 2, pos0.y0 + pos0.height / 2, np.nan, pos1.y0 + pos1.height / 2,
                            pos1.y0 + pos1.height / 2)))
                if dir & DIR_X0:
                    snaps.append(
                        Snap(pos0.x1 - pos1.width, None, (pos0.x1, pos0.x1 - pos1.width, np.nan, pos1.x0, pos1.x1), (
                            pos0.y0 + pos0.height / 2, pos0.y0 + pos0.height / 2, np.nan, pos1.y0 + pos1.height / 2,
                            pos1.y0 + pos1.height / 2)))
                if dir & DIR_Y1:
                    snaps.append(Snap(None, pos0.y0 + pos1.height, (
                        pos0.x0 + pos0.width / 2, pos0.x0 + pos0.width / 2, np.nan, pos1.x0 + pos1.width / 2,
                        pos1.x0 + pos1.width / 2), (pos0.y0, pos0.y0 + pos1.height, np.nan, pos1.y0, pos1.y1)))
                if dir & DIR_Y0:
                    snaps.append(Snap(None, pos0.y1 - pos1.height, (
                        pos0.x0 + pos0.width / 2, pos0.x0 + pos0.width / 2, np.nan, pos1.x0 + pos1.width / 2,
                        pos1.x0 + pos1.width / 2), (pos0.y1, pos0.y1 - pos1.height, np.nan, pos1.y0, pos1.y1)))
            # same distances
            for axes2 in target.figure.axes:
                if axes2 != axes and axes2 != target:
                    pos2 = axes2.get_position()
                    if pos1.x1 < pos2.x0:
                        if dir & DIR_X0:
                            snaps.append(Snap(pos2.x1 + (pos2.x0 - pos1.x1), None, (
                                pos2.x1, pos2.x1 + (pos2.x0 - pos1.x1), np.nan, pos1.x1, pos2.x0),
                                                   [pos0.y0 + pos0.height / 2] * 5))
                        if dir & DIR_X1:
                            snaps.append(Snap(pos1.x0 - (pos2.x0 - pos1.x1), None, (
                                pos1.x0, pos1.x0 - (pos2.x0 - pos1.x1), np.nan, pos1.x1, pos2.x0),
                                                   [pos0.y0 + pos0.height / 2] * 5))
    return snaps


class Grabber(object):
    fig = None
    target = None
    dir = None
    snaps = None

    got_artist = False

    def __init__(self, parent, x, y, artist, dir):
        self.parent = parent
        self.axes_pos = (x, y)
        self.fig = artist.figure
        self.target = artist
        self.dir = dir
        self.snaps = []
        self.updatePos()
        pos = self.target.get_position()
        self.aspect = pos.width / pos.height
        self.height = pos.height
        self.width = pos.width
        self.fix_aspect = self.target.get_aspect() != "auto" and self.target.get_adjustable() != "datalim"

        c2 = self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        c3 = self.fig.canvas.mpl_connect('button_release_event', self.on_release)

        self.cids = [c2, c3]

    def on_motion(self, evt):
        if self.got_artist:
            if self.parent.blit_initialized is False:
                self.parent.initBlit()

            self.movedEvent(evt)

            self.parent.doBlit()

    def on_pick(self, evt):
        if evt.artist == self:
            self.got_artist = True

            self._c1 = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.clickedEvent(evt)

    def on_release(self, event):
        if self.got_artist:
            self.got_artist = False
            self.fig.canvas.mpl_disconnect(self._c1)
            self.releasedEvent(event)

    def get_xy(self):
        return self.center

    def set_xy(self, xy):
        self.center = xy

    def getPos(self):
        x, y = self.get_xy()
        return self.fig.transFigure.inverted().transform((x, y))

    def updatePos(self):
        x, y = self.target.transAxes.transform(self.axes_pos)
        self.set_xy((x, y))

    def clickedEvent(self, event):
        self.snaps = []
        #self.snaps.extend(self.parent.snaps)
        self.snap_index_offset = 0#len(self.snaps)
        self.snaps.extend(getSnaps(self.target, self.dir))

    def releasedEvent(self, event):
        for snap in self.snaps[self.snap_index_offset:]:
            snap.remove()
        self.snaps = self.snaps[self.snap_index_offset:]

    def movedEvent(self, event):
        x, y = event.x, event.y
        for snap in self.snaps:
            x, y = snap.checkSnap(x, y)
        for snap in self.snaps:
            snap.checkSnapActive((x, y))
        self.set_xy((x, y))
        x, y = self.getPos()
        axes = self.target
        pos = axes.get_position()
        modifier = "control" in event.key.split("+") if event.key is not None else False
        if self.dir & DIR_X0:
            pos.x0 = x
        if self.dir & DIR_Y0:
            pos.y0 = y
        if self.dir & DIR_X1:
            pos.x1 = x
        if self.dir & DIR_Y1:
            pos.y1 = y

        if self.fix_aspect or modifier:
            if self.dir & DIR_Y0 and not self.dir & DIR_X1 or (self.dir & DIR_X0 and self.dir & DIR_Y1):
                pos.x0 = pos.x1 - pos.height * self.aspect
            if self.dir & DIR_Y1 and not self.dir & DIR_X0:
                pos.x1 = pos.x0 + pos.height * self.aspect
            if self.dir & DIR_X0 and not self.dir & DIR_Y1 or (self.dir & DIR_X1 and self.dir & DIR_Y0):
                pos.y0 = pos.y1 - pos.width / self.aspect
            if self.dir & DIR_X1 and not self.dir & DIR_Y0:
                pos.y1 = pos.y0 + pos.width / self.aspect

        axes.set_position(pos)
        self.parent.updateGrabbers()
        #self.fig.canvas.draw()

    def keyPressEvent(self, event):
        pass


class GrabberRound(Ellipse, Grabber):
    w = 10

    def __init__(self, parent, x, y, artist, dir):
        Grabber.__init__(self, parent, x, y, artist, dir)
        Ellipse.__init__(self, (0, 0), self.w, self.w, picker=True, figure=artist.figure, edgecolor="k", zorder=1000)
        self.fig.patches.append(self)
        self.updatePos()


class GrabberRectangle(Rectangle, Grabber):
    w = 10

    def __init__(self, parent, x, y, artist, dir):
        Rectangle.__init__(self, (0, 0), self.w, self.w, picker=True, figure=artist.figure, edgecolor="k", zorder=1000)
        Grabber.__init__(self, parent, x, y, artist, dir)
        self.fig.patches.append(self)
        self.updatePos()

    def get_xy(self):
        xy = Rectangle.get_xy(self)
        return xy[0] + self.w / 2, xy[1] + self.w / 2

    def set_xy(self, xy):
        Rectangle.set_xy(self, (xy[0] - self.w / 2, xy[1] - self.w / 2))


class AxesGrabber(Grabber):

    def clickedEvent(self, event):
        Grabber.clickedEvent(self, event)
        axes = self.target
        pos = axes.get_position()
        x, y = self.fig.transFigure.transform((pos.x0, pos.y0))
        self.drag_offset = (event.mouseevent.x - x, event.mouseevent.y - y)

    def movedEvent(self, event):
        x, y = event.x - self.drag_offset[0], event.y - self.drag_offset[1]
        w, h = self.fig.transFigure.transform((self.width, self.height))
        for snap in self.snaps:
            x, y = snap.checkSnap(x, y)
            x1, y1 = snap.checkSnap(x + w, y + h)
            x, y = x1 - w, y1 - h
        for snap in self.snaps:
            snap.checkSnapActive((x, y), (x + w, y + h))
        self.set_xy((x, y))
        x, y = self.getPos()
        axes = self.target
        pos = axes.get_position()

        pos.x0 = x
        pos.y0 = y
        pos.x1 = x + self.width
        pos.y1 = y + self.height

        axes.set_position(pos)
        self.updateGrabbers()

    def moveAxes(self, x, y):
        pos = self.target.get_position()
        self.target.set_position([pos.x0 + x, pos.y0 + y, pos.width, pos.height])
        self.updateGrabbers()
        self.parent.draw()

    def keyPressEvent(self, event):
        # move last axis in z order
        if event.key == 'pagedown':
            self.target.set_zorder(self.target.get_zorder() - 1)
            self.parent.draw()
        if event.key == 'pageup':
            self.target.set_zorder(self.target.get_zorder() + 1)
            self.parent.draw()
        if event.key == 'left':
            self.moveAxes(-0.01, 0)
        if event.key == 'right':
            self.moveAxes(+0.01, 0)
        if event.key == 'down':
            self.moveAxes(0, -0.01)
        if event.key == 'up':
            self.moveAxes(0, +0.01)


from matplotlib.offsetbox import DraggableBase

def on_pick_wrap(func):
    def on_pick(self, evt):
        func(self, evt)
        if evt.artist != self.ref_artist:
            self.on_release(evt)
    return on_pick

DraggableBase.on_pick = on_pick_wrap(DraggableBase.on_pick)

class DraggableAxes(DraggableBase):
    selected = False
    blit_initialized = False

    def __init__(self, axes, use_blit=False):
        DraggableBase.__init__(self, axes, use_blit=use_blit)
        self.axes = axes
        self.cids.append(self.canvas.mpl_connect('key_press_event', self.keyPressEvent))
        self.grabbers = []

    def initBlit(self):
        self.blit_initialized = True

        self.ref_artist.set_animated(True)
        for grabber in self.grabbers:
            grabber.set_animated(True)
            for snap in grabber.snaps:
                snap.set_animated(True)
        for snaps in self.snaps:
            for snap in snaps:
                snap.set_animated(True)

        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.ref_artist.figure.bbox)

    def finishBlit(self):
        self.blit_initialized = False
        self.ref_artist.set_animated(False)
        for grabber in self.grabbers:
            grabber.set_animated(False)
            for snap in grabber.snaps:
                snap.hide()
                snap.set_animated(False)
        self.canvas.draw()

    def doBlit(self):
        self.canvas.restore_region(self.background)
        self.ref_artist.draw(self.ref_artist.figure._cachedRenderer)
        for grabber in self.grabbers:
            grabber.draw(self.ref_artist.figure._cachedRenderer)
            for snap in grabber.snaps:
                snap.draw(self.ref_artist.figure._cachedRenderer)
        for snaps in self.snaps:
            for snap in snaps:
                snap.draw(self.ref_artist.figure._cachedRenderer)
        self.canvas.blit(self.ref_artist.figure.bbox)

    def on_motion_blit(self, evt):
        if self.got_artist:
            if self.blit_initialized is False:
                self.initBlit()

            dx = evt.x - self.mouse_x
            dy = evt.y - self.mouse_y
            self.update_offset(dx, dy)
            self.doBlit()

    def on_pick(self, evt):
        if evt.artist == self.ref_artist:

            self.mouse_x = evt.mouseevent.x
            self.mouse_y = evt.mouseevent.y
            self.got_artist = True

            if self._use_blit:
                self._c1 = self.canvas.mpl_connect('motion_notify_event',
                                                   self.on_motion_blit)
            else:
                self._c1 = self.canvas.mpl_connect('motion_notify_event',
                                                   self.on_motion)
            self.save_offset()
        if evt.artist != self.ref_artist:
            self.on_release(evt)

    def on_release(self, event):
        if self.got_artist:
            self.finalize_offset()
            self.got_artist = False
            self.canvas.mpl_disconnect(self._c1)

        if self._use_blit and self.blit_initialized:
            self.finishBlit()

        if getattr(event, "inaxes", 0) is None and self.selected:
            self.deselectArtist()

        new_artist = getattr(event, "artist", None)
        if new_artist and new_artist != self.axes and self.selected:
            if getattr(new_artist, "parent", None) != self:
                self.deselectArtist()

    def addGrabber(self, x, y, artist, dir, GrabberClass):
        # add a grabber object at the given coordinates
        self.grabbers.append(GrabberClass(self, x, y, artist, dir))

    def updateGrabbers(self):
        for grabber in self.grabbers:
            grabber.updatePos()

    def on_releasexxx(self, event):
        DraggableBase.on_release(self, event)
        new_artist = getattr(event, "artist", None)
        if new_artist and new_artist != self.axes and self.selected:
            if getattr(new_artist, "parent", None) != self:
                self.deselectArtist()

    def deselectArtist(self):
        self.selected = False
        # remove all grabbers when an artist is deselected
        for grabber in self.grabbers[::-1]:
            # remove the grabber from the list
            self.grabbers.remove(grabber)
            # and from the figure (if it is drawn on the figure)
            try:
                self.axes.figure.patches.remove(grabber)
            except ValueError:
                pass
        self.axes.figure.canvas.draw()

    def selectArtist(self):
        if self.selected:
            return
        self.selected = True

        self.addGrabber(0, 0, self.axes, DIR_X0 | DIR_Y0, GrabberRound)
        self.addGrabber(0.5, 0, self.axes, DIR_Y0, GrabberRectangle)
        self.addGrabber(1, 1, self.axes, DIR_X1 | DIR_Y1, GrabberRound)
        self.addGrabber(1, 0.5, self.axes, DIR_X1, GrabberRectangle)
        self.addGrabber(0, 1, self.axes, DIR_X0 | DIR_Y1, GrabberRound)
        self.addGrabber(0.5, 1, self.axes, DIR_Y1, GrabberRectangle)
        self.addGrabber(1, 0, self.axes, DIR_X1 | DIR_Y0, GrabberRound)
        self.addGrabber(0, 0.5, self.axes, DIR_X0, GrabberRectangle)
        self.axes.figure.canvas.draw()

        self.snaps = []
        # self.snaps.extend(self.parent.snaps)
        self.snap_index_offset = 0  # len(self.snaps)
        self.snaps = [getSnaps(self.axes, DIR_X0, no_height=True), getSnaps(self.axes, DIR_X1, no_height=True), getSnaps(self.axes, DIR_Y0, no_height=True), getSnaps(self.axes, DIR_Y1, no_height=True)]

    def save_offset(self):
        self.selectArtist()
        # get current position of the text
        pos = self.axes.get_position()
        self.ox, self.oy = self.axes.figure.transFigure.transform((pos.x0, pos.y0))
        self.width = pos.width
        self.height = pos.height
        self.w, self.h = self.axes.figure.transFigure.transform((pos.width, pos.height))

    def update_offset(self, dx, dy):
        # get new position
        x, y = self.ox + dx, self.oy + dy

        for snap in self.snaps[0]:
            x = snap.checkSnap(x, 0)[0]
        for snap in self.snaps[1]:
            x = snap.checkSnap(x+self.w, 0)[0]-self.w
        for snap in self.snaps[2]:
            y = snap.checkSnap(0, y)[1]
        for snap in self.snaps[3]:
            y = snap.checkSnap(0, y+self.h)[1]-self.h

        for snap in self.snaps[0]:
            snap.checkSnapActive((x, 0))
        for snap in self.snaps[1]:
            snap.checkSnapActive((x+self.w, 0))
        for snap in self.snaps[2]:
            snap.checkSnapActive((0, y))
        for snap in self.snaps[3]:
            snap.checkSnapActive((0, y+self.h))

        x, y = self.axes.figure.transFigure.inverted().transform((x, y))

        pos = self.axes.get_position()

        pos.x0 = x
        pos.y0 = y
        pos.x1 = x + self.width
        pos.y1 = y + self.height

        # set the new position for the text
        self.axes.set_position(pos)

        self.updateGrabbers()

    def finalize_offset(self):
        for snaps in self.snaps:
            for snap in snaps:
                snap.hide()
        self.axes.figure.canvas.draw()

    def moveAxes(self, x, y):
        pos = self.axes.get_position()
        self.axes.set_position([pos.x0 + x, pos.y0 + y, pos.width, pos.height])
        self.updateGrabbers()
        self.axes.figure.canvas.draw()

    def keyPressEvent(self, event):
        if not self.selected:
            return
        # move last axis in z order
        if event.key == 'pagedown':
            self.axes.set_zorder(self.axes.get_zorder() - 1)
            self.axes.figure.canvas.draw()
        if event.key == 'pageup':
            self.axes.set_zorder(self.axes.get_zorder() + 1)
            self.axes.figure.canvas.draw()
        if event.key == 'left':
            self.moveAxes(-0.01, 0)
        if event.key == 'right':
            self.moveAxes(+0.01, 0)
        if event.key == 'down':
            self.moveAxes(0, -0.01)
        if event.key == 'up':
            self.moveAxes(0, +0.01)
        if event.key == "escape":
            self.deselectArtist()


class DraggableText(DraggableBase):
    def __init__(self, text, use_blit=False):
        DraggableBase.__init__(self, text, use_blit=use_blit)
        self.text = text

    def save_offset(self):
        # get current position of the text
        self.ox, self.oy = self.text.get_transform().transform(self.text.get_position())
        # add snaps
        self.snaps = []
        fig = self.text.figure
        for ax in fig.axes + [fig]:
            for txt in ax.texts:
                # for other texts
                if txt == self.text:
                    continue
                # snap to the x and the y coordinate
                x, y = txt.get_transform().transform(txt.get_position())
                self.snaps.append(Snap(x, None, (x, x), (0, 1000), transform=None))
                self.snaps.append(Snap(None, y, (0, 1000), (y, y), transform=None))

    def update_offset(self, dx, dy):
        # get new position
        x, y = self.ox + dx, self.oy + dy
        # check snaps
        for snap in self.snaps:
            x, y = snap.checkSnap(x, y)
        # display active snaps
        for snap in self.snaps:
            snap.checkSnapActive((x, y))
        # set the new position for the text
        self.text.set_position(self.text.get_transform().inverted().transform((x, y)))

    def finalize_offset(self):
        # remove all snaps when the dragger is released
        for snap in self.snaps:
            snap.remove()


def StartPylustration(xsnaps=None, ysnaps=None, unit="cm"):
    import matplotlib as mpl
    mpl.rcParams['keymap.back'].remove('left')
    mpl.rcParams['keymap.forward'].remove('right')

    # add a dragger for each figure
    for i in plt.get_fignums():
        FigureDragger(plt.figure(i), xsnaps, ysnaps, unit)
