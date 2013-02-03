#!/usr/bin/python

import sqlite3 as sql
import os
from geors import loc_factory as fact


if __name__=="__main__":
	inconn = sql.connect(os.path.join(os.path.dirname( __file__ ), 'germany.db'))
	inconn.row_factory = fact
	gvcur = inconn.cursor()
	outconn = sql.connect(os.path.join(os.path.dirname( __file__ ), 'zipcode.db'))
	outconn.row_factory = fact
	zipcur = outconn.cursor()


	zipcur.execute("SELECT * FROM zipcode")
	zips = zipcur.fetchall()

	for z in zips:
		zipcode = z["zipcode"]
		
		gvcur.execute("SELECT * FROM gemeindeverzeichnis WHERE zipcode=? LIMIT 1", (zipcode,))
		mun = gvcur.fetchone()
		if mun is None:
			print("No county for %s" % zipcode)
			continue
		key = mun["key_county"]
		gvcur.execute("SELECT * FROM gemeindeverzeichnis WHERE key_county=? AND key_VB is NULL AND key_municipality IS NULL LIMIT 1", (key,))
		countyrow = gvcur.fetchone()
		if countyrow is None:
			print("No county with key %s" % key)
			continue
		county = countyrow["descr"]

		print("Adding %s to %s" %(county, zipcode))

		#zipcur.execute("UPDATE zipcode SET county=? WHERE zipcode=?", (county, zipcode)
	
	#outconn.commit()
		
	
