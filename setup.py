#!/usr/bin/env python2.7

import subprocess
version = subprocess.check_output(["git", "describe", "--tags", "--always"])[:-1]

try:
	from setuptools import setup
except ImportError:
	print "Can't find setuptools; dependencies will not be installed."
	from distutils.core import setup

setup(
	name		=	"lib-solaris-facility-macros",
	version		=	version,
	description	=	"Solaris-wide Sardana macros",
	author		=	"Grzegorz Kowalski",
	author_email=	"g.kowalski@uj.edu.pl",
	url			=	"http://git.m.cps.uj.edu.pl/beamline-software/lib-solaris-facility-macros",
	packages	=	["facility"],
	package_dir	=	{"facility": "."},
	zip_safe	=	False,
	setup_cfg	=	True
)