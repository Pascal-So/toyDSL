import numpy as np

from toydsl.driver.driver import computation
from toydsl.frontend.language import Horizontal, Vertical, end, start


@computation
def otherfunc(out_field, in_field):
    with Vertical[start:end]:
        with Horizontal[start : end - 1, start : end - 1]:
            in_field[1, 0, 0] = 2
        with Horizontal[start : end - 1, start:end]:
            out_field = in_field[1, 0, 0]


if __name__ == "__main__":
    i = [0, 5]
    j = [0, 5]
    k = [0, 5]
    shape = (i[-1], j[-1], k[-1])
    a = np.ones(shape)
    b = np.zeros(shape)
    otherfunc(b, a, i, j, k)
    print(b[:, :, 0].T)
