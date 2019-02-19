#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup

data_files = [('share/man/man1',['lybniz.1']),('share/applications',['lybniz.desktop']),('share/pixmaps',['images/lybniz.png']),('share/gnome/help/lybniz/C',['doc/lybniz.xml']),('share/gnome/help/lybniz/C/figures',['doc/figures/lybniz_colour_graph_small.png'])]

setup(
	name = 'lybniz',
	version = '3.0.2',
	description = 'Graph Plotter',
	author = 'Thomas Führinger, Sam Tygier',
	author_email = 'ThomasFuhringer@Yahoo.com, samtygier@yahoo.co.uk',
	contact = 'Thomas Führinger',
	contact_email = 'ThomasFuhringer@Yahoo.com',
	url = 'github.com/thomasfuhringer/lybniz',
	scripts = ['lybniz'],
	data_files = data_files,
	license = 'BSD',
	)

