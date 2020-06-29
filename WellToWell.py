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


class WellToWell:
	""" A class for mapping a set of transfers from one plate to another plate.
	"""
	def __init__(self):

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
		# metadata
		self.plate_timestr = time.strftime("%Y%m%d-%H%M%S")

		# load path from config file
		self.cwd = os.getcwd()
		self.config_path = os.path.join(self.cwd, "wellLitConfig.json")
		with open(self.config_path) as json_file:
			self.configs = json.load(json_file)
		self.csv_folder_path = self.configs['OUTPUT_PATH']

		# make path if it does not exist
		if not os.path.exists(self.csv_folder_path):
			os.makedirs(self.csv_folder_path)

		# this will be the filename header for all files associated with this run
		self.csv_file_header = self.plate_timestr + '_' + plate_name + '_plate_to_plate'

		# set up file path for the output file
		self.csv_file_path = os.path.join(self.csv_folder_path, self.csv_file_header)

		# use the first 5 rows of the output file for metadata
		self.metadata = [['%Plate Timestamp: ', self.plate_timestr], ['%Plate Barcode: ', plate_barcode], ['%Recorder Name: ', recorder], ['%Aliquoter Name: ', aliquoter], ['%Timestamp', 'Tube Barcode', 'Location']]
		with open(self.csv_file_path + '.csv', 'w', newline='') as csvFile:
			writer = csv.writer(csvFile)
			writer.writerows(self.metadata)


	def isPlate(self, check_input):
		if re.match(r'SP[0-9]{6}$', check_input) or check_input == 'EDIT':
			return True
		return False

	def isName(self, check_input):
		if any(char.isdigit() for char in check_input):
			return False
		elif check_input == 'EDIT':
			return True
		return True

	def reset(self):
		# clear tube locations
		for w in self.well_names:
			self.tube_locations[w] = None

		# reset index
		self.current_idx = 0

		# reset scanned tubes
		self.scanned_tubes.clear()

