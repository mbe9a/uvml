"""
Mike Eller
UVML
July 2017
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import csv
from statsmodels.nonparametric.smoothers_lowess import lowess
from shutil import copyfile

plt.style.use('bmh')


# helper function to print polynomial fit
def print_polynomial(p):
    s = '$'
    for coef in range(0, len(p)):
        s += str(p[coef]) + '*x^' + str(len(p) - 1 - coef)
        if coef < len(p) - 1:
            s += '+'
    return s + '$'


# helper function to convert values in file name format into float values
# i.e. convert 'p' to '.' and cast to float
def convert_to_float(num):
    s = ""
    for x in range(0, len(num)):
        if num[x] == 'p':
            s += '.'
        else:
            s += num[x]
    return float(s)


# used to set the directory structure
# WILL UPDATE to sort any directory with any given amounts of files with varying independent variables
def sort_directory(path, power=True):
    files = os.listdir(path)
    if power:
        powers = []
        for f in files:
            if f.endswith(".txt"):
                sdf = SpectrumDataFile(path + "/" + f)
                if str(sdf.power) not in powers:
                    powers.append(str(sdf.power))
            else:
                files.remove(f)
        for p in powers:
            os.mkdir(path + "/" + p)
            for f in files:
                sdf = SpectrumDataFile(path + "/" + f)
                if str(sdf.power) == p:
                    copyfile(path + "/" + f, path + "/" + p + "/" + f)
                    os.remove(path + "/" + f)


# struct to handle units
# parameters for data files are stored with value and unit
class SpectrumDataParameter(object):

    def __init__(self, value, units):
        self.value = value
        self.units = units

    def __str__(self):
        return str(self.value) + " " + self.units


"""
    This class is a representation of one data file. You must pass the path to the data file on creation.
    Object automatically calculates dissociation using the trapezoid integral method (trapz) from numpy.
    You can plot the spectrum and save it to a .png file.
    
    Params:
        spacing - width of integration peaks
        data_range - range of data to plot
        peaks - where to start integration
        current - SpectrumDataParameter
        power - SpectrumDataParameter
        pressure - SpectrumDataParameter
        dissociation - float
        filepath - used to generate filename
        filename - just the base file name
        dataname - formatted name of data
        data_points - all the data parsed from the file (a list of tuples)
        
    Methods:
        parse_spectral_data
        plot_spectrum
        save_spectrum_plot
        get_range
        calculate_dissociation
