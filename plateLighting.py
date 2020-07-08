#!/usr/bin/env python3

# Joana Cabrera
# 3/15/2020
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import matplotlib as mpl

# !/usr/bin/env python3

# Joana Cabrera
# 3/15/2020
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import matplotlib as mpl

from enum import Enum


class WStatus(Enum):
	empty = 1
	target = 2
	filled = 3

	def color(self):
		return {'empty': 'gray', 'target': 'red', 'filled': 'blue'}[self.name]


class Well:
	""" A class for individual wells in the matplotlib plot
    """
	def __init__(self, center, shape, size_param, status=WStatus.empty):
		self.center = center
		self.shape = shape
		self.size_param = size_param
		self.status = status
		if shape == 'circle':
			self.marker = Circle(self.center, radius=size_param, color=self.status.color(), zorder=0)
		elif shape == 'square':
			self.marker = Rectangle(self.center, width=size_param, height=size_param, color=self.status.color(),
									zorder=0)

	def markEmpty(self):
		self.status = WStatus.empty
		self.marker.set_color(self.status.color())
		self.marker.zorder = 0

	def markFilled(self):
		self.status = WStatus.filled
		self.marker.set_color(self.status.color())
		self.marker.zorder = 1

	def markTarget(self):
		self.status = WStatus.target
		self.marker.set_color(self.status.color())
		self.marker.zorder = 2

	def setMarker(self, shape):
		if shape == 'circle':
			self.marker = Circle(self.center, radius=self.size_param, color=self.status.color(), zorder=0)
		elif shape == 'square':
			self.marker = Rectangle(self.center, width=self.size_param, height=self.size_param,
									color=self.status.color(), zorder=0)


class PlateLighting:
	""" A class for lighting up the corresponding well using matplotlib
    """

	def __init__(self, a1_x, a1_y, shape, size_dict, well_spacing):

		# set up plot
		mpl.rcParams['toolbar'] = 'None'
		plt.style.use('dark_background')
		self.fig, self.ax = plt.subplots()
		self.fig.tight_layout()
		self.fig.subplots_adjust(bottom=0)

		self.a1_x, self.a1_y = a1_x, a1_y
		self.shape = shape
		self.size_dict = size_dict
		self.well_spacing = well_spacing

		self.well_dict = {}  # maps well names to Well objects
		self.well_list = []

		self.makeWells()  # populates a dict of well_name : Well
		self.refresh()  # adds dict of wells to canvas in 8x12 grid

	def makeWells(self):
		self.well_rows = [chr(x) for x in range(ord('A'), ord('H') + 1)]
		self.well_nums = [x for x in range(1, 13)]

		for idx_r, row in enumerate(self.well_rows):
			for idx_n, num in enumerate(self.well_nums):
				well_name = row + str(num)
				self.well_list.append(well_name)
				x_coord = self.a1_x + self.well_spacing * idx_n
				y_coord = self.a1_y + self.well_spacing * (12 - idx_r)
				size_param = self.size_dict[self.shape]

				self.well_dict[well_name] = Well((x_coord, y_coord),
												 self.shape, size_param)

	def setMarker(self, shape):
		self.shape = shape
		for name in self.well_list:
			orig_well = self.well_dict[name]
			new_well = Well(orig_well.center, shape, self.size_dict[self.shape])
			self.well_dict[name] = new_well

	def refresh(self):
		self.ax.clear()
		self.ax.axis('off')
		self.ax.axis('equal')
		for name in self.well_list:
			self.ax.add_artist(self.well_dict[name].marker)
		self.fig.canvas.draw()

	def markTarget(self, name):
		self.well_dict[name].markTarget()

	def markFilled(self, name):
		self.well_dict[name].markFilled()

	def markEmpty(self, name):
		self.well_dict[name].markEmpty()

	def emptyWells(self):
		# mark all wells as empty
		for name in self.well_list:
			self.well_dict[name].markEmpty()

	def show(self):
		self.fig.canvas.draw()