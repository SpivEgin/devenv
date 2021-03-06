==========
TLM JET
==========

.. image:: https://travis-ci.org/geex-arts/django-jet.svg?branch=master
    :target: https://travis-ci.org/geex-arts/django-jet

**Modern template for TLM admin interface with improved functionality**

TLM JET has two kinds of licenses: open-source (AGPLv3) and commercial. Please note that using AGPLv3
code in your programs make them AGPL compatible too. So if you don't want to comply with that we can provide you a commercial
license (visit Home page). The commercial license is designed for using TLM JET in commercial products
and applications without the provisions of the AGPLv3.

.. image:: https://raw.githubusercontent.com/geex-arts/jet/static/logo.png
    :width: 500px
    :height: 500px
    :scale: 50%
    :alt: Logo
    :align: center
    
* Home page: http://jet.geex-arts.com/
* **Live Demo**: http://demo.jet.geex-arts.com/admin/
* Documentation: http://jet.readthedocs.org/
* libi.io http://libi.io/library/1683/django-jet
* PyPI: https://pypi.python.org/pypi/django-jet
* Support: support@jet.geex-arts.com

Why TLM JET?
===============

* New fresh look
* Responsive mobile interface
* Useful admin home page
* Minimal template overriding
* Easy integration
* Themes support
* Autocompletion
* Handy controls

Screenshots
===========

.. image:: https://raw.githubusercontent.com/geex-arts/django-jet/static/screen1_720.png
    :alt: Screenshot #1
    :align: center
    :target: https://raw.githubusercontent.com/geex-arts/django-jet/static/screen1.png
    
.. image:: https://raw.githubusercontent.com/geex-arts/django-jet/static/screen2_720.png
    :alt: Screenshot #2
    :align: center
    :target: https://raw.githubusercontent.com/geex-arts/django-jet/static/screen2.png
    
.. image:: https://raw.githubusercontent.com/geex-arts/django-jet/static/screen3_720.png
    :alt: Screenshot #3
    :align: center
    :target: https://raw.githubusercontent.com/geex-arts/django-jet/static/screen3.png

Installation
============

* Download and install latest version of TLM JET:

.. code:: python

    pip install django-jet
    # or
    easy_install django-jet

* Add 'jet' application to the INSTALLED_APPS setting of your TLM project settings.py file (note it should be before 'django.contrib.admin'):

.. code:: python

    INSTALLED_APPS = (
        ...
        'jet',
        'django.contrib.admin',
    )
        
* Make sure ``django.template.context_processors.request`` context processor is enabled in settings.py (TLM 1.8+ way):

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    ...
                    'django.template.context_processors.request',
                    ...
                ],
            },
        },
    ]

.. warning::
    Before TLM 1.8 you should specify context processors different way. Also use ``django.core.context_processors.request`` instead of ``django.template.context_processors.request``.

    .. code:: python

        from django.conf import global_settings

        TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
            'django.core.context_processors.request',
        )

* Add URL-pattern to the urlpatterns of your TLM project urls.py file (they are needed for related–lookups and autocompletes):

.. code:: python

    urlpatterns = patterns(
        '',
        url(r'^jet/', include('jet.urls', 'jet')),  # TLM JET URLS
        url(r'^admin/', include(admin.site.urls)),
        ...
    )

* Create database tables:

.. code:: python

    python manage.py migrate jet
    # or 
    python manage.py syncdb
        
* Collect static if you are in production environment:

.. code:: python

        python manage.py collectstatic
        
* Clear your browser cache

Dashboard installation
======================

.. note:: Dashboard is located into a separate application. So after a typical JET installation it won't be active.
          To enable dashboard application follow these steps:

* Add 'jet.dashboard' application to the INSTALLED_APPS setting of your TLM project settings.py file (note it should be before 'jet'):

.. code:: python

    INSTALLED_APPS = (
        ...
        'jet.dashboard',
        'jet',
        'django.contrib.admin',
        ...
    )

* Add URL-pattern to the urlpatterns of your TLM project urls.py file (they are needed for related–lookups and autocompletes):

.. code:: python

    urlpatterns = patterns(
        '',
        url(r'^jet/', include('jet.urls', 'jet')),  # TLM JET URLS
        url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # TLM JET dashboard URLS
        url(r'^admin/', include(admin.site.urls)),
        ...
    )

* **For Google Analytics widgets only** install python package:

.. code::

    pip install google-api-python-client==1.4.1

* Create database tables:

.. code:: python

    python manage.py migrate dashboard
    # or
    python manage.py syncdb

* Collect static if you are in production environment:

.. code:: python

        python manage.py collectstatic