"""


class SpectrumDataFile(object):

    def __init__(self, filepath, data_range=(740, 765), peaks=(740.5, 752.5), spacing=6.5):
        if filepath[-4:] != ".txt":
            raise ValueError("Invalid File Extension")
        elif not os.path.isfile(filepath):
            raise IOError("Invalid Path")

        self._spacing = spacing
        self._data_range = data_range
        self._peaks = peaks
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

        self.power = SpectrumDataParameter(convert_to_float(self.filename.split("_")[0].split("W")[0]), "W")
        self.pressure = SpectrumDataParameter(convert_to_float(self.filename.split("_")[1].split("m")[0]), "mTorr")
        self.current = SpectrumDataParameter(convert_to_float(self.filename.split("_")[2].split("A")[0]), "A")
        if len(self.filename.split("_")) > 3:
        	self.time = SpectrumDataParameter(int(self.filename.split("_")[3][:-7]), "min")
        else:
        	self.time = SpectrumDataParameter('N/A', 'min')

        self.dataname = str(self.power) + ", " + str(self.pressure) + ", " + str(self.current) + ", " + str(self.time)

        self.data_points = self.parse_spectral_data()
        self.dissociation = self.calculate_dissociation()

    # for readability
    def __str__(self):
        return self.dataname

    def __repr__(self):
        return self.__str__()

    # I chose to use properties so that I can recalculate dissociation
    # when any of these properties are changed
    @property
    def data_range(self):
        return self._data_range

    @data_range.setter
    def data_range(self, new_range):
        self._data_range = new_range
        self.data_points = self.parse_spectral_data()
        self.dissociation = self.calculate_dissociation()

    @property
    def peaks(self):
        return self._peaks

    @peaks.setter
    def peaks(self, new_peaks):
        self._peaks = new_peaks
        self.dissociation = self.calculate_dissociation()

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, val):
        self._spacing = val
        self.dissociation = self.calculate_dissociation()

    # this function reads the file and creates a list of points in the format (wavelength, intensity)
    # list is stored in the 'data_points' parameter
    # data_range corresponds to the desired wavelengths in the plot
    def parse_spectral_data(self):
        data_points = []
        with open(self.filepath, 'r') as datafile:
            # burn the header lines
            for x in range(0, 17):
                line = datafile.readline()

            line = datafile.readline()

            # for data files with thickness added as the top line
            if line[0] == ">":
                line = datafile.readline()

            if hex(ord(line[0])) == '0xd' and hex(ord(line[1])) == '0xa':
                return

            while line:
                # split the line on tabs and convert to float
                # adds a tuple (wavelength, intensity) to data_points
                data_point = (float(line.split("\t")[0]), float(line.split("\t")[1].split("\r")[0]))
                if self.data_range[0] <= data_point[0] <= self.data_range[1]:
                    data_points.append(data_point)
                line = datafile.readline()

                # must break because last line isn't actually data (will throw errors in loop above)
                if line[0] == ">":
                    break
        max = np.max([x[1] for x in data_points])
        return [(x, y/max) for (x, y) in data_points]

    """
        Plots the data in memory using pyplot
        
        Params:
            ax - axes object you can optionally plot to
            save - if true the plot will be saved to the current working directory with its dataname
            filtered - you can optionally plot a filtered version of the data
            frac - filter parameter
            fill - if true, the integral regions will be filled in with color
    """
    def plot_spectrum(self, ax=None, save=False, filtered=False, frac=0.025, fill=True):
        # the axes (ax) param is so that this function can be used within another function
        # i.e. this can be used to plot to an external figure -- just pass that fig's axes object as ax
        # when you call this function
        if ax is None:
            plt.figure()
            ax = plt.gca()
        ax.set_title("Spectrum")
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Normalized Intensity (AU)")
        xs = [x[0] for x in self.data_points]
        ys = [x[1] for x in self.data_points]
        if not filtered:
            ax.plot(xs, ys, 'b--', label=self.dataname)

        # filtered plot could be usefull when plotting the whole spectrum -- pretty noisy
        else:
            filtered = lowess(ys, xs, is_sorted=True, frac=frac, it=0)
            ax.plot(filtered[:, 0], filtered[:, 1], label='filtered data')

        # fill in the integral regions defined by peaks and spacing
        if fill:
            fill_point_1 = self.get_range(self.peaks[0], self.peaks[0] + self.spacing)
            fill_point_2 = self.get_range(self.peaks[1], self.peaks[1] + self.spacing)
            fill_xs_1 = [x[0] for x in fill_point_1]
            fill_ys_1 = [x[1] for x in fill_point_1]
            fill_xs_2 = [x[0] for x in fill_point_2]
            fill_ys_2 = [x[1] for x in fill_point_2]
            ax.fill_between(fill_xs_1, fill_ys_1, color='lightblue', label='Region I')
            ax.fill_between(fill_xs_2, fill_ys_2, color='orange', label='Region II')
        ax.set_ylim(ymin=0)
        ax.margins(0.05)
        ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        if save:
            ax.savefig(self.filename[:-4])

    # ax is used in the same way as in 'plot_spectrum'
    def plot_difference(self, ax=None):
        if ax is None:
            plt.figure()
            ax = plt.gca()
        ax.set_title("Spectrum Shadow")
        ax.set_xlabel("Wavelength")
        ax.set_ylabel("Normalized Intensity (AU)")

        # points_1 contains all the points for the first region
        points_1 = self.get_range(self.peaks[0], self.peaks[0] + self.spacing)
        # points_2 -> region 2
        points_2 = self.get_range(self.peaks[1], self.peaks[1] + self.spacing)

        # get the y values from the points
        ys_1 = [x[1] for x in points_1]
        ys_2 = [x[1] for x in points_2]

        # check and make sure the lists have the same length
        # if they don't, just truncate the end of the longer one
        diff = np.abs(len(ys_1) - len(ys_2))
        if diff < 0:
            ys_1 = ys_1[:-diff]
        elif diff > 0:
            ys_2 = ys_2[:-diff]

        # build the y values for the difference between the two
        ys_3 = []
        for x in range(0, len(ys_2)):
            if ys_1[x] - ys_2[x] > 0:
                ys_3.append(ys_1[x] - ys_2[x])
            else:
                ys_3.append(0)

        # make a generic x's list
        xs = np.linspace(0, 1, num=len(ys_1))
        ax.plot(xs, ys_1, 'b', label='Region I (' + str(self.peaks[0]) + ' nm - ' +
                                        str(self.peaks[0] + self.spacing) + ' nm)')
        ax.plot(xs, ys_2, 'r', label='Region II (' + str(self.peaks[1]) + ' nm - ' +
                                        str(self.peaks[1] + self.spacing) + ' nm)')
        ax.plot(xs, ys_3, 'm--', label='Difference (No Negatives)')
        ax.set_ylim(ymin=0)
        labels = [item.get_text() for item in ax.get_xticklabels()]
        empty_string_labels = [''] * len(labels)
        ax.set_xticklabels(empty_string_labels)
        ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        return plt.gca()

    # this is a method just to save the figure (will also plot to memory)
    # can give a custom name for the image
    # a little redundant but oh well
    def save_spectrum_plot(self, name=False):
        plt.figure()
        plt.title("Spectrum - " + self.dataname)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Intensity")
        plt.plot([x[0] for x in self.data_points], [x[1] for x in self.data_points])
        if name:
            plt.savefig(name)
        else:
            plt.savefig(self.filename[:-4])

    # this is a helper function to get the points within the range given by lower and upper
    def get_range(self, lower, upper):
        subset = []
        for x in range(0, len(self.data_points)):
            if lower <= self.data_points[x][0] <= upper:
                subset.append(self.data_points[x])
        return subset

    # calculates the two integrals of the major peaks, takes the difference, and computes the ratio
    def calculate_dissociation(self, scaling=0.91, *args, **kwargs):
        if self.data_points is None:
            return
        integral1 = np.trapz([x[1] for x in self.get_range(self.peaks[0],
                                                       self.peaks[0] + self.spacing)], *args, **kwargs)
        integral2 = np.trapz([x[1] for x in self.get_range(self.peaks[1],
                                                       self.peaks[1] + self.spacing)], *args, **kwargs) * scaling
        return np.abs(integral1 - integral2) / integral2


"""
    This class is basically a container for multiple SpectrumDataFile objects. 
    It is an extension of the python built-in dictionary - {SpectrumDataFile object: all data points}
    Automatically reads a directory given by path on creation and creates a SpectrumDataFile object for each file.
    A plot can then be generated for dissociation vs. current. Files in a single directory should have the same power and pressure.
    
    Params:
        path - directory of .txt spectrum files
        
    Methods:
        compile_dataset
        plot_dissociation
        save_dissociation_plot
