import numpy as np
import time

from toydsl.driver.driver import computation
from toydsl.frontend.language import Horizontal, Vertical, end, start
import matplotlib.pyplot as plt
from statistics import median


@computation
def copy_stencil(out_field, in_field):
    with Vertical[start:end]:
        with Horizontal[start : end, start: end]:
            out_field[0, 0, 0] = in_field[0, 0, 0]


@computation
def vertical_blur(out_field, in_field):
    with Vertical[start+1:end-1]:
        with Horizontal[start : end, start: end]:
            out_field[0, 0, 0] = (in_field[0, 0, 1] + in_field[0, 0, 0] + in_field[0, 0, -1]) / 3


@computation
def lapoflap(out_field, in_field, tmp1_field):
    """
    out = in - 0.03 * laplace of laplace
    """
    with Vertical[start:end]:
        with Horizontal[start+1 : end-1, start+1: end-1]:
            tmp1_field[0, 0, 0] = -4.0 * in_field[0,0,0] + in_field[-1,0,0] + in_field[1,0,0] + in_field[0,-1,0] + in_field[0,1,0]
        with Horizontal[start+1 : end-1, start+1: end-1]:
            out_field[0, 0, 0] = in_field[0, 0, 0] - 0.03 * (-4.0 * tmp1_field[0,0,0] + tmp1_field[-1,0,0] + tmp1_field[1,0,0] + tmp1_field[0,-1,0] + tmp1_field[0,1,0])


def set_up_data(vert,plane):
    """
    Set up the input for the test example
    """
    i = [0, vert]
    j = [0, plane]
    k = [0, plane]
    shape = (i[-1], j[-1], k[-1])
    a = np.zeros(shape)
    a[:,j[-1]//5:4*(j[-1]//5),k[-1]//5:4*(k[-1]//5)]=1
    b = np.zeros(shape)
    c = np.zeros(shape)
    d = np.zeros(shape)
    return a, b, c, d, i, j, k


if __name__ == "__main__":
    vert = [16,32,64,128,256]
    plane = [32,64,128,256,512]

    time_sizes = []

    for index in range(len(vert)):
        nb_measurements = 100
        time_all = []
        for _ in range(nb_measurements):
            input_warm, output_warm, tmp1_warm, tmp2_warm, i_warm, j_warm, k_warm = set_up_data(vert[index],plane[index])
            input, output, tmp1, tmp2, i, j, k = set_up_data(vert[index],plane[index])

            num_runs_warm = 10
            num_runs = 512


            # plt.ioff()
            # plt.imshow(input[input.shape[0] // 2, :, :], origin="lower")
            # # plt.imshow(input[:, :, input.shape[0] // 2], origin="lower")
            # plt.colorbar()
            # plt.savefig("in_field.png")
            # plt.close()

            # Warm up
            for _ in range(num_runs_warm):
                # lapoflap(output_warm, input_warm,tmp1_warm, i_warm, j_warm, k_warm)
                copy_stencil(output_warm, input_warm,i_warm,j_warm,k_warm)
                # vertical_blur(output_warm, input_warm,i_warm,j_warm,k_warm)
                input = output

            start = time.time_ns()
            for _ in range(num_runs):
                # lapoflap(output, input,tmp1, i, j, k)
                copy_stencil(output, input,i,j,k)
                # vertical_blur(output, input,i,j,k)
                input = output
            end = time.time_ns()

            time_all.append((end-start)/(10**9))
    # Using this inupt, we expect the output of b to be
    # [[2. 2. 2. 2. 0.]
    #  [2. 2. 2. 2. 0.]
    #  [2. 2. 2. 2. 0.]
    #  [2. 2. 2. 2. 0.]
    #  [1. 1. 1. 1. 0.]]
    # print(output[:, :, 0].T)

    # plt.imshow(output[output.shape[0] // 2, :, :], origin="lower")
    # # plt.imshow(output[:, :, output.shape[0] // 2], origin="lower")
    # plt.colorbar()
    # plt.savefig("out_field.png")
    # plt.close()


    # print("Called DSL function {} times in {} seconds".format(num_runs, (end-start)/(10**9)))
        time_sizes.append(median(time_all))

    print(time_sizes)
    # with open('lapoflap.npy', 'wb') as f:
    #     np.save(f, time_sizes)

    # with open('vertical_blur.npy', 'wb') as f:
    #     np.save(f, time_sizes)

    with open('copy_stencil.npy', 'wb') as f:
        np.save(f, time_sizes)
    # with open('lapoflap.npy', 'rb') as f:
    #     test = np.load(f)
    #     print(test)
