=============================
django-simple-2fa
=============================

.. image:: https://badge.fury.io/py/django-simple-2fa.svg
    :target: https://badge.fury.io/py/django-simple-2fa

.. image:: https://travis-ci.org/expert-m/django-simple-2fa.svg?branch=master
    :target: https://travis-ci.org/expert-m/django-simple-2fa

.. image:: https://codecov.io/gh/expert-m/django-simple-2fa/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/expert-m/django-simple-2fa

Your project description goes here

Documentation
-------------

The full documentation is at https://django-simple-2fa.readthedocs.io.

Quickstart
----------

Install django-simple-2fa::

    pip install django-simple-2fa

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_simple_2fa.apps.DjangoSimple2faConfig',
        ...
    )

Add django-simple-2fa's URL patterns:

.. code-block:: python

    from django_simple_2fa import urls as django_simple_2fa_urls


    urlpatterns = [
        ...
        url(r'^', include(django_simple_2fa_urls)),
        ...
    ]

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


Development commands
---------------------

::

    pip install -r requirements_dev.txt
    invoke -l


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
