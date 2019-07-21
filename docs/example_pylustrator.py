# import matplotlib and numpy as usual
import matplotlib.pyplot as plt
import numpy as np

# now import pylustrator
import pylustrator

# activate pylustrator
pylustrator.start()

# build plots as you normally would
np.random.seed(1)
t = np.arange(0.0, 2, 0.001)
y = 2 * np.sin(np.pi * t)
a, b = np.random.normal(loc=(5., 3.), scale=(2., 4.), size=(100,2)).T
b += a

plt.figure(1)
plt.subplot(131)
plt.plot(t, y)

plt.subplot(132)
plt.plot(a, b, "o")

plt.subplot(133)
plt.bar(0, np.mean(a))
plt.bar(1, np.mean(b))

# show the plot in a pylustrator window
plt.show()

