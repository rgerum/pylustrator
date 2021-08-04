import numpy as np; np.random.seed(0)
uniform_data = np.random.rand(10, 12)

import pylustrator

pylustrator.start()



plt.figure(
    output_file="thisisatest.py",
    placeholder=f"""
import matplotlib.pyplot as plt
import seaborn as sns; sns.set_theme()
ax = sns.heatmap({repr(uniform_data)})
    """
)

## complex imports and calls to plotting which we do not want to try and
## find from pylustrator

## this is copied into the call to figure ##
import seaborn as sns; sns.set_theme()
import matplotlib.pyplot as plt
ax = sns.heatmap(uniform_data)
##                  ###                   ##


plt.show()
