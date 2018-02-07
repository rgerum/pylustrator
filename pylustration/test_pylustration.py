"""
Enable picking on the legend to toggle the legended line on and off
"""
import numpy as np
import matplotlib.pyplot as plt

from pylustration import StartPylustration, fig_text, add_axes, StartDragger
#plt.ion()

StartDragger()

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
add_axes([1, 1, 16, 3])
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')


ax0 = plt.subplot(233)
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')
plt.legend()

ax1 = plt.subplot(234)
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')
plt.axis("equal")
plt.legend()

ax2 = plt.subplot(235)
a = np.arange(1000).reshape(20, 50)
plt.imshow(a)

ax3 = plt.colorbar()

plt.axis()


#plt.ylim(0, 5)
fig_text(1, -1, "A", size=15)
fig_text(5, -1, "B")

plt.text(0, 0, "Heyhho", transform=ax2.transAxes, picker=True)
plt.text(10, 10, "Heyhho", transform=ax2.transData, picker=True)


#% start: automatic generated code from pylustration
fig = plt.figure(0)
fig.set_size_inches(10.160000/2.54, 7.620000/2.54, forward=True)
fig.axes[0].set_position([0.672059, 0.530000, 0.227941, 0.350000])
fig.axes[1].set_position([0.125000, 0.110000, 0.227941, 0.350000])
fig.axes[2].set_position([0.398529, 0.236373, 0.182353, 0.097255])
fig.axes[2].texts[0].set_position([0.000000, 0.000000])  # Text: "Heyhho"
fig.axes[2].texts[1].set_position([10.000000, 10.000000])  # Text: "Heyhho"
fig.axes[3].set_position([0.592279, 0.110000, 0.013125, 0.350000])
fig.texts[0].set_position([0.098425, 0.868766])  # Text: "A"
fig.texts[1].set_position([0.492126, 0.868766])  # Text: "B"
#% end: automatic generated code from pylustration
plt.show()