#!/usr/bin/env python3
# Joana Cabrera
# 3/15/2020

import argparse
import logging
import csv
import time 
import os
import re
import json
import pandas as pd
from plateLighting import PlateLighting, Well


class WellToWell:

	"""
	A class for mapping a set of transfers from one plate to another plate.

	Takes two WellPlate objects as source and dest upon initialization.
	"""
	def __init__(self, source=None, dest=None):
		"""
		:param source: a
		:param dest:
		:return:
		"""
		self.source = source
		self.dest   = dest

		# make a list of the well row characters
		self.well_rows = [chr(x) for x in range(ord('A'), ord('H') + 1)] # move to state machine
		
		# make a list of well names in column wise order 
		self.well_names = []
		for i in range(1, 13):
			for letter in self.well_rows:
				self.well_names.append(letter+str(i))
		# target well index
		self.current_idx = 0

		# make a dictionary with the tube locations as the key and the barcodes as the value
		self.tube_locations = {}
		for w in self.well_names:
			self.tube_locations[w] = None

		self.scanned_tubes = []
		self.filename = ''

	def loadCSV(self, path):
		self.df = pd.read(path)

	def openCSV(self):
		pass

	def reset(self):
		# clear tube locations
		for w in self.well_names:
			self.tube_locations[w] = None

		# reset index
		self.current_idx = 0

		# reset scanned tubes
		self.scanned_tubes.clear()

