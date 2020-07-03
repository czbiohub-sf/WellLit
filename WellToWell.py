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


class WelltoWell:
	'''
   * Loads a csv file into a pandas DataFrame, checking for duplicates or invalid Well labels
   * Parses a validated DataFrame into a TransferProtocol
   * Updates Transfers on functions connected to user actions, i.e. next, skipped, failed
   * Writes Transfers to transferlog.csv


    User-facing functions:
        next, skip, failed - marks transfers

    Internal functions:
        checkDuplicatesSource
        checkDuplicatesTarget
        parseDataframe

    Objects
         2 x PlateLighting
             96 x Well
         1 x TransferProtocol
             N x PlateTransfer
                M x Transfer
    '''

	def __init__(self, csv=None):
		self.csv = csv
		self.error_msg = ''
		self.df = None
		self.tp = None

		if self.csv is not None:
			self.loadCsv(csv)

	def loadCsv(self, csv):
		try:
			self.df = pd.read_csv(csv)
		except:
			print('Failed to load file csv %s' % csv)
			return '_'

		hasSourDupes, msg_s = self.checkDuplicateSource()
		hasDestDupes, msg_d = self.checkDuplicateDestination()

		if hasSourDupes or hasDestDupes:
			print(str(msg_s) + msg_d)
			self.df = None
		else:
			self.tp = TransferProtocol(self.df)

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