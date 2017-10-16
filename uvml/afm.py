"""
Mike Eller
July 2017
"""

from igor import binarywave as bw
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


class Scan(object):
    def __init__(self, filename):
        self.data = bw.load(filename)
        self.scan_size = float(self.data['wave']['note'].split('\r')[0].split(': ')[1]) * 1e6

    def height_retrace(self):
        array = np.rot90(np.array(self.data['wave']['wData'])[:, :, 0])
        plt.figure()
        plt.title('Height Retrace', fontsize=14)
        plt.imshow(array * 1e9, cmap='copper', interpolation='nearest',
                   extent=[0, self.scan_size, 0, self.scan_size])
        plt.colorbar().set_label('$nm$', fontsize=14, rotation=0, horizontalalignment='left')
        plt.xlabel('$\mu m$', fontsize=14)
        plt.ylabel('$\mu m$', fontsize=14, rotation=0, labelpad=20)
        plt.show()

    def amplitude_retrace(self):
        array = np.rot90(np.array(self.data['wave']['wData'])[:, :, 1])
        plt.figure()
        plt.title('Amplitude Retrace', fontsize=14)
        plt.imshow(array * 1e9, cmap='copper', interpolation='nearest',
                   extent=[0, self.scan_size, 0, self.scan_size])
        plt.colorbar().set_label('$nm$', fontsize=14, rotation=0, horizontalalignment='left')
        plt.xlabel('$\mu m$', fontsize=14)
        plt.ylabel('$\mu m$', fontsize=14, rotation=0, labelpad=20)
        plt.show()

    def phase_retrace(self):
        array = np.rot90(np.array(self.data['wave']['wData'])[:, :, 2])
        plt.figure()
        plt.title('Phase Retrace', fontsize=14)
        plt.imshow(array, cmap='copper', interpolation='nearest',
                   extent=[0, self.scan_size, 0, self.scan_size])
        plt.colorbar().set_label('degrees', fontsize=14, rotation=0, horizontalalignment='left')
        plt.xlabel('$\mu m$', fontsize=14)
        plt.ylabel('$\mu m$', fontsize=14, rotation=0, labelpad=20)
        plt.show()

    def zsensor_retrace(self):
        array = np.rot90(np.array(self.data['wave']['wData'])[:, :, 3])
        plt.figure()
        plt.title('Z Sensor Retrace', fontsize=14)
        plt.imshow(array * 1e9, cmap='copper', interpolation='nearest',
                   extent=[0, self.scan_size, 0, self.scan_size])
        plt.colorbar().set_label('$nm$', fontsize=14, rotation=0, horizontalalignment='left')
        plt.xlabel('$\mu m$', fontsize=14)
        plt.ylabel('$\mu m$', fontsize=14, rotation=0, labelpad=20)
        plt.show()

    def plot_3d(self, arg):
        if 0 <= arg <= 3:
            array = np.rot90(np.array(self.data['wave']['wData'])[:, :, arg])
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            xx, yy = np.meshgrid(np.linspace(0, 1, 512), np.linspace(0, 1, 512))
            ax.plot_surface(xx, yy, array)
            plt.show()
        else:
            raise ValueError("Argument must be 0 - 3.")


if __name__ == "__main__":
    pass
