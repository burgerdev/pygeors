#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name: geo.py
# Purpose: Geoinformation for DE based on opengeodb data and openstreetmap webservice
# Author: burger@burgerdev.de
# Created: 08.01.2013
# Copyright: (c) Markus Döring 2013,
#	plz.db is in the public domain (thanks to opengeodb.org)
#	full text search results are covered by the Database Contents License (DbCL) 1.0
# Licence: GPL3, ODbL (see openstreetmap.org for details)
#-------------------------------------------------------------------------------


# =======================================
# imports for openstreetmap.org queries
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError
import xml.etree.ElementTree as etree
#
# =======================================


# =======================================
# geographic functions for sqlite
from math import sin, cos, acos, radians
import sqlite3 

"""
great circle distance

input: 	latitudes and longitudes
	radius (default: earth radius in km)
output: distance on the surface, units as in input
"""
def gcd(lat1, lon1, lat2, lon2, r=6367.5):
	lat1=radians(float(lat1))
	lat2=radians(float(lat2))
	lon1=radians(float(lon1))
	lon2=radians(float(lon2))

	return r*acos( cos(lat1)*cos(lat2)*cos(lon1-lon2) + sin(lat1)*sin(lat2) )
#
# =======================================

# =======================================
# python stdlib imports
from collections import Iterable
import json
import pprint
# 
# =======================================




# =======================================
# START GEO FUNCTIONS
# =======================================

# global connection to zipcode DB 
conn = sqlite3.connect('plz.db')
conn.create_function("GCD", 4, gcd)




"""
geographic location object

This object represents a geographic location in terms of zip codes and city limits
(as opposed to street addresses and the like). This object prefers German locations
at the moment.

Attributes:
	city - string
	zipcode - string
	state - string
	countrycode - string
	country - string
	latlon - string


Methods: 
	complete()

Basic Usage:

>>> g = GeoLoc()
>>> g.zipcode = "87527"
>>> g.complete()
>>> g.city
'Sonthofen'

>>> g = GeoLoc()
>>> g.city = "Sonthofen"
>>> g.complete()
>>> g.zipcode
'87527'

>>> g = GeoLoc()
>>> g.latlon = (47.51, 10.29)
>>> g.complete()
>>> g.zipcode
'87527'
>>> g.city
'Sonthofen'

"""
class GeoLoc(object):
	city = None
	zipcode = None
	county = None
	state = None
	country = "Deutschland"
	countrycode = "de"
	latlon = None

	# experimental
	query = None
	_alternatives = None
	
	def __init__(self, tup=None):
		if isinstance(tup, (list, tuple)):
			# result from zipcode DB query
			self._fromtuple(tup)
		elif isinstance(tup, dict):
			self._fromdict(tup)
		elif tup is not None:
			print("Error: Unknown constructor argument")

	def _copyfrom(self, g):
		if not isinstance(g, GeoLoc):
			return
		self.city = g.city
		self.zipcode = g.zipcode
		self.county = g.county
		self.state = g.state
		self.country = g.country
		self.countrycode = g.countrycode
		self.latlon = g.latlon
		self._alternatives = g._alternatives


			
	def _fromtuple(self, tup):
		# input is expected to be a result of a database query
		self.zipcode = tup[4]
		self.city = tup[1]
		try:
			self.latlon = (float(tup[2]), float(tup[3]))
		except TypeError:
			self.latlon = None

	def _fromdict(self, d):
		# input is expected to be a result from an osm query

		addr = d["address"]
		names = ["city", "county", "state", "countrycode", "country"]	
		keys = addr.keys()
		[setattr(self, attr, addr[attr]) for attr in  keys if attr in names]

		if "town" in keys:
			self.city = addr["town"]

		self.latlon = (float(d["lat"]), float(d["lon"]))
		
		# add zip code, we are guaranteed to find one with given coordinates
		g = GeoLoc()
		g.latlon = self.latlon
		g.complete(useosm=False)
		self.zipcode = g.zipcode


	
	def __str__(self):
		lat = self.latlon[0] if self.latlon is not None else 0
		lon = self.latlon[1] if self.latlon is not None else 0
		return "%s, %s" % (self.city if self.city is not None else self.county, self.state)
		#return "%s (country=%s, zip=%s, lat=%.2f, lon=%.2f)" % (self.city if self.city is not None else self.county, self.countrycode, self.zipcode, lat, lon)

	def complete(self, useosm=True):
		""" 
		look up complete GeoLoc information
		"""
		
		if self.zipcode is not None:
			self._ziplookup()
		elif self.city is not None or self.query is not None:
			self._citylookup()
		elif self.latlon is not None:
			self._reverselookup()

	def _ziplookup(self):
		cur = conn.cursor()
		cur.execute("SELECT * FROM geodb_zip WHERE zip = ? LIMIT 1", (self.zipcode,))
		res = cur.fetchone()
		if res is not None:
			self.city = res[1]
			self.latlon = (float(res[2]), float(res[3]))
			self.zipcode = res[4]


	def _citylookup(self):
		
		# prepare query parameters
		p = {}
		if self.query is not None:
			p["q"] = self.query
		if self.city is not None:
			p["city"] = self.city
		if self.zipcode is not None:
			p["postalcode"] = self.zipcode
		if self.state is not None:
			p["state"] = self.state

		# get data from openstreetmap.org (thanks, you guys)
		r = _osmquery(p)
		if r is None:
			return

		#self._pprint(r)

		g = [GeoLoc(res) for res in r]
		if len(g)>0:
			self._copyfrom(g[0])
		if len(g)>1:
			self._alternatives = g[1:]

	def _reverselookup(self):
		cur = conn.cursor()
		cur.execute("SELECT * FROM geodb_zip ORDER BY GCD(lat, lon, ?, ?) ASC LIMIT 1", self.latlon)
		res = cur.fetchone()
		if res is not None:
			temp = self.latlon
			self._fromtuple(res)
			self.latlon = temp

	def _pprint(self, obj):
		pp = pprint.PrettyPrinter()
		print("================================")
		pp.pprint(obj)
		print("================================")
		



