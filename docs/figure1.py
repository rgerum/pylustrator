import matplotlib.pyplot as plt

import pylustrator

pylustrator.load("plot1.py")
pylustrator.load("plot2.py", offset=[1, 0])

plt.show()
