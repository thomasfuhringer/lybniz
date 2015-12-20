#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup

data_files = [('share/applications',['lybniz.desktop']),('share/pixmaps',['images/lybniz.png']),('share/gnome/help/lybniz/C',['doc/lybniz.xml']),('share/gnome/help/lybniz/C/figures',['doc/figures/lybniz_colour_graph_small.png'])]

setup(
	name = 'lybniz',
	version = '1.3.3',
	description = 'Graph Plotter',
	author = 'Thomas Führinger, Sam Tygier',
	author_email = 'ThomasFuhringer@Yahoo.com, samtygier@yahoo.co.uk',
	contact = 'Sam Tygier',
	contact_email = 'samtygier@yahoo.co.uk',
	url = 'github.com/thomasfuhringer/lybniz',
	scripts = ['lybniz.py'],
	data_files = data_files,
	license = 'BSD',
	)

