#! /usr/bin/env python3
from setuptools import setup


BINDER_TAG = '1.2.0'


setup(
    name='django-tally',
    packages=['django_tally'],
    version='0.1.0',
    description='A package for easily tallying Django data.',
    author='Daan van der Kallen',
    author_email='mail@daanvdk.com',
    keywords=['django', 'tally'],
    test_suite='tests',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    install_requires=[
        'django>=1.11',
    ],
    tests_require=[
        'django-binder>=1',
    ],
    extras_require={
        'app': ['django-binder>=1'],
    },
    dependency_links=[
        'git+http://github.com/CodeYellowBV/django-binder.git'
        '@{0}#egg=django-binder-{0}'.format(BINDER_TAG),
    ],
)
