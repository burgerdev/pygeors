#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package geors
# Name: geors.py
# Purpose: Geoinformation for DE based on opengeodb data and openstreetmap webservice
# Author: burger@burgerdev.de
# Created: 08.01.2013
# Copyright: (c) Markus Döring 2013,
#	plz.db is in the public domain (thanks to opengeodb.org)
#	full text search results are covered by the Database Contents License (DbCL) 1.0
# Licence: GPL3, ODbL (see openstreetmap.org for details)


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


## great circle distance
#
# compute the great circle distance between two latitude/longitude pairs
# @param lat1 first latitude 
# @param lon1 first longitude
# @param lat2 second latitude
# @param lon2 second longitude
# @param r radius (defalut: earth radius in km)
# 
# @return distance between the coordinates, units are the same as in the input
#
def gcd(lat1, lon1, lat2, lon2, r=6367.5):
	lat1=radians(float(lat1))
	lat2=radians(float(lat2))
	lon1=radians(float(lon1))
	lon2=radians(float(lon2))

	return r*acos( cos(lat1)*cos(lat2)*cos(lon1-lon2) + sin(lat1)*sin(lat2) )

## get associative arrays aka dicts from sqlite3
def loc_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d
#
# =======================================

# =======================================
# python stdlib imports
from collections import Iterable
import json
import pprint
import os.path
# 
# =======================================



# =======================================
# internal imports
from _localized import lookup
#
# =======================================



# =======================================
# START GEO FUNCTIONS
# =======================================

# global connection to zipcode DB 
_conn = sqlite3.connect(os.path.join(os.path.dirname( __file__ ), 'zipcode.db'))
_conn.create_function("GCD", 4, gcd)
_conn.row_factory = loc_factory

## openstreetmap user agent
# set this to your app's name
osm_useragent = "pygeors - autocompletion"

## openstreetmap email address
# provide an email address for OSM to contact you
osm_email = None





### geographic location object
#
# This object represents a geographic location in terms of zip codes and city limits
# (as opposed to street addresses and the like). This object prefers German locations
# at the moment.
#
#
class GeoLoc(object):
	'''
	 Basic Usage (and doctests):
	
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
	'''

	## @var city
	# the city (string, default: None)
	## @var zipcode
	# the zip code (string, default: None)
	## @var county
	# the county (string, default: None)
	## @var state
	# the state (string, default: None)
	## @var country
	# the country (string, default: "Deutschland")
	## @var countrycode
	# the countrycode, in most cases TLD (string, default: "de")
	## @var latlon
	# the city (tuple of two floats, default: None)


	## the constructor
	# @param d dict as returned by a query to geodb_zip (EXPERIMENTAL: dict as returned by a query to openstreetmap)
	#
	def __init__(self, d=None):
		self.city = None
		self.zipcode = None
		self.county = None
		self.state = None
		self.country = "Deutschland"
		self.countrycode = "de"
		self.latlon = None
		
		# experimental
		self._query = None
		self._alternatives = None

		#TODO revisit these, can't be correct anymore
		if d is None:
			return

		if "id" in d.keys():
			# result from zipcode DB query
			self._fromdbentry(d)
		elif isinstance(d, dict):
			self._fromdict(d)
		else:
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


			
	def _fromdbentry(self, d):
		# input is expected to be a result of a database query, the fields below should be set
		self.zipcode = d["zipcode"]
		self.city = d["city"]
		self.county = d["county"]
		self.country = d["country"]
		self.state = d["state"]
		try:
			self.latlon = (float(d["latitude"]), float(d["longitude"]))
		except TypeError:
			self.latlon = None
		except KeyError:
			#TODO remove hack, use _localized
			self.latlon = (float(d["lat"]), float(d["lon"]))

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


	## convert to string
	def __str__(self):

		lat = self.latlon[0] if self.latlon is not None else 0
		lon = self.latlon[1] if self.latlon is not None else 0
		return "%s (country=%s, zip=%s, lat=%.2f, lon=%.2f)" % (self.city if self.city is not None else self.county, self.countrycode, self.zipcode, lat, lon)

	def toString(self):
		return "%s, %s%s" % (self.city if self.city is not None else self.county, self.zipcode+", " if self.zipcode is not None else "", self.state)

	## look up GeoLoc information
	# Complete the geographic information in this GeoLoc object. 
	# At the moment, this works if either
	#   * the zip code is set or
	#   * the latitude/longitude pair is set or
	#   * you are lucky with openstreetmap
	# @param useosm Specify if openstreetmap query should be sent (this feature is experimental!). *Don't forget to set geors.useragent and geors.email correctly!*
	# @param deep Do you want precise results?
	def complete(self, useosm=False, deep=True):
		
		if self.zipcode is not None:
			#TODO should be unified
			self._ziplookup()

		if self.city is not None and deep:
			if useosm:
				self._osmlookup()
			else:
				self._lookup()
		if self.city is None and self.latlon is not None:
			self._reverselookup()

	def _lookup(self):
		q = self.city if self.city is not None else self.county
		if q is None or len(q)==0:
			return
		if self.state is not None:
			q += ", " + self.state
		other = GeoLoc(lookup(q))
		if other.city is not None:
			self._copyfrom(other)

	def _ziplookup(self):
		#TODO will be omitted once zip code search is implemented in _localized
		con = sqlite3.connect(os.path.join(os.path.dirname( __file__ ), 'zipcode.db'))
		con.row_factory = loc_factory
		cur = con.cursor()
		if self.zipcode is not None:
			cur.execute("SELECT * FROM zipcode WHERE zipcode = ? LIMIT 1", (self.zipcode,))
		elif self.city is not None:
			cur.execute("SELECT * FROM zipcode WHERE city = ? LIMIT 1", (self.city,))
		else:
			return

		res = cur.fetchone()
		if res is not None:
			self.city = res["city"]
			self.latlon = (float(res["lat"]), float(res["lon"]))
			self.zipcode = res["zipcode"]
			self.state = res["state"]


	def _osmlookup(self):
		
		# prepare query parameters
		p = {}
		if self._query is not None:
			p["q"] = self._query
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
		con = sqlite3.connect(os.path.join(os.path.dirname( __file__ ), 'zipcode.db'))
		con.row_factory = loc_factory
		con.create_function("GCD", 4, gcd)
		cur = con.cursor()
		cur.execute("SELECT * FROM zipcode ORDER BY GCD(lat, lon, ?, ?) ASC LIMIT 1", self.latlon)
		res = cur.fetchone()
		if res is not None:
			temp = self.latlon
			self._fromdbentry(res)
			self.latlon = temp

	def _pprint(self, obj):
		pp = pprint.PrettyPrinter()
		print("================================")
		pp.pprint(obj)
		print("================================")
		


