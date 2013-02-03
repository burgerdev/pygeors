pygeors
=======

Python Radius Search Module (Germany, at the moment)

Content
-------

This python module provides a few things related to geospatial information:

* a class **GeoLoc** representing geographic locations
* a function **query** that lets you search for locations
* a function **distance** that calculates the distance of two GeoLoc-objects
* a function **area** that returns all regions near a GeoLoc within a specified distance 
* an sqlite3 database of German communities with hierarchical and geospatial information (probably the most up-to-date database around)

This module does only work for **German** locations, but extensions are planned.
[Website](http://burgerdev.de/pygeors)

Author
------

[Markus Döring](http://burgerdev.de)


Licence
-------

The code in geors.py is available under the terms of the GNU General Public License v3:

> This program is free software: you can redistribute it and/or modify
> it under the terms of the GNU General Public License as published by
> the Free Software Foundation, either version 3 of the License, or
> (at your option) any later version.
> 
> This program is distributed in the hope that it will be useful,
> but WITHOUT ANY WARRANTY; without even the implied warranty of
> MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
> GNU General Public License for more details.
> 
> You should have received a copy of the GNU General Public License
> along with this program.  If not, see <http://www.gnu.org/licenses/>.

The contents of germany.db and gemeindeverzeichnis.csv are a derived work of the [Gemeindeverzeichnis](https://www.destatis.de/DE/ZahlenFakten/LaenderRegionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/Verwaltungsgliederung/Verwalt4QAktuell.html),
whose copyright owner is the German federal statistic office on behalf of the community of German statistical offices. 
It may be copied and distributed at will, provided the German federal statistic office is 
attributed as source.

The contents of zipcode.db are derived from the Gemeindeverzeichnis and 
data provided by opengeodb.org, which is in the public domain.


Thanks
------

  * opengeodb.org, for providing the geospatial data.
  * the Federal Republic of Germany, for providing statistical data

