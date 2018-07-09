#! /usr/bin/env python3
from setuptools import setup


setup(
    name='django-buckets',
    packages=['buckets'],
    version='0.1.0',
    description='A package for easily tallying Django data.',
    author='Daan van der Kallen',
    author_email='mail@daanvdk.com',
    keywords=['django', 'tally', 'buckets'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    test_suite='tests',
)
