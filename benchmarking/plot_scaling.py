import os

import matplotlib as mpl
import numpy as np

mpl.use('Agg')
from matplotlib import pyplot as plt


def plot_data(data, nparticles):
    data = np.array(data)
    plt.title('Number of particles: %i' % nparticles)
    plt.xlabel('Number of cores')
    plt.ylabel('Duration, seconds')
    plt.xlim([data[0, 0] - 1, data[-1, 0] + 1])
    plt.grid()

    plt.scatter(data[:, 0], data[:, 1])

    # plt.show()
    fname = '%03i_particles.pdf' % nparticles
    try:
        os.remove(fname)
    except:
        pass

    plt.savefig(fname)
    plt.clf()


if __name__ == '__main__':
    nparticles_list = [100, 180, 720, ]

    # Columns: number of processors, duration (seconds)
    data_list = [
        [
            [3, 556.107],
            [5, 298.233],
            [9, 138.462],
            [13, 81.393],
            [16, 83.939],
        ],
        [
            [13, 204.224],
            [16, 146.239],

        ],
        [
            [5, 2046.493],
            [9, 1103.129],
            [13, 751.322],
            [16, 572.369],
        ],
    ]

    for i in range(len(nparticles_list)):
        plot_data(data_list[i], nparticles_list[i])
