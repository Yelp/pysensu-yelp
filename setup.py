#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='pysensu-yelp',
    version='0.1.0',
    provides=['pysensu_yelp'],
    description='Emits Yelp-flavored Sensu events to a Sensu Client',
    url='https://gitweb.yelpcorp.com/?p=pysensu-yelp.git',
    author='Yelp Operations Team',
    author_email='operations@yelp.com',
    packages=find_packages(exclude=['tests']),
    install_requires=['ordereddict'],
    license='Copyright Yelp 2014, all rights reserved',
)