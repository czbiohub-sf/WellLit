#!/usr/bin/env python3
# Joana Cabrera
# 3/15/2020

# revised
# Andrew Cote
# 6/30/2020

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import kivy
import json, logging, time, os, time, csv
kivy.require('1.11.1')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
# noinspection ProblematicWhitespace
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserListView
from .plateLighting import PlateLighting


class WellLitWidget(FloatLayout):
	def __init__(self, **kwargs):
		super(WellLitWidget, self).__init__(**kwargs)
		self._popup = None

	def dismiss_popup(self):
		self._popup.dismiss()

	def updateLights(self):
		'''
		dest_wells:
			- colors well empty to filled, current target
		source_wells:
			- colors well filled to empty, current target
		:return:
		'''
		pass

	def reset_plates(self):
		self.ids.source_plate.initialize()
		self.ids.dest_plate.initialize()

	def resetAll(self): 
		self.plateLighting.reset()
		self.ids.notificationLabel.font_size = 50
		self.canUndo = False
		self.warningsMade = False


class Well2WellApp(App):
	def build(self):
		return WellLitWidget()


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
		self.pos_hint={'y': 800 / Window.height}
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
	Well2WellApp.run()