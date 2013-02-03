#!/usr/bin/python

## encoding: utf-8

table = "gemeindeverzeichnis"

import sqlite3 as sql
import os

## look up a German city or county
# 
# You can even look up states or Germany as a whole, but this will
# most likely not be what you want. 
# 
# @param query a query string of the from [<city>|<county>]{1}[<state>]{0,} 
# @return a dictionary with keys 'city', 'county', 'state', 'country', 'zipcode', 'latitude', 'longitude'
def lookup(query):
	'''
	basic usage (and tests)

	>>> d = lookup("Sonthofen")
	>>> d['zipcode']
	'87527'
	>>> d = lookup("Neustadt, Niedersachsen")
	>>> d['city']
	'Neustadt am Rübenberge'

	'''
	d = _initial(query)
	conn = sql.connect(os.path.join(os.path.dirname( __file__ ), 'germany.db'))
	conn.row_factory = _factory
	cur = conn.cursor()

	
	s = [t.strip() for t in query.split(',')]
	name = s[0]
	state = s[1] if len(s)>1 else None

	# keys to try
	keys = ['city', 'county']
	res = None
	for k in keys:
		q = "SELECT * FROM %s WHERE %s LIKE ?" % (table, k)
		cur.execute(q, ('%'+name+'%',))
		res = cur.fetchall()
		if len(res)>0:
			key = k
			break

	
	if res is not None and len(res)>0 and state is not None:
		q = "SELECT * FROM %s WHERE %s LIKE ? AND state LIKE ?" % (table, key)
		cur.execute(q, ('%'+name+'%', '%'+state+'%'))
		newres = cur.fetchall()
		res = newres if len(newres)>0 else res

	res = res[0] if len(res)>0 else d
	# TODO what about multiple results?

	res = _manicure(res)

	return res 

## get dicts from sqlite3
def _factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
        return d



def _initial(q):
	keys = ['id', 'city', 'county', 'state', 'country', 'zipcode', 'latitude', 'longitude']
	values = [None]*8
	ret = dict(zip(keys,values))

	return ret

def _manicure(r):
	try:
		r['city'] = r['city'].split(',')[0]
	except AttributeError:
		pass

	return r

if __name__=="__main__":
	pass
	#'''
	s = ["Sonthofen", "Neustadt, Niedersachsen", "Neustadt, Bayern"]
	for q in s:
		print(lookup(q))
	#'''
