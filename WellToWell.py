#!/usr/bin/env python3
# Joana Cabrera
# 3/15/2020

import logging, csv, time, os, re, json, uuid, datetime, argparse
import pandas as pd
from plateLighting import PlateLighting, Well
import csv, re, uuid, datetime
import pandas as pd
import numpy as np
from plateLighting import Well, PlateLighting
from Transfer import Transfer, TransferProtocol

#TODO: regexp check on well names
#TODO: Write log files

class WelltoWell:
	"""
	* Loads a csv file into a pandas DataFrame, checking for duplicates or invalid Well labels
	* Parses a validated DataFrame into a TransferProtocol
	* Updates Transfers on functions connected to user actions, i.e. next, skipped, failed
	* Writes Transfers to transferlog.csv
	"""


	def __init__(self, csv=None):
		self.csv = csv
		self.error_msg = ''
		self.df = None
		self.tp = None

		if self.csv is not None:
			self.loadCsv(csv)

	def tp_present(self):
		if self.tp is not None:
			return True
		else:
			self.log('No transferProtocol loaded into memory.')
			return False

	def next(self):
		if self.tp_present():
			self.tp.complete()

	def skip(self):
		if self.tp_present():
			self.tp.skip()

	def failed(self):
		if self.tp_present():
			self.tp.failed()

	def undo(self):
		if self.tp_present():
			self.tp.undo()

	def nextPlate(self):
		if self.tp_present():
			self.tp.nextPlate()

	def log(self, error):
		self.error_msg = error
		print(error)
		logging.info(error)

	def loadCsv(self, csv):
		try:
			self.df = pd.read_csv(csv)
			self.log('CSV file %s loaded' % csv)
		except:
			self.log('Failed to load file csv %s' % csv)
			return None

		hasSourDupes, msg_s = self.checkDuplicateSource()
		hasDestDupes, msg_d = self.checkDuplicateDestination()

		if hasSourDupes or hasDestDupes:
			self.log(str(msg_s) + msg_d)
			self.df = None
		else:
			self.tp = TransferProtocol(df=self.df)
			self.log('TransferProtocol with %s transfers in %s plates created' %
					 (self.tp.num_transfers, self.tp.num_plates))

	def checkDuplicateDestination(self):
		hasDupes = False
		dupes_mask = self.df.duplicated(subset='TargetWell')
		dupes = self.df.where(dupes_mask).dropna()
		duplicates = set(dupes['TargetWell'].values)
		error_msg = ''

		if len(duplicates) == 0:
			return hasDupes, error_msg
		else:
			hasDupes = True

		for element in duplicates:
			subset = self.df.where(df['TargetWell'] == element).dropna()

			indices = []
			for index, row in subset.iterrows():
				indices.append(index)
				target = row['TargetWell']
			error_msg = error_msg + 'TargetWell %s is duplicated in rows %s' % (target, indices)
		return hasDupes, error_msg

	def checkDuplicateSource(self):
		plates = self.df['PlateName'].drop_duplicates().values

		hasDupes = False
		error_msg = []
		msg = ''

		for plate in plates:
			batch = self.df.where(self.df['PlateName'] == plate).dropna()

			dupes_mask = batch.duplicated(subset='SourceWell')
			dupes = batch.where(dupes_mask).dropna()
			duplicates = set(dupes['SourceWell'].values)

			if len(duplicates) == 0:
				continue
			else:
				hasDupes = True

			message = 'Plate %s has duplicates: \n ' % plate
			for element in duplicates:
				subset = batch.where(batch['SourceWell'] == element).dropna()

				indices = []
				for index, row in subset.iterrows():
					indices.append(index)
				msg = msg + 'SourceWell %s is duplicated in rows %s' % (element, indices) + '\n'

			error_msg.append(msg)
			msg = ''

		return hasDupes, error_msg