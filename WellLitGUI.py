#!/usr/bin/env python3
# Joana Cabrera
# 3/15/2020

# revised
# Andrew Cote
# 6/30/2020

import kivy
kivy.require('1.11.1')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from plateLighting import *
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
# noinspection ProblematicWhitespace
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserListView
import json, logging, time, os, time, csv
from WellToWell import WelltoWell

'''
TODO:
* repace print with logging info 
'''



import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    filename='filename.txt')  # pass explicit filename here
logger = logging.get_logger()  # get the root logger
logger.warning('This should go in the file.')


class LoadDialog(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)

#TODO: Add warning messages about file importing into a popup window
#TODO: Add buttons that change the marker type of a WellPlot object

class Well2WellWidget(FloatLayout):
	def __init__(self, **kwargs):
		super(Well2WellWidget, self).__init__(**kwargs)
		self._popup = None
		self.wtw = None

	def reset_plates(self):
		self.ids.source_plate.initialize()
		self.ids.dest_plate.initialize()

	def show_load(self):
		content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
		self._popup = Popup(title='Load File', content=content, size_hint=(0.5, 0.5))
		self._popup.open()

	def load(self, path, filename):
		target = (os.path.join(str(path), str(filename[0])))
		if os.path.isfile(target):
			print(target)
		else:
			print('not a file')
		self.dismiss_popup()

		# Reset the plates and create a new Well2Well transfer to manage them
		self.reset_plates()



	def dismiss_popup(self):
		self._popup.dismiss()

	def next(self):
		pass

	def undo(self):
		pass

	def loadTransfer(self):
		pass

	def abortTransfer(self):
		pass
		# self.confirm_popup.show()

	def resetAll(self): 
		self.plateLighting.reset()
		self.ids.notificationLabel.font_size = 50
		self.canUndo = False
		self.warningsMade = False


class Well2WellApp(App):
	def build(self):
		return Well2WellWidget()


class WellPlot(BoxLayout):
	'''
	Acts as a Kivy GUI block which contains a matplotlib figure as its only content.
	matplotlib figure resizes with BoxLayout resizing.

	Owns a PlateLighting object
	'''
	shape = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(WellPlot, self).__init__(**kwargs)

	def initialize(self):
		# load configs
		cwd = os.getcwd()
		config_path = os.path.join(cwd, "wellLitConfig.json")
		with open(config_path) as json_file:
			configs = json.load(json_file)
		A1_X = configs["A1_X"]
		A1_Y = configs["A1_Y"]
		size_param = configs["size_param"]
		well_spacing = configs["well_spacing"]

		# set up PlateLighting object
		self.pl = PlateLighting(A1_X, A1_Y, self.shape, size_param, well_spacing)
		self.add_widget(FigureCanvasKivyAgg(figure=self.pl.fig))

	def on_touch_down(self, touch):
		# this method keeps the app from crashing if the plot is clicked on
		pass


class ConfirmPopup(Popup):
	def __init__(self, txt_file_path=None):
		super(ConfirmPopup, self).__init__()
		self.pos_hint={'y': 800 /  Window.height}
		self.txt_file_path = txt_file_path

	def show(self):
		content = BoxLayout(orientation='vertical')
		popup_lb = Label(text='Finish plate?', font_size=30)
		content.add_widget(popup_lb)
		button_box = BoxLayout(orientation='horizontal', size_hint=(1, .4))
		content.add_widget(button_box)

		# configure yes button
		self.yes_button = Button(text='yes')
		button_box.add_widget(self.yes_button)
		self.yes_button.bind(on_press=self.yes_callback)
		self.yes_button.bind(on_press=self.dismiss)

		# configure no button
		no_button = Button(text='no')
		button_box.add_widget(no_button)
		no_button.bind(on_press=self.dismiss)


		self.content = content
		self.open()

	def yes_callback(self, *args):
		if self.txt_file_path:
			txt_file = open(self.txt_file_path,"w")
			txt_file.close()
		Well2WellApp.get_running_app().p.resetAll()


class WellLitPopup(Popup):
	def __init__(self):
		super(WellLitPopup, self).__init__()
		self.pos_hint={'y': 800 /  Window.height}

	def show(self,error_str):
		content = BoxLayout(orientation='vertical')
		popup_lb = Label(text=error_str, font_size = 30)
		content.add_widget(popup_lb)
		close_button = Button(text='Close', size_hint=(1, .4))
		content.add_widget(close_button)
		close_button.bind(on_press=self.dismiss)
		self.content = content
		self.open()


if __name__ == '__main__':
	cwd = os.getcwd()
	logging.basicConfig(filename=cwd + '\WelltoWell_log.log',
						format='%(asctime)s %(levelname)-8s %(message)s',
						level=logging.INFO,
						datefmt='%Y-%m-%d %H:%M:%S')
	logging.info('Session started')
	Window.size = (1600, 1200)
	# Window.fullscreen = True
	Well2WellApp().run()
