import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
uniform_data = np.random.rand(10, 12)

import pylustrator

pylustrator.start()


test_str = "test string"
test_dict = {"key": "value"}


def make_plot(uniform_data, str_test, dict_test):
    """Contains all functions calls and imports to generate plot."""
    import seaborn as sns

    sns.set_theme()

    ax = sns.heatmap(uniform_data)


# if output file is given a name and reqd_code is not provided, the output
# to the file will only contain the change code written by pylustrator.
# This implementation also assumes that the reqd_code is provided as:
#   [function, argument_1, argument_2, etc.]
plt.figure(
    output_file="sample_pylustrator_output.py",
    reqd_code=[
        make_plot,
        uniform_data,
        test_str,
        test_dict,
    ],
)

# call to plotting function must come after call to figure
make_plot(uniform_data, test_str, test_dict)

plt.show()
