Tow
===

[![Stories in Ready](https://badge.waffle.io/petebachant/tow.png?label=ready&title=Ready)](https://waffle.io/petebachant/tow)

Tow is an app for controlling UNH's tow carriage motion. It accesses functions
in the ACS Motion Control C library through a wrapper module called `acsc`,
which is part of the [ACSpy](https://github.com/petebachant/ACSpy) package.


Dependencies
------------

  * Python 2.7
  * PyQt4
  * [ACSpy](https://github.com/petebachant/ACSpy) (available via `pip install acspy`)
  * ACS motion control C library (must be obtained from ACS Motion Control)


Installing
----------
After installing all the necessary dependencies, execute

    python setup.py install

If you'd like to create a shortcut, run

    python create_shortcut.py

This shortcut can be copied wherever you like, pinned to the taskbar, etc.


License
-------

Tow copyright (c) 2013-2015 Peter Bachant

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


