#!/usr/bin/env python3

# Joana Cabrera
# 3/15/2020
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import matplotlib as mpl
import os, json
from enum import Enum


class WStatus(Enum):
	empty = 1
	target = 2
	filled = 3
	unused = 4
	control = 5
	rescan = 6
	discarded = 7

	def color(self):
		return {
			'empty': 'darkslategray',
			'target': 'yellow',
			'filled': 'red',
			'unused': 'black',
			'control': 'white',
			'rescan': 'blue',
			'discarded': 'whitesmoke'
			}[self.name]


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
			self.marker = Rectangle((self.center[0] - self.size_param/2, self.center[1] - self.size_param/2),
									width=size_param, height=size_param, color=self.status.color(),
									zorder=0)

	def markEmpty(self):
		self.status = WStatus.empty
		self.marker.set_color(self.status.color())
		self.marker.zorder = 1

	def markDiscarded(self):
		self.status = WStatus.discarded
		self.marker.set_color(self.status.color())
		self.marker.zorder = 3

	def markFilled(self):
		self.status = WStatus.filled
		self.marker.set_color(self.status.color())
		self.marker.zorder = 2

	def markTarget(self):
		self.status = WStatus.target
		self.marker.set_color(self.status.color())
		self.marker.zorder = 3

	def markControl(self):
		self.status = WStatus.control
		self.marker.set_color(self.status.color())
		self.marker.zorder = 3

	def markUnused(self):
		self.status = WStatus.unused
		self.marker.set_color(self.status.color())
		self.marker.zorder = 0

	def markRescan(self):
		self.status = WStatus.rescan
		self.marker.set_color(self.status.color())
		self.marker.zorder = 5

	def setMarker(self, shape, size):
		self.shape = shape
		self.size_param = size

		if shape == 'circle':
			self.marker = Circle(self.center, radius=self.size_param, color=self.status.color(), zorder=0)
		elif shape == 'square':
			self.marker = Rectangle((self.center[0] - self.size_param/2, self.center[1] - self.size_param/2), width=self.size_param, height=self.size_param,
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

		cwd = os.getcwd()
		config_path = os.path.join(cwd, "wellLitConfig.json")
		with open(config_path) as json_file:
			configs = json.load(json_file)
		num_wells = configs['num_wells']
		if num_wells == '384':
			rows = 24
			self.well_rows = [chr(x) for x in range(ord('A'), ord('P') + 1)]
			self.well_nums = [x for x in range(1, rows + 1)]
		else:
			rows = 12
			self.well_rows = [chr(x) for x in range(ord('A'), ord('H') + 1)]
			self.well_nums = [x for x in range(1, rows + 1)]

		for idx_r, row in enumerate(self.well_rows):
			for idx_n, num in enumerate(self.well_nums):
				well_name = row + str(num)
				self.well_list.append(well_name)
				x_coord = self.a1_x + self.well_spacing * idx_n
				y_coord = self.a1_y + self.well_spacing * (rows - idx_r)
				size_param = self.size_dict[self.shape]

				self.well_dict[well_name] = Well((x_coord, y_coord),
												 self.shape, size_param)

	def setMarker(self, shape):
		self.shape = shape
		for name in self.well_list:
			# orig_well = self.well_dict[name]
			# new_well = Well(orig_well.center, self.shape, self.size_dict[self.shape])
			self.well_dict[name].setMarker(shape, self.size_dict[shape])
		self.refresh()

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

	def markDiscarded(self, name):
		self.well_dict[name].markDiscarded()

	def markControl(self, name):
		self.well_dict[name].markControl()

	def markUnused(self, name):
		self.well_dict[name].markUnused()

	def markRescan(self, name):
		self.well_dict[name].markRescan()

	def emptyWells(self):
		# mark all wells as empty
		for name in self.well_list:
			self.well_dict[name].markEmpty()

	def blackoutWells(self):
		# mark all wells unused
		for name in self.well_list:
			self.well_dict[name].markUnused()

	def show(self):
		self.fig.canvas.draw()