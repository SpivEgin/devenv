#!/usr/bin/env bash
pip3 install -r requirements/common.txt
pip3 install -r requirements/reqGit.txt
pip3 uninstall -y django django-cms django-cascade django-oscar django-jet pinax-stripe

cd /c//Source/CMS/devenv/source/django
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/django-oscar
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/djangocms-cascade
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/django-jet
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/pinax-stripe
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/django-cms
yarn install
python setup.py build && python setup.py install
