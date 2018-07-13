"""
Enable picking on the legend to toggle the legended line on and off
"""
import numpy as np
import matplotlib.pyplot as plt

#from pylustration import StartPylustration, fig_text, add_axes, StartDragger
import pylustrator
#plt.ion()

#StartDragger()
pylustrator.start()

t = np.arange(0.0, 0.2, 0.1)
y1 = 2*np.sin(2*np.pi*t)
y2 = 4*np.sin(2*np.pi*2*t)
fig = plt.figure(0, (18/2.54, 15/2.54))
"""
#fig, ax = plt.subplots()
plt.subplot(231)
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')

line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')
#leg = ax.legend(loc='upper left', fancybox=True, shadow=True)
#leg.get_frame().set_alpha(0.4)
"""
ax0 = plt.subplot(231, label="a")
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')


ax0 = plt.subplot(233, label="b")
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')
plt.xlim(-10, 10)
plt.ylim(-10, 10)
plt.legend()

ax2 = plt.subplot(235, label="c")
a = np.arange(1000).reshape(20, 50)
plt.imshow(a)

ax1 = plt.axes([0.2, 0.2, 0.2, 0.2])#subplot(234)
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')
plt.axis("equal")
plt.legend()


from mpl_toolkits.axes_grid1.inset_locator import mark_inset
mark_inset(ax0, ax1, loc1=2, loc2=4, fc="none", lw=2, ec='r')

ax3 = plt.colorbar()

plt.axis()


#plt.ylim(0, 5)
#fig_text(1, -1, "A", size=15)
#fig_text(5, -1, "B")

plt.text(0, 0, "Heyhho", transform=ax2.transAxes, picker=True)
plt.text(10, 10, "Heyhho", transform=ax2.transData, picker=True)

#plt.axes([0, 0, 1, 1], zorder=-1)
#from pylustration import loadFigureFromFile
#loadFigureFromFile("test_pylustration2")

#% start: automatic generated code from pylustration
fig = plt.figure(0)
fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}
fig.ax_dict["c"].set_position([0.606157, 0.318644, 0.227941, 0.109412])
fig.ax_dict["c"].annotate('New Annotation', (-0.5, 19.5), (24.5, 9.5), arrowprops=dict(arrowstyle='->'))  # id=fig.ax_dict["c"].texts[1].new
fig.ax_dict["c"].texts[0].set_text("zZz")
fig.ax_dict["c"].texts[0].set_position([14.895480, 10.000000])  # Text: "zZz"
fig.ax_dict["c"].text(0.5, 0.5, 'New Text', transform=fig.ax_dict["c"].transAxes)  # id=fig.ax_dict["c"].texts[2].new
fig.ax_dict["c"].texts[1].set_text("bla")
fig.ax_dict["c"].texts[1].set_position([0.772644, 1.181611])  # Text: "bla"
fig.axes[3].texts[0].set_visible(False)
fig.axes[3].texts[1].set_visible(False)
fig.axes[4].set_position([0.419435, 0.272881, 0.008333, 0.200000])
#% end: automatic generated code from pylustration
plt.show()