def code(s):
	"""
	Free text search
	
	input: string (future: file, Iterable, ...)
	output: Iterable of GeoLocs, None on error

	tests: 

	>>> code(None)
	>>>
	"""
	return None

	

def _osmquery(d={}):
	"""
	query the open street map database via http

	input: 	d - dict query parameters (good ideas are "q", "city", "postalcode")
	output: result - list of dicts (see osm documentation)
	"""

	osmurl = "http://nominatim.openstreetmap.org/search"
	zzheaders = {"User-Agent": "zeezaar.de city lookup - contact webmaster@burgerdev.de; Thanks, you guys!"}
	params = {'format': 'json', 'countrycodes': 'de', 'addressdetails': 1, 'email': 'webmaster@burgerdev.de', 'accept-language': 'de-de'}

	params.update(d)

	params = urlencode(params)
	req = Request("?".join([osmurl, params]), headers=zzheaders, unverifiable=True)
	try:
		x = urlopen(req)
	except URLError as err:
		return None

	return json.loads(x.read().decode("utf-8"))

def distance(loc, locs):
	"""
	calculate distance between GeoLocs
	
	input: 	GeoLoc start, GeoLoc end
		GeoLoc start, GeoLoc-iterable end
	output:	distance, or None on error
		distance-iterable with None on error
	
	tests:

	>>> distance(None, None)
	>>>

	>>> distance(None, [None, None])
	[None, None]
	"""
	
	if not isinstance(loc, GeoLoc):
		return [None for d in locs] if isinstance(locs,Iterable) else None
	loc.complete()

	(lat, lon) = loc.latlon

	ziparray = [d.zipcode for d in locs] if isinstance(locs,Iterable) else [locs.zipcode, ]
	
	cur = conn.cursor() 
	res = []
	for zipcode in ziparray:
		cur.execute("SELECT GCD(lat,lon,?,?) AS dist FROM geodb_zip WHERE zip in (?)", (lat, lon, zipcode))
		res += [float(d[0]) for d in cur.fetchall()]

	if len(res) == 0:
		return None
	if len(res) == 1:
		return res[0]
	
	return res

	
def area(loc, dist):
	"""
	get surrounding GeoLocs
	
	input: GeoLoc, distance in km
	output: GeoLoc-iterable or None on error
	
	tests:

	>>> area(None, 0)
	>>> 

	>>> g = GeoLoc([87527, "Sonthofen", None, None, "87527"])
	>>> L = area(g,0.1)
	>>> len(L)
	1
	>>> L[0].zipcode
	'87527'
	"""

	if not isinstance(loc, GeoLoc):
		return None

	if loc.latlon is None:
		loc.complete()

	(lat, lon) = loc.latlon

	try:
		cur = conn.cursor()
		cur.execute("SELECT * FROM geodb_zip WHERE GCD(lat,lon,?,?) <= ?", (lat, lon, dist))
	except sqlite3.OperationalError as e:
		print(e.message)
		return None
	res = [GeoLoc(d) for d in cur.fetchall()]

	if len(res) == 0:
		return None
	
	return res




if __name__ == "__main__":
# testing
	a = GeoLoc()
	a.zipcode = "69115"
	b = GeoLoc()
	b.zipcode = "74906"

	print("Heidelberg to Bad Rappenau: %.2fkm" % distance(a,b))

	c = GeoLoc()
	c.zipcode = "87527"
	d = area(c,10)
	e = distance(c,d)
	print("\nZip codes near Sonthofen:")
	for q,r in zip(d,e):
		print("%s, %.2fkm" % (str(q), r))
	
	print("\nFree Text Search:")	
	g = GeoLoc()
	g.city = "Sonthofen"
	g.complete()
	print(g)

	print("\nReverse Geocoding")
	g = GeoLoc()
	g.latlon = (47.5,10.3)
	g.complete()
	print(g)



