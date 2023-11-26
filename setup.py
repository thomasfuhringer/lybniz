#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from distutils.core import setup
from glob import glob
import os
import shutil

shutil.copyfile('lybniz.py', 'lybniz')

data_files = [('share/icons/hicolor/scalable/apps',['images/lybniz.svg']),('share/man/man1',['lybniz.1']),('share/applications',['lybniz.desktop']),('share/pixmaps',['images/lybniz.png']),('share/gnome/help/lybniz/C',['doc/lybniz.xml']),('share/gnome/help/lybniz/C/figures',['doc/figures/lybniz_colour_graph_small.png'])]

directories = glob('locale/*/*/')
for directory in directories:
    files = glob(directory+'*')
    data_files.append(('share/'+directory, files))

setup(
	name = 'lybniz',
	version = '3.0.4',
	description = 'Graph Plotter',
	author = 'Thomas Führinger, Sam Tygier',
	author_email = 'ThomasFuhringer@Yahoo.com, samtygier@yahoo.co.uk',
	contact = 'Thomas Führinger',
	contact_email = 'ThomasFuhringer@Yahoo.com',
	url = 'github.com/thomasfuhringer/lybniz',
	packages = [],
	scripts = ['lybniz'],
	data_files = data_files,
	license = 'BSD',
	)

os.remove("lybniz")