## query the geo database
# 
# @param s the query string (format: <city|county>[,<state>] or <zipcode>)
# @return a GeoLoc object
def query(s):
	'''
	Usage

	>>> g = query('Hindelang')
	>>> g.city
	'Bad Hindelang'
	>>> g.zipcode
	'87541'
	>>> g.state
	'Bayern'
	'''

	g = GeoLoc(lookup(s))
	return g


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

## calculate distance between GeoLocs
# @param loc a GeoLoc obejct to start with
# @param locs either a GeoLoc object or a list of GeoLoc objects
# @return a float or a list of floats (depending on the input) with the distance in kilometres
#	
def distance(loc, locs):
	'''
	usage (and doctests):
	
	>>> distance(None, None)
	>>>
	>>> distance(None, [None, None])
	[None, None]
	
	'''

	if not isinstance(loc, GeoLoc):
		return [None for d in locs] if isinstance(locs,Iterable) else None
	loc.complete()

	(lat, lon) = loc.latlon

	ziparray = [d.zipcode for d in locs] if isinstance(locs,Iterable) else [locs.zipcode, ]
				
	con = sqlite3.connect(os.path.join(os.path.dirname( __file__ ), 'zipcode.db'))
	con.create_function("GCD", 4, gcd)
	con.row_factory = loc_factory
	cur = con.cursor() 
	res = []
	for zipcode in ziparray:
		cur.execute("SELECT GCD(lat,lon,?,?) AS dist FROM zipcode WHERE zipcode=?", (lat, lon, zipcode))
		res += [float(d["dist"]) for d in cur.fetchall()]

	if len(res) == 0:
		return None
	if len(res) == 1:
		return res[0]
	
	return res

## get surrounding GeoLocs
# This function gets surrounding locations for a given location. At the moment, there are a few restrictions to when this
# function will work as expected:
#   * one of these is true
#     * GeoLoc.complete() finds a latitude/longitude pair (see there to check the requirements)
#     * the input has its latitude/longitude pair GeoLoc.latlon set
#   * the location is in Germany
# @param loc a GeoLoc obejct to start with
# @param dist a distance in kilometres to search in
# @return a list of GeoLocs (aka cities) within the specified radius of loc
#	
def area(loc, dist):
	'''
	usage (and doctests):

	>>> area(None, 0)
	>>> 
	>>> g = GeoLoc({'id': 1, 'zipcode': '87527', 'city': 'Sonthofen', 'latitude': 47.510178, 'longitude': 10.289223, 'county': 'Oberallgäu', 'state': 'Bayern', 'country': 'Germany'})
	>>> L = area(g,0.1)
	>>> len(L)
	1
	>>> L[0].zipcode
	'87527'
	'''
	

	if not isinstance(loc, GeoLoc):

		return None

	if loc.latlon is None:
		loc.complete()
	if loc.latlon is None:
		return None
	(lat, lon) = loc.latlon

	con = sqlite3.connect(os.path.join(os.path.dirname( __file__ ), 'zipcode.db'))
	con.create_function("GCD", 4, gcd)
	con.row_factory = loc_factory
	cur = con.cursor() 
	
	try:
		cur.execute("SELECT * FROM zipcode WHERE GCD(lat,lon,?,?) <= ?", (lat, lon, dist))
	except sqlite3.OperationalError as e:
		print(e.message)
		return None
	res = [GeoLoc(d) for d in cur]

	if len(res) == 0:
		return None
	
	return res




if __name__ == "__main__":
	# testing
	pass
	'''
	_a = GeoLoc()
	_a.zipcode = "69115"
	_b = GeoLoc()
	_b.zipcode = "74906"

	print("Heidelberg to Bad Rappenau: %.2fkm" % distance(_a,_b))

	_c = GeoLoc()
	_c.zipcode = "87527"
	_d = area(_c,10)
	_e = distance(_c,_d)
	print("\nZip codes near Sonthofen:")
	for _q,_r in zip(_d,_e):
		print("%s, %.2fkm" % (str(_q), _r))
	
	print("\nFree Text Search:")	
	_g = GeoLoc()
	_g.city = "Sonthofen"
	_g.complete()
	print(_g)

	print("\nReverse Geocoding")
	_g = GeoLoc()
	_g.latlon = (47.5,10.3)
	_g.complete()
	print(_g)
	'''


