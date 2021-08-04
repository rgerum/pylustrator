
import matplotlib.pyplot as plt

import pylustrator

pylustrator.start()

a = [1,2,3]
b = [1,2,3]

plt.figure(
    output_file="thisisatest.py",
    placeholder="import matplotlib\nplt.plot({},{})".format(
        str(a).replace(" ",","),str(b).replace(" ",",")
    )
)


plt.show()
