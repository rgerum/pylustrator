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


StartPylustration(xsnaps=[1, 2, -0.5])

plt.show()