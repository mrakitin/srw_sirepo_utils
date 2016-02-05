import matplotlib as mpl
import numpy as np

mpl.use('Agg')
from matplotlib import pyplot as plt


def plot_time_interval(data, interval=15, number_of_particles=0):
    """
    The function plots graph RMSE vs. number of processors for a given interval.

    :param data: 2D NumPy array (1st column - number of processors)
    :param interval: time interval in minutes.
    :return: None.
    """

    # Convert input data to ndarray:
    data = np.array(data)

    plt.title('%i min | %i particles' % (interval, number_of_particles))
    plt.xlabel('Number of cores')
    plt.ylabel('RMSE')
    plt.xlim([-1, data[-1, 0] + 1])
    plt.grid()

    plt.scatter(data[:, 0], data[:, 1])

    # plt.show()
    plt.savefig('%imin_%i_particles.pdf' % (interval, number_of_particles))

    return
