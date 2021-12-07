#!/usr/bin/env python3
# Joana Cabrera
# 3/15/2020

# revised
# Andrew Cote
# 6/30/2020

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import kivy
import json, os
kivy.require('1.11.1')
from kivy.app import App
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
# noinspection ProblematicWhitespace
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.metrics import sp
from kivy.properties import ObjectProperty, StringProperty

from .plateLighting import PlateLighting
from abc import ABC, abstractmethod


class WellLitWidget(FloatLayout):
	status = StringProperty('')

	def __init__(self, **kwargs):
		super(WellLitWidget, self).__init__(**kwargs)
		self._popup = None
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		self._keyboard.bind(on_key_down=self._on_keyboard_up)
		Config.set('kivy', 'exit_on_escape', 0)


	def updateLights(self):
		"""
		To be called after every user action, updating the current WellPlots by accessing self.ids.___plate
		"""
		pass

	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_up=self._on_keyboard_up)
		self._keyboard = None

	def _on_keyboard_up(self, keyboard, keycode, text, modifiers):
		if keycode[1] == 'esc' or keycode[1] == 'q':
			self.showPopup('Are you sure you want to exit?', 'Confirm exit', func=self.quit)

	def log(self, msg):
		self.status = msg

	def dismiss_popup(self):
		self._popup.dismiss()

	def showPopup(self, error, title: str, func=None):
		self._popup = WellLitPopup()
		self._popup.title = title
		self._popup.show(error.__str__(), func=func)

	def reset_plates(self):
		self.ids.source_plate.initialize()
		self.ids.dest_plate.initialize()

	def resetAll(self):
		self.ids.notificationLabel.font_size = 20

	def quit(self, _):
		App.get_running_app().stop()


class WellPlot(BoxLayout):
	'''
	Acts as a Kivy GUI block which contains a matplotlib figure as its only content.
	matplotlib figure resizes with BoxLayout resizing.

	Owns a PlateLighting object
	'''
	shape = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(WellPlot, self).__init__(**kwargs)
		self.pl = None

	def initialize(self):
		# load configs
		cwd = os.getcwd()
		config_path = os.path.join(cwd, "wellLitConfig.json")
		with open(config_path) as json_file:
			configs = json.load(json_file)

		self.num_wells = configs['num_wells']

		if self.type == 'source_plate':
			A1_X = configs[self.num_wells]["A1_X_source"]
			A1_Y = configs[self.num_wells]["A1_Y_source"]

		if self.type == 'dest_plate':
			A1_X = configs[self.num_wells]["A1_X_dest"]
			A1_Y = configs[self.num_wells]["A1_Y_dest"]

		size_param = configs[self.num_wells]["size_param"]
		well_spacing = configs[self.num_wells]["well_spacing"]

		# set up PlateLighting object
		self.pl = PlateLighting(A1_X, A1_Y, self.shape, size_param, well_spacing)
		self.add_widget(FigureCanvasKivyAgg(figure=self.pl.fig))

	def on_touch_down(self, touch):
		# this method keeps the app from crashing if the plot is clicked on
		pass


class ConfirmPopup(Popup):
	def __init__(self, txt_file_path=None):
		super(ConfirmPopup, self).__init__()
		self.pos_hint={'left': 1}
		self.txt_file_path = txt_file_path

	def show(self, text):
		content = BoxLayout(orientation='vertical')
		popup_lb = Label(text=text, font_size=25)
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
			txt_file = open(self.txt_file_path, "w")
			txt_file.close()


class WellLitPopup(Popup):
	def __init__(self):
		super(WellLitPopup, self).__init__()

	def show(self, error_str, func=None):
		content = BoxLayout(orientation='vertical')
		popup_lb = Label(text=error_str, font_size=25, text_size=(sp(450), sp(800)), halign='center', valign='center')
		content.add_widget(popup_lb)
		if func is not None:
			confirm_button = Button(text='Confirm', size_hint=(0.5, 0.4))
			content.add_widget(confirm_button)
			confirm_button.bind(on_press=func)
			confirm_button.bind(on_press=self.dismiss)
			close_button = Button(text='Cancel', size_hint=(0.5, .4))
		else:
			close_button = Button(text='Close', size_hint=(0.5, .4))
		content.add_widget(close_button)
		close_button.bind(on_press=self.dismiss)
		self.content = content
		self.open()


