pygeors
=======

Python Radius Search Module

Content
-------

This python module provides a few things related to geospatial information:

* a class **GeoLoc** representing geographic locations
* a function **distance** that calculates the distance of two GeoLoc-objects
* a function **area** that returns all regions near a GeoLoc within a specified distance 

This module does only work for **German** zip codes, but extensions are planned.

Author
------

Markus D&ouml;ring, http://burgerdev.de


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

The contents of the sqlite3 database plz.db are provided by <http://opengeodb.org/> and are in the public domain.


Thanks
------

Thanks to opengeodb.org for providing the geospatial data.


