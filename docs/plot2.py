import matplotlib.pyplot as plt
import numpy as np

np.random.seed(1)
a, b = np.random.normal(loc=(5.0, 3.0), scale=(2.0, 4.0), size=(100, 2)).T
b += a

plt.figure(0, (4, 4))
plt.plot(a, b, "o")
plt.xlabel("A")
plt.ylabel("B")
plt.savefig("plot2.png")
plt.show()
