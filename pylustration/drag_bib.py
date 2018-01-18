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
        x = x/2.54/fig.get_size_inches()[0]
        y = y/2.54/fig.get_size_inches()[1]
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
        x = x/2.54/fig.get_size_inches()[0]
        y = y/2.54/fig.get_size_inches()[1]
        w = w/2.54/fig.get_size_inches()[0]
        h = h/2.54/fig.get_size_inches()[1]
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
                axe.set_position([1 - (1- box.x0) * fx, 1 - (1 - box.y0) * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
            else:
                axe.set_position([box.x0 * fx, 1-(1-box.y0) * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
    for text in plt.gcf().texts:
        x0, y0 = text.get_position()
        if cut_from_top:
            text.set_position([x0 * fx, y0 * fy])
        else:
            if cut_from_left:
                text.set_position([1 - (1 - x0) * fx, 1 - (1 - y0) * fy])
            else:
                text.set_position([x0 * fx, 1-(1-y0) * fy])
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
    #rect = TransformedBbox(Bbox([[1, 0], [1, 0]]), parent_axes.transData)
    p1 = BboxConnector(rect, insert_axes.bbox, loc, **kwargs)
    parent_axes.add_patch(p1)
    p1.set_clip_on(False)
    return p1

def draw_from_point_to_point(parent_axes, insert_axes, point1, point2, **kwargs):
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxConnector, Bbox
    rect = TransformedBbox(Bbox([point1, point1]), parent_axes.transData)
    rect2 = TransformedBbox(Bbox([point2, point2]), insert_axes.transData)
    #rect = TransformedBbox(Bbox([[1, 0], [1, 0]]), parent_axes.transData)
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
        #print(index)
        reg = vor.regions[vor.point_region[index]]
        if -1 in reg:
            #plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)
            excluded_indices.append(index)
            continue
        distances = np.linalg.norm(np.array([vor.vertices[i] for i in reg])-p, axis=1)
        if np.max(distances) > 2:
            #plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)
            excluded_indices.append(index)
            continue
        region = np.array([vor.vertices[i] for i in reg])
        polygon = Polygon(region, True)
        patches.append(polygon)
        dists = values[index]
        dist_list.append(dists)
        #plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)

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

def button_press_callback(event):
    global drag_axes, drag_dir, last_mouse_pos, last_axes, drag_offset, drag_text
    # only drag with left mouse button
    if event.button != 1:
        return
    # if the user doesn't have clicked on an axis do nothing
    if event.inaxes is None or drag_text:
        return
    # get the axis teh user clicked in
    ax = event.inaxes
    # transform the event coordinates to that axis
    xaxes, yaxes = ax.transAxes.inverted().transform([event.x, event.y])
    # determine which borders are dragged, dragged borders are stored as set bits in drag_dir
    drag_dir = 0
    xfigure, yfigure = fig.transFigure.inverted().transform([event.x, event.y])
    pos1 = event.inaxes.get_position()
    drag_offset = [xfigure-pos1.x0, yfigure-pos1.y0]
    # smaller then 10% in x or larger then 90% drag left or right border
    if xaxes < 0.1:
        drag_dir |= 1
    if xaxes > 0.9:
        drag_dir |= 2
        drag_offset[0] = xfigure-pos1.x0-pos1.width
    # smaller then 10% in y or larger then 90% drag bottom or top border
    if yaxes < 0.1:
        drag_dir |= 4
    if yaxes > 0.9:
        drag_dir |= 8
        drag_offset[1] = yfigure-pos1.y0-pos1.height
    # no border selected? drag the whole axis
    if drag_dir == 0:
        drag_dir = 16
    # remember the starting position and the axis
    last_mouse_pos = [event.x, event.y]
    drag_axes = event.inaxes
    last_axes = drag_axes


def motion_notify_callback(event):
    global drag_axes, drag_dir, last_mouse_pos, drag_offset, displaying, text, pick_offset
    # if the mouse moves and no axis is dragged do nothing
    if displaying:
        return
    if drag_text is not None:
        displaying = True
        x, y = event.x, event.y
        if not nosnap:
            for ax in fig.axes+[fig]:
                for txt in ax.texts:
                    if txt == drag_text:
                        continue
                    tx, ty = txt.get_transform().transform(txt.get_position())
                    if abs(x-tx) < 10:
                        x = tx
                    if abs(y-ty) < 10:
                        y = ty
        x, y = drag_text.get_transform().inverted().transform([x, y])
        #x -= pick_offset[0]
        #y -= pick_offset[1]
        drag_text.set_position((x, y))
        #drag_text.set_position([xfigure, yfigure])
        fig.canvas.flush_events()
        fig.canvas.draw()
        return
    if drag_axes is None:
        return
    displaying = True
    # transform event in figure coordinates and calculate offset from last mouse pos1ition
    xfigure, yfigure = fig.transFigure.inverted().transform([event.x, event.y])
    xfigure -= drag_offset[0]
    yfigure -= drag_offset[1]
    #xoff, yoff = fig.transFigure.inverted().transform([event.x-last_mouse_pos1[0], event.y-last_mouse_pos1[1]])
    last_mouse_pos1 = [event.x, event.y]
    # get pos1sible x and y snapping positions
    pos = drag_axes.get_position()
    snap_positions_y = additional_ysnaps+[y-pos.height for y in additional_ysnaps]
    snap_positions_y_draw = [[[0, 1], [y, y]] for y in additional_ysnaps]*2
    snap_positions_x = additional_xsnaps+[x-pos.width for x in additional_xsnaps]
    snap_positions_x_draw = [[[x, x], [0, 1]] for x in additional_xsnaps]*2
    for index, ax in enumerate(fig.axes):
        if ax != drag_axes:
            pos1 = ax.get_position()
            if drag_dir & 4:
                snap_positions_y.append(pos.y0+pos.height-pos1.height)
                snap_positions_y_draw.append([[pos1.x0/2+pos1.x1/2, pos1.x0/2+pos1.x1/2, np.nan, pos.x0/2+pos.x1/2, pos.x0/2+pos.x1/2], [pos1.y0, pos1.y1, np.nan, pos.y0, pos.y1]])
            if drag_dir & 8:
                snap_positions_y.extend([pos.y0+pos1.height])
                snap_positions_y_draw.append([[pos1.x0/2+pos1.x1/2, pos1.x0/2+pos1.x1/2, np.nan, pos.x0/2+pos.x1/2, pos.x0/2+pos.x1/2], [pos1.y0, pos1.y1, np.nan, pos.y0, pos.y1]])
            if drag_dir & 16:
                snap_positions_y.extend([pos1.y1-pos.height, pos1.y0-pos.height])
                snap_positions_y_draw.extend([[[0, 1], [pos1.y1, pos1.y1]], [[0, 1], [pos1.y0, pos1.y0]]])
            snap_positions_y.extend([pos1.y0, pos1.y1])
            snap_positions_y_draw.extend(([[0, 1], [pos1.y0, pos1.y0]], [[0, 1], [pos1.y1, pos1.y1]]))

            if drag_dir & 1:
                snap_positions_x.extend([pos.x1-pos1.width])
                snap_positions_x_draw.append([[pos1.x0, pos1.x1, np.nan, pos.x0, pos.x1], [pos1.y0/2+pos1.y1/2, pos1.y0/2+pos1.y1/2, np.nan, pos.y0/2+pos.y1/2, pos.y0/2+pos.y1/2]])
            if drag_dir & 2:
                snap_positions_x.extend([pos.x0+pos1.width])
                snap_positions_x_draw.append([[pos1.x0, pos1.x1, np.nan, pos.x0, pos.x1], [pos1.y0/2+pos1.y1/2, pos1.y0/2+pos1.y1/2, np.nan, pos.y0/2+pos.y1/2, pos.y0/2+pos.y1/2]])
            if drag_dir & 16:
                snap_positions_x.extend([pos1.x0-pos.width, pos1.x1-pos.width])
                snap_positions_x_draw.extend([[[pos1.x0, pos1.x0], [0, 1]], [[pos1.x1, pos1.x1], [0, 1]]])
            snap_positions_x.extend([pos1.x0, pos1.x1])
            snap_positions_x_draw.extend(([[pos1.x0, pos1.x0], [0, 1]], [[pos1.x1, pos1.x1], [0, 1]]))

            def add_snap():
                snap_positions_x.append(pos1.x1+diff)
                y_mean = np.mean((pos1.y0, pos1.y1))
                snap_positions_x_draw.append([[pos1.x1, pos1.x1+diff]+display[0], [y_mean, y_mean]+display[1]])

                snap_positions_x.append(pos1.x0-diff-pos.width)
                y_mean = np.mean((pos1.y0, pos1.y1))
                snap_positions_x_draw.append([[pos1.x0, pos1.x0-diff]+display[0], [y_mean, y_mean]+display[1]])

                snap_positions_y.append(pos1.y1+diff)
                x_mean = np.mean((pos1.x0, pos1.x1))
                snap_positions_y_draw.append([[x_mean, x_mean]+display[0], [pos1.y1, pos1.y1+diff]+display[1]])

                snap_positions_y.append(pos1.y0-diff-pos.height)
                x_mean = np.mean((pos1.x0, pos1.x1))
                snap_positions_y_draw.append([[x_mean, x_mean]+display[0], [pos1.y0, pos1.y0-diff]+display[1]])


            for index2, ax2 in enumerate(fig.axes):
                if ax2 != drag_axes and ax2 != ax:
                    pos2 = ax2.get_position()

                    diff = pos2.x0-pos1.x1
                    if diff > 0:
                        y_mean = np.mean((max(pos1.y0, pos2.y0), min(pos1.y1, pos2.y1)))
                        display = [[np.nan, pos1.x1, pos2.x0], [np.nan, y_mean, y_mean]]
                        add_snap()
                    diff = pos1.x0-pos2.x1
                    if diff > 0:
                        y_mean = np.mean((max(pos1.y0, pos2.y0), min(pos1.y1, pos2.y1)))
                        display = [[np.nan, pos1.x0, pos2.x1], [np.nan, y_mean, y_mean]]
                        add_snap()
                    diff = pos2.y0-pos1.y1
                    if diff > 0:
                        x_mean = np.mean((max(pos1.x0, pos2.x0), min(pos1.x1, pos2.x1)))
                        display = [[np.nan, x_mean, x_mean], [np.nan, pos1.y1, pos2.y0]]
                        add_snap()
                    diff = pos1.y0-pos2.y1
                    if diff > 0:
                        x_mean = np.mean((max(pos1.x0, pos2.x0), min(pos1.x1, pos2.x1)))
                        display = [[np.nan, x_mean, x_mean], [np.nan, pos1.y0, pos2.y1]]
                        add_snap()

            """
            for index2, ax2 in enumerate(fig.axes):
                if ax2 != drag_axes and ax2 != ax:
                    pos2 = ax2.get_position()
                    diff = pos2.x0-(pos1.x1)
                    if diff > 0:
                        snap_positions_x.extend([pos2.x1+diff, pos1.x0-diff-pos.width])
                        snap_positions_x_draw.append([[pos2.x1, pos2.x1+diff, np.nan, pos1.x1, pos1.x1+diff], [pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2, np.nan, pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2]])
                        snap_positions_x_draw.append([[pos1.x0, pos1.x0-diff, np.nan, pos1.x1, pos1.x1+diff], [pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2, np.nan, pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2]])

                        snap_positions_y.extend([pos2.y1+diff, pos1.y0-diff-pos.height])
                        snap_positions_y_draw.append([[pos2.x0/2+pos2.x1/2, pos2.x0/2+pos2.x1/2, np.nan, pos1.x1, pos1.x1+diff], [pos2.y1, pos2.y1+diff, np.nan, pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2]])
                        snap_positions_y_draw.append([[pos1.x0/2+pos1.x1/2]*5, [pos1.y0, pos1.y0-diff, np.nan, pos2.y0, pos2.y0-diff]])
                    diff = pos2.y0-(pos1.y1)
                    if diff > 0:
                        snap_positions_y.extend([pos2.y1+diff, pos1.y0-diff-pos.height])
                        snap_positions_y_draw.append([[pos2.x0/2+pos2.x1/2]*5, [pos2.y1, pos2.y1+diff, np.nan, pos1.y1, pos1.y1+diff]])
                        snap_positions_y_draw.append([[pos1.x0/2+pos1.x1/2]*5, [pos1.y0, pos1.y0-diff, np.nan, pos2.y0, pos2.y0-diff]])

                        snap_positions_x.extend([pos2.x1+diff, pos1.x0-diff-pos.width])
                        snap_positions_x_draw.append([[pos2.x1, pos2.x1+diff, np.nan, pos2.x0/2+pos2.x1/2, pos2.x0/2+pos2.x1/2], [pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2, np.nan,  pos1.y1, pos1.y1+diff]])
                        snap_positions_x_draw.append([[pos1.x0, pos1.x0-diff, np.nan, pos1.x0/2+pos1.x1/2, pos1.x0/2+pos1.x1/2], [pos2.y0/2+pos2.y1/2, pos2.y0/2+pos2.y1/2, np.nan, pos2.y0, pos2.y0-diff]])
            """
    # try to snap to these positions
    if drag_dir & 4 or drag_dir & 8 or drag_dir & 16:
        dist = 999
        bary.set_data([[0, 0], [0, 0]])
        for draw, y in zip(snap_positions_y_draw, snap_positions_y):
            new_dist = fig.transFigure.transform([0, abs(yfigure-y)])[1]
            if new_dist < 10 and new_dist < dist:
                yfigure = y
                dist = new_dist
                bary.set_data(draw)
    if drag_dir & 1 or drag_dir & 2 or drag_dir & 16:
        dist = 999
        barx.set_data([[0, 0], [0, 0]])
        for draw, x in zip(snap_positions_x_draw, snap_positions_x):
            new_dist = fig.transFigure.transform([abs(xfigure-x), 0])[0]
            if new_dist < 10 and new_dist < dist:
                xfigure = x
                dist = new_dist
                barx.set_data(draw)
    # drag x borders
    pos1 = drag_axes.get_position()
    save_aspect = drag_axes.get_adjustable() != "auto" and drag_axes.get_aspect() != "datalim"
    save_aspect = drag_axes.get_aspect() != "auto" and drag_axes.get_adjustable() != "datalim"
#        [a.get_adjustable() for a in [ax0, ax1, ax2, ax3]]
#Out[35]: [u'box', u'datalim', u'box', u'box']
#In[36]: [a.get_aspect() for a in [ax0, ax1, ax2, ax3]]
#Out[36]: [u'auto', u'equal', u'equal', 20.0]
    if drag_dir & 1:
        if save_aspect:
            new_width = max(pos1.width+(pos1.x0-xfigure), 1e-2)
            new_height = new_width/pos1.width*pos1.height
            drag_axes.set_position([xfigure, pos1.y0, new_width, new_height])
        else:
            drag_axes.set_position([xfigure, pos1.y0, max(pos1.width+(pos1.x0-xfigure), 1e-2), pos1.height])
    elif drag_dir & 2:
        if save_aspect:
            new_width = max(pos1.width-(pos1.x1-xfigure), 1e-2)
            new_height = new_width/pos1.width*pos1.height
            drag_axes.set_position([pos1.x0, pos1.y0, new_width, new_height])
        else:
            drag_axes.set_position([pos1.x0, pos1.y0, max(pos1.width-(pos1.x1-xfigure), 1e-2), pos1.height])
    # drag y borders
    pos1 = drag_axes.get_position()
    if drag_dir & 4:
        if save_aspect:
            new_height = max(pos1.height+(pos1.y0-yfigure), 1e-2)

            new_width = new_height/pos1.height*pos1.width
            drag_axes.set_position([pos1.x0, yfigure, new_width, new_height])
        else:
            drag_axes.set_position([pos1.x0, yfigure, pos1.width, max(pos1.height++(pos1.y0-yfigure), 1e-2)])
    elif drag_dir & 8:
        if save_aspect:
            new_height = max(pos1.height-(pos1.y0+pos1.height-yfigure), 1e-2)
            new_width = new_height/pos1.height*pos1.width
            drag_axes.set_position([pos1.x0, pos1.y0, new_width, new_height])
        else:
            drag_axes.set_position([pos1.x0, pos1.y0, pos1.width, max(pos1.height-(pos1.y0+pos1.height-yfigure), 1e-2)])
    # drag whole axis
    if drag_dir & 16:
        drag_axes.set_position([xfigure, yfigure, pos1.width, pos1.height])

    pos1 = drag_axes.get_position()
    offx, offy = fig.transFigure.inverted().transform([5, 5])
    text.set_position([pos1.x0+offx, pos1.y0+offy])
    text.set_text("%.2f x %.2f cm" % (pos1.width*fig.get_size_inches()[0]*2.54, pos1.height*fig.get_size_inches()[1]*2.54))
    # redraw figure
    fig.canvas.flush_events()
    fig.canvas.draw()


def draw_event(event):
    global displaying
    displaying = False


def button_release_callback(event):
    global drag_axes, last_axes, drag_text
    # only react to left mouse button
    if event.button != 1:
        return
    drag_text = None
    # button up releases the dragged figure
    bary.set_data([[0, 0], [0, 0]])
    barx.set_data([[0, 0], [0, 0]])
    drag_axes = None
    fig.canvas.draw()

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
    distance = np.linalg.norm(np.array([x1,y1])-np.array(positions), axis=1)
    print(np.min(distance), np.array([x2,y2]), np.array(positions).shape)
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
                #print(lineno, stack_pos.lineno, last_block)
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

def key_press_callback(event):
    global last_axes, nosnap
    global stack_position
    # space: print code to restore current configuration
    if event.key == ' ':
        save_text = "#% start: automatic generated code from pylustration\n"
        save_text += "plt.gcf().set_size_inches(%f/2.54, %f/2.54, forward=True)\n" % ((fig.get_size_inches()[0]-inch_offset[0])*2.54, (fig.get_size_inches()[1]-inch_offset[1])*2.54)
        for index, ax in enumerate(fig.axes):
            pos = ax.get_position()
            save_text += "plt.gcf().axes[%d].set_position([%f, %f, %f, %f])\n" % (index, pos.x0, pos.y0, pos.width, pos.height)
            if ax.get_zorder() != 0:
                save_text += "plt.gcf().axes[%d].set_zorder(%d)\n" % (index, ax.get_zorder())
            for index2, artist in enumerate(ax.get_children()):
                if artist.pickable():
                    try:
                        pos0 = artist.original_pos
                    except:
                        continue
                    pos = artist.get_position()
                    save_text += "pylustration.moveArtist(%d, %f, %f, %f, %f)\n" % (index, pos0[0], pos0[1], pos[0], pos[1])
        for index, txt in enumerate(fig.texts):
            if txt.pickable():
                pos = txt.get_position()
                save_text += "plt.gcf().texts[%d].set_position([%f, %f])\n" % (index, pos[0], pos[1])
        save_text += "#% end: automatic generated code from pylustration"
        print(save_text)
        insertTextToFile(save_text, stack_position)
    if event.key == 'control':
        nosnap = True
    # move last axis in z order
    if event.key == 'pagedown' and last_axes is not None:
        last_axes.set_zorder(last_axes.get_zorder()-1)
        fig.canvas.draw()
    if event.key == 'pageup' and last_axes is not None:
        last_axes.set_zorder(last_axes.get_zorder()+1)
        fig.canvas.draw()
    if event.key == 'left':
        pos = last_axes.get_position()
        last_axes.set_position([pos.x0-0.01, pos.y0, pos.width, pos.height])
        fig.canvas.draw()
    if event.key == 'right':
        pos = last_axes.get_position()
        last_axes.set_position([pos.x0+0.01, pos.y0, pos.width, pos.height])
        fig.canvas.draw()
    if event.key == 'down':
        pos = last_axes.get_position()
        last_axes.set_position([pos.x0, pos.y0-0.01, pos.width, pos.height])
        fig.canvas.draw()
    if event.key == 'up':
        pos = last_axes.get_position()
        last_axes.set_position([pos.x0, pos.y0+0.01, pos.width, pos.height])
        fig.canvas.draw()


def key_release_callback(event):
    global nosnap
    if event.key == 'control':
        nosnap = False


def on_pick_event(event):
    global drag_text, pick_offset, pick_pos
    " Store which text object was picked and were the pick event occurs."

    if isinstance(event.artist, Text):
        drag_text = event.artist
        try:
            print(drag_text.original_pos)
        except:
            drag_text.original_pos = drag_text.get_position()
        if event.mouseevent.xdata is not None:
            pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)
            pick_offset = (event.mouseevent.xdata-drag_text.get_position()[0], event.mouseevent.ydata-drag_text.get_position()[1])
            print("pick_offset", event.mouseevent.xdata, drag_text.get_position()[0], event.mouseevent.xdata-drag_text.get_position()[0])
    return True


def resize_event(event):
    global first_resize, fig_inch_size, inch_offset
    if first_resize:
        first_resize = False
        print("###", fig_inch_size, fig.get_size_inches())
        inch_offset = np.array(fig.get_size_inches())-np.array(fig_inch_size)
    offx, offy = fig.transFigure.inverted().transform([5, 5])
    text.set_position([offx, offy])
    text.set_text("%.2f x %.2f cm" % ( (fig.get_size_inches()[0]-inch_offset[0])*2.54, (fig.get_size_inches()[1]-inch_offset[1])*2.54))
    print("Resize", fig.get_size_inches()[0]*2.54, fig.get_size_inches()[1]*2.54)


def scroll_event(event):
    global inch_offset
    inches = np.array(fig.get_size_inches())-inch_offset
    old_dpi = fig.get_dpi()
    new_dpi = fig.get_dpi()+10*event.step
    inch_offset /= old_dpi/new_dpi
    fig.set_dpi(fig.get_dpi()+10*event.step)
    fig.canvas.draw()
    fig.set_size_inches(inches+inch_offset, forward=True)
    print(fig_inch_size, fig.get_size_inches())
    resize_event(None)
    print(fig_inch_size, fig.get_size_inches())
    print("---")
    fig.canvas.draw()
    print(fig_inch_size, fig.get_size_inches())
    resize_event(None)
    print(fig_inch_size, fig.get_size_inches())
    print("###")


def StartPylustration(xsnaps=None, ysnaps=None, unit="cm"):
    global drag_axes, drag_text, last_axes, displaying
    global barx, bary, text, fig, fig_inch_size, first_resize
    global additional_xsnaps, additional_ysnaps
    global nosnap
    global pick_offset, pick_pos
    global stack_position
    nosnap = False

    # store the position where StartPylustration was called
    stack_position = traceback.extract_stack()[-2]


    # init some variables
    drag_axes = None
    drag_text = None
    last_axes = plt.gca()
    displaying = False
    pick_offset = [0, 0]
    pick_pos = [0, 0]

    fig = plt.gcf()
    fig_inch_size = fig.get_size_inches()
    print(fig_inch_size)
    first_resize = True

    additional_xsnaps = []
    if xsnaps is not None:

        for x in xsnaps:
            if unit == "cm":
                x = x/2.54/fig.get_size_inches()[0]
            if x < 0:
                print("minus", x)
                x = 1+x
            plt.plot([x, x], [0, 1], '-', color=[0.8, 0.8, 0.8], transform=fig.transFigure, clip_on=False, lw=1, zorder=-10)
            additional_xsnaps.append(x)
            print(additional_xsnaps)

    additional_ysnaps = []
    if ysnaps is not None:
        for y in ysnaps:
            if unit == "cm":
                y = y/2.54/fig.get_size_inches()[1]
            if y < 0:
                y = 1+y
            plt.plot([0, 1], [y, y], '-', color=[0.8, 0.8, 0.8], transform=fig.transFigure, clip_on=False, lw=1, zorder=-10)
            additional_ysnaps.append(y)


    # get current figure and add callbacks
    barx, = plt.plot(0, 0, 'rs--', transform=fig.transFigure, clip_on=False, lw=4, zorder=100)
    bary, = plt.plot(0, 0, 'rs--', transform=fig.transFigure, clip_on=False, lw=4, zorder=100)
    text = plt.text(0, 0, "", transform=fig.transFigure, clip_on=False, zorder=100)
    fig.canvas.mpl_connect("pick_event", on_pick_event)
    fig.canvas.mpl_connect('button_press_event', button_press_callback)
    fig.canvas.mpl_connect('motion_notify_event', motion_notify_callback)
    fig.canvas.mpl_connect('key_press_event', key_press_callback)
    fig.canvas.mpl_connect('key_release_event', key_release_callback)
    fig.canvas.mpl_connect('button_release_event', button_release_callback)
    fig.canvas.mpl_connect('draw_event', draw_event)
    fig.canvas.mpl_connect('resize_event', resize_event)
    fig.canvas.mpl_connect('scroll_event', scroll_event)
