# Tow

Tow is an app for controlling UNH's tow carriage motion. It accesses functions
in the ACS Motion Control C library through a wrapper module called `acsc`,
which is part of the [ACSpy](https://github.com/petebachant/ACSpy) package.

## Dependencies

  * Python 3
  * PyQt5
  * [ACSpy](https://github.com/petebachant/ACSpy) (available via `pip install acspy`)
  * ACS motion control C library (must be obtained from ACS Motion Control)

## Installing

After installing all the necessary dependencies, execute

    pip install .

If you'd like to create a shortcut, run

    make shortcut

This shortcut can be copied wherever you like, pinned to the taskbar, etc.
