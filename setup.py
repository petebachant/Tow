#!/usr/bin/env python
# coding=utf-8

from setuptools import setup
import os
from tow import __version__

setup(
    name="Tow",
    version=__version__,
    author="Pete Bachant",
    author_email="petebachant@gmail.com",
    packages=["tow"],
    scripts=["scripts/tow-script.py", "scripts/tow.bat"],
    include_package_data=True,
    url="https://github.com/petebachant/Tow.git",
    license="LICENSE",
    description="Python desktop app for controlling the UNH tow/wave tank tow carriage.",
    long_description=open("README.md").read(),
)
