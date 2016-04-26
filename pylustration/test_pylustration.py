"""
Enable picking on the legend to toggle the legended line on and off
"""
import numpy as np
import matplotlib.pyplot as plt

from drag_bib import StartPylustration, fig_text, add_axes
#plt.ion()

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

ax1 = plt.subplot(234)
line1, = plt.plot(t, y1, lw=2, color='red', label='1 HZ')
line2, = plt.plot(t, y2, lw=2, color='blue', label='2 HZ')
plt.axis("equal")

ax2 = plt.subplot(235)
a = np.arange(1000).reshape(20, 50)
plt.imshow(a)

ax3 = plt.colorbar()

plt.axis()


#plt.ylim(0, 5)
fig_text(1, -1, "A", size=15)
fig_text(5, -1, "B")

plt.gcf().set_size_inches(18.000000/2.54, 15.000000/2.54, forward=True)
plt.gcf().axes[0].set_position([0.055556, 0.604545, 0.132102, 0.210744])
plt.gcf().axes[1].set_position([0.509083, 0.546780, 0.142409, 0.227187])
plt.gcf().axes[2].set_position([0.055556, 0.339549, 0.261938, 0.130337])
plt.gcf().axes[3].set_position([0.592279, 0.100000, 0.015225, 0.363636])
plt.gcf().texts[0].set_position([0.064206, 0.933333])
plt.gcf().texts[1].set_position([0.273356, 0.933333])

StartPylustration(xsnaps=[1, 2, -0.5])

plt.show()