"""


class SpectrumDataSet(dict):

    def __init__(self, pathname, *args, **kw):
        super(SpectrumDataSet, self).__init__(*args, **kw)
        self.path = pathname

    # this function reads a directory of spectrum data text files, populates the dict of this class
    # and writes a csv file
    def compile_dataset(self, save=True, fname=None):
        self.clear()
        if not os.path.exists(self.path):
            raise ValueError("Path does not exist.")
        else:
            files = os.listdir(self.path)
            try:
                os.remove('output.csv')
            except OSError:
                pass
            if not fname:
                n = 'output.csv'
            else:
                n = fname
            if save:
                with open(n, "w") as output:
                    # I thought csv's would be better than a text file, but I can change it to whatever
                    # reading and writing csv's is also much nicer
                    writer = csv.DictWriter(output, fieldnames=["Time (min)", "Pressure (mTorr)", "Power (W)", "Current (A)", "Ratio"])
                    writer.writeheader()
                    for f in files:
                        if f.endswith(".txt"):
                            # create a SpectrumDataFile object with each file
                            sdf = SpectrumDataFile(self.path + "/" + f)
                            # write all the values to the csv file
                            writer.writerow({"Time (min)": sdf.time.value, "Pressure (mTorr)": sdf.pressure.value, "Power (W)": sdf.power.value,
                                             "Current (A)": sdf.current.value, "Ratio": sdf.dissociation})
                            # add the dict entry to the object
                            sdf.data_points = sdf.parse_spectral_data()
                            self[sdf] = sdf.data_points
            else:
                for f in files:
                    if f.endswith(".txt"):
                        # create a SpectrumDataFile object with each file
                        sdf = SpectrumDataFile(self.path + "/" + f)
                        # add the dict entry to the object
                        sdf.data_points = sdf.parse_spectral_data()
                        self[sdf] = sdf.data_points

    """
        This function is most useful when used in iPython notebook with sliders.
        function auto sorts files in dict object based on power - 
                            will update eventually to sort by independent variable
    
        Params:
            save - can save plot in current directory
            ind_var - 'power' | 'current' | 'pressure'
            spectrum - you can plot the spectrum for a file in the SpectrumDataSet
            file - index of SpectrumDataSet to plot spectrum
            shadow - you can plot the shadow of the current file
            region1 - start of integral 1, if changed it adjusts all files in the data set - 
                                                                and therefore all dissociations
            region2 - integral 2
            spacing - width of integral regions, if changed: changes all files in data set
            
            fit - can plot just points and a poly fit
            degree - the degree of fitting polynomial   
    """
    def plot_dissociation(self, ax=None, ind_var='current', spectrum=False, shadow=False, 
        f=-1, region1=740.5, region2=752.5, spacing=6.5, fit=False, degree=5, labeloverride=None, 
        xlim=None, ylim=None, pattern='.-', **kwargs):
        # get selected spectrum data file
        sdf = sorted(self.keys(), key=lambda spec: spec.power.value)[f]

        # change all the files to the specified param values
        for spec in self.keys():
            spec.peaks = (region1, region2)
            spec.spacing = spacing
        if ax is None:
            plt.figure(figsize=(6, 10))
            ax3 = plt.subplot(312)
            if spectrum:
                ax1 = plt.subplot(311)
                sdf.plot_spectrum(ax1)
            if shadow:
                ax2 = plt.subplot(313)
                sdf.plot_difference(ax2)
        else:
            ax3 = ax

        ax3.set_title("Relative Dissociation vs " + ind_var.title())
        ax3.set_ylabel("Relative Dissociation")
        
        if xlim:
        	ax3.set_xlim(xlim)
        if ylim:
        	ax3.set_ylim(ylim)
        if ind_var == 'current':
            ax3.set_xlabel("Current (A)")
            points = sorted([(x.current.value, x.dissociation) for x in self.keys()])
            label = str(self.keys()[0].power) + " " + str(self.keys()[0].pressure)
        elif ind_var == 'power':
            ax3.set_xlabel("Power (W)")
            points = sorted([(x.power.value, x.dissociation) for x in self.keys()])
            label = str(self.keys()[0].current) + " " + str(self.keys()[0].pressure)
        elif ind_var == 'pressure':
            ax3.set_xlabel("Pressure (mTorr)")
            points = sorted([(x.pressure.value, x.dissociation) for x in self.keys()])
            label = str(self.keys()[0].power) + " " + str(self.keys()[0].current)
        elif ind_var == 'time':
        	ax3.set_xlabel("Time (min)")
        	points = sorted([(x.time.value, x.dissociation) for x in self.keys()])
        	label = str(self.keys()[0].power) + " " + str(self.keys()[0].current)
        else:
            raise ValueError("Incorrect independent variable name.")
        
        xs = [x[0] for x in points]
        ys = [x[1] for x in points]
        if labeloverride is not None:
            label = labeloverride
        if not fit:
                ax3.plot(xs, ys, pattern, label=label, **kwargs)
        else:
            c = ax3.plot(xs, ys, pattern, label=label, **kwargs)
            xp = np.linspace(np.min(xs), np.max(xs), 100)
            p = np.poly1d(np.polyfit(xs, ys, degree))
            ax3.plot(xp, p(xp), '-', label='Poly Fit: ' + label, color=c[0].get_color())
        ax3.margins(0.05)
        ax3.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        plt.tight_layout()


def errorbar(datasets, ax=None, ind_var='current', region1=740.5, region2=752.5, spacing=6.5,
             labeloverride=None, xlim=None, ylim=None, capthick=0, capcolor='black', **kwargs):

    # change all the files to the specified param values
    for dataset in datasets:
        for spec in dataset.keys():
            spec.peaks = (region1, region2)
            spec.spacing = spacing

    for x in range(1, len(datasets)):
        if len(datasets[0].keys()) == len(datasets[x].keys()):
            continue
        else:
            raise ValueError("Spectrum Data Set Objects are not the same length.")

    D = {}
    for x in range(0, len(datasets)):
        for y in range(0, len(datasets[x].keys())):
            if ind_var == 'time':
                key = datasets[x].keys()[y].time.value
            elif ind_var == 'current':
                key = datasets[x].keys()[y].current.value
            elif ind_var == 'power':
                key = datasets[x].keys()[y].power.value
            elif ind_var == 'pressure':
                key = datasets[x].keys()[y].pressure.value
            if key not in D.keys():
                D[key] = []
            D[key].append(datasets[x].keys()[y].dissociation)
    
    Davg = D.copy()
    Dmax = D.copy()
    Dmin = D.copy()
    for key in D.keys():
        Davg[key] = 0
        for x in range(0, len(datasets)):
            Davg[key] += D[key][x]
        Davg[key] /= len(datasets)
        Dmin[key] = min(D[key])
        Dmax[key] = max(D[key])

    if ax is None:
        plt.figure(figsize=(10, 6))
        ax3 = plt.gca()
    else:
        ax3 = ax

    ax3.set_title("Relative Dissociation vs " + ind_var.title())
    ax3.set_ylabel("Relative Dissociation")
    
    if xlim:
        ax3.set_xlim(xlim)
    if ylim:
        ax3.set_ylim(ylim)
    if ind_var == 'current':
        ax3.set_xlabel("Current (A)")
        label = str(datasets[0].keys()[0].power) + " " + str(datasets[0].keys()[0].pressure)
    elif ind_var == 'power':
        ax3.set_xlabel("Power (W)")
        label = str(datasets[0].keys()[0].current) + " " + str(datasets[0].keys()[0].pressure)
    elif ind_var == 'pressure':
        ax3.set_xlabel("Pressure (mTorr)")
        label = str(datasets[0].keys()[0].power) + " " + str(datasets[0].keys()[0].current)
    elif ind_var == 'time':
        ax3.set_xlabel("Time (min)")
        label = str(datasets[0].keys()[0].power) + " " + str(datasets[0].keys()[0].current)
    else:
        raise ValueError("Incorrect independent variable name.")
    
    if labeloverride is not None:
        label = labeloverride

    x = []
    y = []
    yerr_min = []
    yerr_max = []

    for i in range(0, len(D.keys())):
        x.append(D.keys()[i])
        y.append(Davg[D.keys()[i]])
        yerr_min.append(np.abs(Dmin[D.keys()[i]] - Davg[D.keys()[i]]))
        yerr_max.append(Dmax[D.keys()[i]] - Davg[D.keys()[i]])

    (_, caps, _) = ax3.errorbar(x, y, yerr=[yerr_min, yerr_max], label=label, **kwargs)

    for cap in caps:
        cap.set_color(capcolor)
        cap.set_markeredgewidth(capthick)

    ax3.margins(0.05)
    ax3.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

    plt.tight_layout()

    return D
