import matplotlib.pyplot as plt
import numpy as np

t = np.arange(0.0, 2, 0.001)
y = 2 * np.sin(np.pi * t)

plt.figure(0, (6, 4))
plt.plot(t, y)
plt.xlabel("time")
plt.ylabel("amplitude")
plt.savefig("plot1.png")

plt.show()
