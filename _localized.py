#!/usr/bin/python

import os,sys

sys.path.append(os.path.join(os.path.dirname( __file__ ), 'countries', 'Germany'))

import _germany

def lookup(q):
	return _germany.lookup(q)
