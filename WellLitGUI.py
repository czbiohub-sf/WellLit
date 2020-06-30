#!/usr/bin/env python3
# Joana Cabrera
# 3/15/2020

import kivy
kivy.require('1.11.1')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from plateLighting import *
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserListView
import json, logging, time, os, time, csv
from WellToWell import WellToWell


# https://stackoverflow.com/questions/51947447/kivy-select-folder-with-filechooser
class LoadDialog(FloatLayout):

	def __init__(self, **kwargs):
		super(LoadDialog, self).__init__(**kwargs)
		self.load = ObjectProperty(None)
		self.cancel = ObjectProperty(None)

	def show(self):
		content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
		self._popup = Popup(title="Load file", content=content,
						size_hint=(0.9, 0.9))
		self._popup.open()


class Well2WellWidget(FloatLayout):
	def __init__(self, **kwargs):
		super(Well2WellWidget, self).__init__(**kwargs)
		self.loadfile = ObjectProperty(None)

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
	def __init__(self, shape='circle', **kwargs):
		super(WellPlot, self).__init__(**kwargs)

		self.shape = shape
		# load configs
		self.cwd = os.getcwd()
		self.config_path = os.path.join(self.cwd, "wellLitConfig.json")
		with open(self.config_path) as json_file:
			self.configs = json.load(json_file)
		A1_X = self.configs["A1_X"]
		A1_Y = self.configs["A1_Y"]
		WELL_SPACING = self.configs["WELL_SPACING"]
		SHAPE = self.configs["MARKER_SHAPE"]
		if SHAPE == 'circle':
			SIZE_PARAM = self.configs["CIRC_RADIUIS"]
			SHAPE = self.configs["MARKER_SHAPE"]
		elif SHAPE == 'square':
			SIZE_PARAM = self.configs["SQUARE_LENGTH"]

		# set up PlateLighting object
		self.pl = PlateLighting(A1_X, A1_Y, SHAPE, SIZE_PARAM, WELL_SPACING)
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
		WellLitApp.get_running_app().p.resetAll()


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
