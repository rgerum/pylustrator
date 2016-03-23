from __future__ import division
import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np


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
    global drag_axes, drag_dir, last_mouse_pos, drag_offset, displaying, text
    # if the mouse moves and no axis is dragged do nothing
    if displaying:
        return
    if drag_text is not None:
        displaying = True
        x, y = event.x, event.y
        for ax in fig.axes+[fig]:
            for txt in ax.texts:
                if txt == drag_text:
                    continue
                tx, ty = txt.get_transform().transform(txt.get_position())
                if abs(x-tx) < 10:
                    x = tx
                if abs(y-ty) < 10:
                    y = ty
        drag_text.set_position(drag_text.get_transform().inverted().transform([x, y]))
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


def key_press_callback(event):
    global last_axes
    # space: print code to restore current configuration
    if event.key == ' ':
        print("plt.gcf().set_size_inches(%f/2.54, %f/2.54, forward=True)" % ((fig.get_size_inches()[0]-inch_offset[0])*2.54, (fig.get_size_inches()[1]-inch_offset[1])*2.54))
        for index, ax in enumerate(fig.axes):
            pos = ax.get_position()
            print("plt.gcf().axes[%d].set_position([%f, %f, %f, %f])" % (index, pos.x0, pos.y0, pos.width, pos.height))
            if ax.get_zorder() != 0:
                print("plt.gcf().axes[%d].set_zorder(%d)" % (index, ax.get_zorder()))
        for index, txt in enumerate(fig.texts):
            if txt.pickable():
                pos = txt.get_position()
                print("plt.gcf().texts[%d].set_position([%f, %f])" % (index, pos[0], pos[1]))

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


def on_pick_event(event):
    global drag_text
    " Store which text object was picked and were the pick event occurs."

    if isinstance(event.artist, Text):
        drag_text = event.artist
        pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)
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

    # init some variables
    drag_axes = None
    drag_text = None
    last_axes = plt.gca()
    displaying = False

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
    text = plt.text(0, 0, "test", transform=fig.transFigure, clip_on=False, zorder=100)
    fig.canvas.mpl_connect("pick_event", on_pick_event)
    fig.canvas.mpl_connect('button_press_event', button_press_callback)
    fig.canvas.mpl_connect('motion_notify_event', motion_notify_callback)
    fig.canvas.mpl_connect('key_press_event', key_press_callback)
    fig.canvas.mpl_connect('button_release_event', button_release_callback)
    fig.canvas.mpl_connect('draw_event', draw_event)
    fig.canvas.mpl_connect('resize_event', resize_event)
    fig.canvas.mpl_connect('scroll_event', scroll_event)
