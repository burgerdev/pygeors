#!/usr/bin/python

import sqlite3 as sql
from sqlite3 import InterfaceError
import os
import csv

class result:

	m = "type,text,key_state,key_RB,key_county,key_VB,key_municipality,descr,area,population,pop_male,pop_female,pop_per_sqkm,zipcode,longitude,latitude,travel_key,travel_descr,eu_key,eu_descr".split(',')

	def __init__(self, r):
		self.r = r

	def __iter__(self):
		return self
	
	def __next__(self):
		t = next(self.r)
		return dict(zip(self.m, t))

def newdict():
	keys = "country,state,county,city,zipcode,key_state,key_RB,key_county,key_VB,key_municipality,area,population,pop_male,pop_female,pop_per_sqkm,longitude,latitude,travel_key,travel_descr,eu_key,eu_descr".split(',')
	return dict(zip(keys,[""]*len(keys)))
	


def maprow(row):
	a = newdict()
	kill = []
	for k in a.keys():
		try:
			if k in ["latitude", "longitude", "area"]:
				try:
					a[k] = float(row[k].replace(',', '.'))
				except ValueError as e:
					kill.append(k)

			elif "pop" in k or "key" in k and not "travel" in k:
				try:
					a[k] = int(row[k].replace(" ", ""))
				except ValueError as e:
					kill.append(k)
			else:
				a[k] = row[k]

		except KeyError:
			print("not adding %s" % k)

	for k in kill:
		del a[k]
	
	return a


def insert(d):

	cur = conn.cursor()
	keys = [k for k in d.keys()]
	values = [d[k] for k in d.keys()]
	for i in range(len(values)):
		try:
			values[i] = values[i].strip()
		except AttributeError:
			pass

	q = "INSERT INTO gemeindeverzeichnis (%s) VALUES (" % ", ".join(keys) + ", ".join(["?"]*len(keys)) + ");"
	#print(q)
	try:
		cur.execute(q, values)
	except InterfaceError as e:
		print(values)
		raise e

if __name__=="__main__":
	conn = sql.connect(os.path.join(os.path.dirname( __file__ ), 'germany.db'))
	cur = conn.cursor()

	f = open("gemeindeverzeichnis.csv", 'r')
	r = csv.reader(f, delimiter=',', quotechar='"')
	it = result(r)
	header=next(r)
	newheader = list(newdict().keys())
	newheader.sort()

	c = ["id INTEGER PRIMARY KEY"]
	a = []
	for item in newheader:
		if item in ["latitude", "longitude", "area"]:
			c.append(item + " FLOAT")
		elif "pop" in item or "key" in item and not "travel" in item:
			c.append(item + " INT")
		else:
			c.append(item + " VARCHAR(250)")
		a.append(item)
	c = ", ".join(c)
	a = ", ".join(a)

	try:
		q = "CREATE TABLE gemeindeverzeichnis (%s)" % c
		print("Executing '%s' ..." % q)
		cur.execute(q)
	except Exception:
		print("Skipping table creation...")
	
	gen = {'country': 'Germany', 'state': '', 'county': '', 'city': ''}
	for row in it:
		n=int(row["type"])
		if n==10:
			gen["state"] = row["descr"]
			continue
		elif n==40:
			gen["county"] = row["descr"]
			continue
		elif row["key_municipality"] == "":
			continue
		else:
			gen["city"] = row["descr"]

		row.update(gen)
		d = maprow(row)
		insert(d)

	conn.commit()
		
	
