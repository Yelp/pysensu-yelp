#!/usr/bin/env python
from setuptools import find_packages
from setuptools import setup

setup(
    name='pysensu-yelp',
    version='1.0.2',
    provides=['pysensu_yelp'],
    description='Emits Yelp-flavored Sensu events to a Sensu Client',
    url='https://github.com/Yelp/pysensu-yelp',
    author='Yelp Operations Team',
    author_email='operations@yelp.com',
    packages=find_packages(exclude=['tests']),
    classifiers=[
         'Programming Language :: Python :: 3',
         'Programming Language :: Python :: 3.6',
         'Programming Language :: Python :: 3.7',
         'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    package_data={
        'pysensu_yelp': ['py.typed'],
    },
    license='Copyright Yelp 2014, all rights reserved',
)
