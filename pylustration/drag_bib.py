from __future__ import division
import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np
import imageio
import traceback


def fig_text(x, y, text, unit="cm", *args, **kwargs):
    """
    add a text to the figure positioned in cm
    """
    fig = plt.gcf()
    if unit == "cm":
        x = x / 2.54 / fig.get_size_inches()[0]
        y = y / 2.54 / fig.get_size_inches()[1]
    if x < 0:
        x += 1
    if y < 0:
        y += 1
    return fig.text(x, y, text, picker=True, *args, **kwargs)


def add_axes(dim, unit="cm", *args, **kwargs):
    """
    add an axes with dimensions specified in cm
    """
    fig = plt.gcf()
    x, y, w, h = dim
    if unit == "cm":
        x = x / 2.54 / fig.get_size_inches()[0]
        y = y / 2.54 / fig.get_size_inches()[1]
        w = w / 2.54 / fig.get_size_inches()[0]
        h = h / 2.54 / fig.get_size_inches()[1]
    if x < 0:
        x += 1
    if y < 0:
        y += 1
    return plt.axes([x, y, w, h], *args, **kwargs)


def add_image(filename):
    plt.imshow(imageio.imread(filename))
    plt.xticks([])
    plt.yticks([])


def changeFigureSize(w, h, cut_from_top=False, cut_from_left=False):
    oldw, oldh = plt.gcf().get_size_inches()
    fx = oldw / w
    fy = oldh / h
    for axe in plt.gcf().axes:
        box = axe.get_position()
        if cut_from_top:
            axe.set_position([box.x0 * fx, box.y0 * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
        else:
            if cut_from_left:
                axe.set_position(
                    [1 - (1 - box.x0) * fx, 1 - (1 - box.y0) * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
            else:
                axe.set_position([box.x0 * fx, 1 - (1 - box.y0) * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
    for text in plt.gcf().texts:
        x0, y0 = text.get_position()
        if cut_from_top:
            text.set_position([x0 * fx, y0 * fy])
        else:
            if cut_from_left:
                text.set_position([1 - (1 - x0) * fx, 1 - (1 - y0) * fy])
            else:
                text.set_position([x0 * fx, 1 - (1 - y0) * fy])
    plt.gcf().set_size_inches(w, h, forward=True)


def mark_inset(parent_axes, inset_axes, loc1=1, loc2=2, **kwargs):
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxPatch, BboxConnector
    try:
        loc1a, loc1b = loc1
    except:
        loc1a = loc1
        loc1b = loc1
    try:
        loc2a, loc2b = loc2
    except:
        loc2a = loc2
        loc2b = loc2
    rect = TransformedBbox(inset_axes.viewLim, parent_axes.transData)

    pp = BboxPatch(rect, fill=False, **kwargs)
    parent_axes.add_patch(pp)
    pp.set_clip_on(False)

    p1 = BboxConnector(inset_axes.bbox, rect, loc1=loc1a, loc2=loc1b, **kwargs)
    inset_axes.add_patch(p1)
    p1.set_clip_on(False)
    p2 = BboxConnector(inset_axes.bbox, rect, loc1=loc2a, loc2=loc2b, **kwargs)
    inset_axes.add_patch(p2)
    p2.set_clip_on(False)

    return pp, p1, p2


def draw_from_point_to_bbox(parent_axes, insert_axes, point, loc=1, **kwargs):
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxConnector, Bbox
    rect = TransformedBbox(Bbox([point, point]), parent_axes.transData)
    # rect = TransformedBbox(Bbox([[1, 0], [1, 0]]), parent_axes.transData)
    p1 = BboxConnector(rect, insert_axes.bbox, loc, **kwargs)
    parent_axes.add_patch(p1)
    p1.set_clip_on(False)
    return p1


def draw_from_point_to_point(parent_axes, insert_axes, point1, point2, **kwargs):
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxConnector, Bbox
    rect = TransformedBbox(Bbox([point1, point1]), parent_axes.transData)
    rect2 = TransformedBbox(Bbox([point2, point2]), insert_axes.transData)
    # rect = TransformedBbox(Bbox([[1, 0], [1, 0]]), parent_axes.transData)
    loc = 1
    p1 = BboxConnector(rect, rect2, loc, **kwargs)
    parent_axes.add_patch(p1)
    p1.set_clip_on(False)
    return p1


def mark_inset_pos(parent_axes, inset_axes, loc1, loc2, point, **kwargs):
    kwargs["lw"] = 0.8
    ax_new = plt.axes(inset_axes.get_position())
    ax_new.set_xlim(point[0], point[0])
    ax_new.set_ylim(point[1], point[1])
    mark_inset(parent_axes, ax_new, loc1, loc2, **kwargs)
    plt.xticks([])
    plt.yticks([])
    ax_new.set_zorder(inset_axes.get_zorder() - 1)


def VoronoiPlot(points, values, vmin=None, vmax=None, cmap=None):
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    from scipy.spatial import Voronoi, voronoi_plot_2d
    from matplotlib import cm

    if cmap is None:
        cmap = cm.get_cmap('viridis')

    vor = Voronoi(points)

    # %%
    patches = []
    dist_list = []
    excluded_indices = []
    for index, p in enumerate(points):
        # print(index)
        reg = vor.regions[vor.point_region[index]]
        if -1 in reg:
            # plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)
            excluded_indices.append(index)
            continue
        distances = np.linalg.norm(np.array([vor.vertices[i] for i in reg]) - p, axis=1)
        if np.max(distances) > 2:
            # plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)
            excluded_indices.append(index)
            continue
        region = np.array([vor.vertices[i] for i in reg])
        polygon = Polygon(region, True)
        patches.append(polygon)
        dists = values[index]
        dist_list.append(dists)
        # plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)

    p = PatchCollection(patches, cmap=cmap)
    p.set_clim([vmin, vmax])
    p.set_array(np.array(dist_list))
    p.set_linewidth(10)

    plt.gca().add_collection(p)
    plt.xticks([])
    plt.yticks([])
    return p, excluded_indices


def selectRectangle(axes=None):
    if axes is None:
        axes = plt.gca()

    def onselect(eclick, erelease):
        'eclick and erelease are matplotlib events at press and release'
        print(' startposition : (%f, %f)' % (eclick.xdata, eclick.ydata))
        print(' endposition   : (%f, %f)' % (erelease.xdata, erelease.ydata))
        print(' used button   : ', eclick.button)

    from matplotlib.widgets import RectangleSelector
    rect_selector = RectangleSelector(axes, onselect)
    return rect_selector


def despine(ax=None, complete=False):
    if not ax:
        ax = plt.gca()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    if complete:
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

""" drag stuff """


class FigureDragger:
    last_picked = False
    active_object = None
    drag_object = None
    fig = None
    first_resize = True
    displaying = False

    def __init__(self, fig):
        self.fig = fig
        self.grabbers = []

        # store the position where StartPylustration was called
        self.stack_position = traceback.extract_stack()[-3]

        self.fig_inch_size = fig.get_size_inches()

        """
        additional_xsnaps = []
        if xsnaps is not None:

            for x in xsnaps:
                if unit == "cm":
                    x = x / 2.54 / fig.get_size_inches()[0]
                if x < 0:
                    print("minus", x)
                    x = 1 + x
                plt.plot([x, x], [0, 1], '-', color=[0.8, 0.8, 0.8], transform=fig.transFigure, clip_on=False, lw=1,
                         zorder=-10)
                additional_xsnaps.append(x)
                print(additional_xsnaps)

        additional_ysnaps = []
        if ysnaps is not None:
            for y in ysnaps:
                if unit == "cm":
                    y = y / 2.54 / fig.get_size_inches()[1]
                if y < 0:
                    y = 1 + y
                plt.plot([0, 1], [y, y], '-', color=[0.8, 0.8, 0.8], transform=fig.transFigure, clip_on=False, lw=1,
                         zorder=-10)
                additional_ysnaps.append(y)
        barx, = plt.plot(0, 0, 'rs--', transform=fig.transFigure, clip_on=False, lw=4, zorder=100)
        bary, = plt.plot(0, 0, 'rs--', transform=fig.transFigure, clip_on=False, lw=4, zorder=100)
        """

        # add a text showing the figure size
        self.text = plt.text(0, 0, "", transform=self.fig.transFigure, clip_on=False, zorder=100)

        # connect event callbacks
        fig.canvas.mpl_connect("pick_event", self.on_pick_event)
        fig.canvas.mpl_connect('button_press_event', self.mouse_down_event)
        fig.canvas.mpl_connect('motion_notify_event', self.mouse_move_event)
        fig.canvas.mpl_connect('button_release_event', self.mouse_up_event)
        fig.canvas.mpl_connect('key_press_event', self.key_press_event)
        fig.canvas.mpl_connect('draw_event', self.draw_event)
        fig.canvas.mpl_connect('resize_event', self.resize_event)
        fig.canvas.mpl_connect('scroll_event', self.scroll_event)

        # make all the subplots pickable
        for axes in self.fig.axes:
            axes.set_picker(True)

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

    def mouse_down_event(self, event):
        # only drag with left mouse button
        if event.button != 1:
            return
        if self.last_picked is False and self.active_object:
            self.deselectArtist()
            # draw the figure
            self.draw()
        self.last_picked = False

    def mouse_move_event(self, event):
        # if the mouse moves and no axis is dragged do nothing
        if self.displaying:
            return
        # move the dragged object
        if self.drag_object is not None:
            # callback
            self.drag_object.movedEvent(event)
            # draw the figure
            self.draw()

    def mouse_up_event(self, event):
        # only react to left mouse button
        if event.button != 1:
            return
        # release dragged object
        if self.drag_object is not None:
            # callback
            self.drag_object.releasedEvent(event)
            # set to none
            self.drag_object = None
            # draw figure
            self.draw()

    def key_press_event(self, event):
        global last_axes, nosnap
        global stack_position
        # space: print code to restore current configuration
        if event.key == ' ':
            save_text = "#% start: automatic generated code from pylustration\n"
            save_text += "plt.gcf().set_size_inches(%f/2.54, %f/2.54, forward=True)\n" % (
                (self.fig.get_size_inches()[0] - self.inch_offset[0]) * 2.54, (self.fig.get_size_inches()[1] - self.inch_offset[1]) * 2.54)
            for index, ax in enumerate(self.fig.axes):
                pos = ax.get_position()
                save_text += "plt.gcf().axes[%d].set_position([%f, %f, %f, %f])\n" % (
                    index, pos.x0, pos.y0, pos.width, pos.height)
                if ax.get_zorder() != 0:
                    save_text += "plt.gcf().axes[%d].set_zorder(%d)\n" % (index, ax.get_zorder())
                for index2, artist in enumerate(ax.get_children()):
                    if artist.pickable():
                        try:
                            pos0 = artist.original_pos
                        except:
                            continue
                        pos = artist.get_position()
                        save_text += "pylustration.moveArtist(%d, %f, %f, %f, %f)\n" % (
                            index, pos0[0], pos0[1], pos[0], pos[1])
            for index, txt in enumerate(self.fig.texts):
                if txt.pickable():
                    pos = txt.get_position()
                    save_text += "plt.gcf().texts[%d].set_position([%f, %f])\n" % (index, pos[0], pos[1])
            save_text += "#% end: automatic generated code from pylustration"
            print(save_text)
            insertTextToFile(save_text, self.stack_position)
        if event.key == 'control':
            nosnap = True
        # move last axis in z order
        if event.key == 'pagedown' and last_axes is not None:
            last_axes.set_zorder(last_axes.get_zorder() - 1)
            self.draw()
        if event.key == 'pageup' and last_axes is not None:
            last_axes.set_zorder(last_axes.get_zorder() + 1)
            self.draw()
        if event.key == 'left':
            pos = last_axes.get_position()
            last_axes.set_position([pos.x0 - 0.01, pos.y0, pos.width, pos.height])
            self.draw()
        if event.key == 'right':
            pos = last_axes.get_position()
            last_axes.set_position([pos.x0 + 0.01, pos.y0, pos.width, pos.height])
            self.draw()
        if event.key == 'down':
            pos = last_axes.get_position()
            last_axes.set_position([pos.x0, pos.y0 - 0.01, pos.width, pos.height])
            self.draw()
        if event.key == 'up':
            pos = last_axes.get_position()
            last_axes.set_position([pos.x0, pos.y0 + 0.01, pos.width, pos.height])
            self.draw()

    def addGrabber(self, x, y, artist, dir, GrabberClass):
        # add a grabber object at the given coordinates
        self.grabbers.append(GrabberClass(self, x, y, artist, dir))

    def deselectArtist(self):
        # remove all grabbers when an artist is deselected
        for grabber in self.grabbers[::-1]:
            # remove the grabber from the list
            self.grabbers.remove(grabber)
            # and from the figure (if it is drawn on the figure)
            try:
                self.fig.patches.remove(grabber)
            except ValueError:
                pass

    def selectArtist(self, artist):
        if self.active_object is not None:
            self.deselectArtist()
        self.active_object = artist

        self.fig = plt.gcf()
        self.addGrabber(0, 0, artist, DIR_X0 | DIR_Y0, GrabberRound)
        self.addGrabber(0.5, 0, artist, DIR_Y0, GrabberRectangle)
        self.addGrabber(1, 1, artist, DIR_X1 | DIR_Y1, GrabberRound)
        self.addGrabber(1, 0.5, artist, DIR_X1, GrabberRectangle)
        self.addGrabber(0, 1, artist, DIR_X0 | DIR_Y1, GrabberRound)
        self.addGrabber(0.5, 1, artist, DIR_Y1, GrabberRectangle)
        self.addGrabber(1, 0, artist, DIR_X1 | DIR_Y0, GrabberRound)
        self.addGrabber(0, 0.5, artist, DIR_X0, GrabberRectangle)
        self.addGrabber(0, 0, artist, 0, AxesGrabber)
        self.draw()

    def on_pick_event(self, event):
        " Store which text object was picked and were the pick event occurs."

        print("picker", event)

        self.last_picked = True
        artist = event.artist

        if isinstance(event.artist, Text):
            if self.active_object is not None:
                self.deselectArtist()
            self.active_object = event.artist
            self.addGrabber(0, 0, event.artist, 0, TextGrabber)
            self.drag_object = self.grabbers[-1]
            self.grabbers[-1].clickedEvent(event)
            return
        # subplot
        else:
            try:
                artist.transData
                self.selectArtist(event.artist)
                self.drag_object = self.grabbers[-1]
                self.grabbers[-1].clickedEvent(event)
            except AttributeError:
                self.drag_object = artist
                artist.clickedEvent(event)

        return True

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
            (self.fig.get_size_inches()[0] - self.inch_offset[0]) * 2.54, (self.fig.get_size_inches()[1] - self.inch_offset[1]) * 2.54))

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




from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Ellipse

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
        Line2D.__init__(self, [], [], transform=transform, clip_on=False, lw=2, zorder=100, linestyle="dashed", color="r", marker="o")
        plt.gca().add_artist(self)

    def checkSnap(self, x, y):
        if self.x is not None and abs(x-self.x) < 10:
            x = self.x
        if self.y is not None and abs(y-self.y) < 10:
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

    def remove(self):
        self.set_data((), ())
        self.axes.artists.remove(self)

class Grabber():
    fig = None
    target = None
    dir = None
    snaps = None

    def __init__(self, parent, x, y, artist, dir):
        self.parent = parent
        self.axes_pos = (x, y)
        self.fig = artist.figure
        self.target = artist
        self.dir = dir
        self.updatePos()
        pos = self.target.get_position()
        self.aspect = pos.width/pos.height
        self.height = pos.height
        self.width = pos.width
        self.fix_aspect = self.target.get_aspect() != "auto" and self.target.get_adjustable() != "datalim"

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

    def updateGrabbers(self):
        global grabbers
        for grabber in self.parent.grabbers:
            grabber.updatePos()

    def clickedEvent(self, event):
        self.snaps = []
        pos0 = self.target.get_position()
        for axes in self.parent.fig.axes:
            if axes != self.target:
                pos1 = axes.get_position()
                self.snaps.append(Snap(pos1.x0, None, (pos1.x0, pos1.x0), (0, 1)))
                self.snaps.append(Snap(pos1.x1, None, (pos1.x1, pos1.x1), (0, 1)))
                self.snaps.append(Snap(None, pos1.y0, (0, 1), (pos1.y0, pos1.y0)))
                self.snaps.append(Snap(None, pos1.y1, (0, 1), (pos1.y1, pos1.y1)))
                if self.dir & DIR_X1:
                    self.snaps.append(Snap(pos0.x0+pos1.width, None, (pos0.x0, pos0.x0+pos1.width, np.nan, pos1.x0, pos1.x1), (pos0.y0+pos0.height/2, pos0.y0+pos0.height/2, np.nan, pos1.y0+pos1.height/2, pos1.y0+pos1.height/2)))
                if self.dir & DIR_X0:
                    self.snaps.append(Snap(pos0.x1-pos1.width, None, (pos0.x1, pos0.x1-pos1.width, np.nan, pos1.x0, pos1.x1), (pos0.y0+pos0.height/2, pos0.y0+pos0.height/2, np.nan, pos1.y0+pos1.height/2, pos1.y0+pos1.height/2)))
                if self.dir & DIR_Y1:
                    self.snaps.append(Snap(None, pos0.y0+pos1.height, (pos0.x0+pos0.width/2, pos0.x0+pos0.width/2, np.nan, pos1.x0+pos1.width/2, pos1.x0+pos1.width/2), (pos0.y0, pos0.y0+pos1.height, np.nan, pos1.y0, pos1.y1)))
                if self.dir & DIR_Y0:
                    self.snaps.append(Snap(None, pos0.y1-pos1.height, (pos0.x0+pos0.width/2, pos0.x0+pos0.width/2, np.nan, pos1.x0+pos1.width/2, pos1.x0+pos1.width/2), (pos0.y1, pos0.y1-pos1.height, np.nan, pos1.y0, pos1.y1)))
                for axes2 in self.parent.fig.axes:
                    if axes2 != axes and axes2 != self.target:
                        pos2 = axes2.get_position()
                        if pos1.x1 < pos2.x0:
                            if self.dir & DIR_X0:
                                self.snaps.append(Snap(pos2.x1+(pos2.x0-pos1.x1), None, (pos2.x1, pos2.x1+(pos2.x0-pos1.x1), np.nan, pos1.x1, pos2.x0), [pos0.y0+pos0.height/2]*5))
                            if self.dir & DIR_X1:
                                self.snaps.append(Snap(pos1.x0-(pos2.x0-pos1.x1), None, (pos1.x0, pos1.x0+(pos2.x0-pos1.x1), np.nan, pos1.x1, pos2.x0), [pos0.y0+pos0.height/2]*5))

    def releasedEvent(self, event):
        for snap in self.snaps:
            snap.remove()

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
        self.updateGrabbers()

class GrabberRound(Ellipse, Grabber):
    w = 10

    def __init__(self, parent, x, y, artist, dir):
        Grabber.__init__(self, parent, x, y, artist, dir)
        Ellipse.__init__(self, (0, 0), self.w, self.w, picker=True, figure=parent.fig, edgecolor="k")
        self.fig.patches.append(self)
        self.updatePos()

class GrabberRectangle(Rectangle, Grabber):
    w = 10

    def __init__(self, parent, x, y, artist, dir):
        Rectangle.__init__(self, (0, 0), self.w, self.w, picker=True, figure=parent.fig, edgecolor="k")
        Grabber.__init__(self, parent, x, y, artist, dir)
        self.fig.patches.append(self)
        self.updatePos()

    def get_xy(self):
        xy = Rectangle.get_xy(self)
        return (xy[0] + self.w/2, xy[1] + self.w/2)

    def set_xy(self, xy):
        Rectangle.set_xy(self, (xy[0] - self.w/2, xy[1] - self.w/2))

class AxesGrabber(Grabber):

    def clickedEvent(self, event):
        Grabber.clickedEvent(self, event)
        axes = self.target
        pos = axes.get_position()
        x, y = self.fig.transFigure.transform((pos.x0, pos.y0))
        self.drag_offset = (event.mouseevent.x-x, event.mouseevent.y-y)

    def movedEvent(self, event):
        x, y = event.x-self.drag_offset[0], event.y-self.drag_offset[1]
        for snap in self.snaps:
            x, y = snap.checkSnap(x, y)
            w, h = self.fig.transFigure.transform((self.width, self.height))
            x1, y1 = snap.checkSnap(x+w, y+h)
            x, y = x1-w, y1-h
        for snap in self.snaps:
            snap.checkSnapActive((x, y), (x+w, y+h))
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

class TextGrabber():
    def __init__(self, parent, x, y, artist, dir):
        self.target = artist
        self.snaps = []

    def releasedEvent(self, event):
        for snap in self.snaps:
            snap.remove()

    def clickedEvent(self, event):
        fig = plt.gcf()
        for ax in fig.axes + [fig]:
            for txt in ax.texts:
                if txt == self:
                    continue
                x, y = txt.get_transform().transform(txt.get_position())
                self.snaps.append(Snap(x, None, (x, x), (0, 1000), transform=None))
                self.snaps.append(Snap(None, y, (0, 1000), (y, y), transform=None))
        pos = self.target.get_position()
        x, y = self.target.get_transform().transform(pos)
        self.drag_offset = (event.mouseevent.x-x, event.mouseevent.y-y)

    def movedEvent(self, event):
        x, y = event.x-self.drag_offset[0], event.y-self.drag_offset[1]
        for snap in self.snaps:
            x, y = snap.checkSnap(x, y)
        for snap in self.snaps:
            snap.checkSnapActive((x, y))
        pos = self.target.get_position()
        self.target.set_position(self.target.get_transform().inverted().transform((x, y)))


DIR_X0 = 1
DIR_Y0 = 2
DIR_X1 = 4
DIR_Y1 = 8


def StartPylustration(xsnaps=None, ysnaps=None, unit="cm"):
    global drags

    drags = []
    for i in plt.get_fignums():
        fig = plt.figure(i)
        drag = FigureDragger(fig)
        drags.append(drag)
