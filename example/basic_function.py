import numpy as np

from toydsl.driver.driver import computation
from toydsl.frontend.language import Horizontal, Vertical, end, start


@computation
def otherfunc(out_field, in_field):
    """
    A basic test of a funcction exercising the patterns of the toyDSL language.
    """
    with Vertical[start:end]:
        with Horizontal[start : end - 1, start : end - 1]:
            in_field[1, 0, 0] = 2
        with Horizontal[start : end - 1, start:end]:
            out_field = in_field[1, 0, 0] + 4*in_field[0,1,0]


def set_up_data():
    """
    Set up the input for the test example
    """
    i = [0, 5]
    j = [0, 5]
    k = [0, 5]
    shape = (i[-1], j[-1], k[-1])
    a = np.ones(shape)
    b = np.zeros(shape)
    return a, b, i, j, k


if __name__ == "__main__":
    input, output, i, j, k = set_up_data()
    otherfunc(output, input, i, j, k)
    # Using this inupt, we expect the output of b to be
    # [[2. 2. 2. 2. 0.]
    #  [2. 2. 2. 2. 0.]
    #  [2. 2. 2. 2. 0.]
    #  [2. 2. 2. 2. 0.]
    #  [1. 1. 1. 1. 0.]]
    print(output[:, :, 0].T)
