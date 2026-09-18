#!/usr/bin/env python
from setuptools import find_packages
from setuptools import setup

setup(
    name='pysensu-yelp',
    version='1.0.3',
    provides=['pysensu_yelp'],
    description='Emits Yelp-flavored Sensu events to a Sensu Client',
    url='https://github.com/Yelp/pysensu-yelp',
    author='Yelp Operations Team',
    author_email='operations@yelp.com',
    packages=find_packages(exclude=['tests']),
    classifiers=[
         'Programming Language :: Python :: 3',
         'Programming Language :: Python :: 3.10',
         'Programming Language :: Python :: 3.11',
         'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.10',
    package_data={
        'pysensu_yelp': ['py.typed'],
    },
    license='Apache License 2.0',
)
