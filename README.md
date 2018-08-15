# django-tally

[![build_status](
    https://api.travis-ci.org/CodeYellowBV/django-tally.svg?branch=master
)](https://travis-ci.org/CodeYellowBV/django-tally)
[![code_coverage](
    https://codecov.io/gh/CodeYellowBV/django-tally/branch/master/graph/badge.svg
)](https://codecov.io/gh/CodeYellowBV/django-tally)

Django tally is a small package to easily keep tallies of data in Django
applications.
This package only works for apps using postgres databases.

## Running the tests
Just running `./setup.py test` requires python3, postgres, a database called
`django-tally-test`, and a user with write access to said database.

To avoid all these requirements you can also run
`docker-compose run django_tally ./setup.py test` which only requires Docker to
be installed.

