#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='pysensu-yelp',
    version='0.2.2',
    provides=['pysensu_yelp'],
    description='Emits Yelp-flavored Sensu events to a Sensu Client',
    url='https://github.com/Yelp/pysensu-yelp',
    author='Yelp Operations Team',
    author_email='operations@yelp.com',
    packages=find_packages(exclude=['tests']),
    install_requires=['ordereddict'],
    license='Copyright Yelp 2014, all rights reserved',
)
