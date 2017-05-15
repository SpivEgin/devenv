#!/usr/bin/env bash
pip3 install -r requirements/common-shop.txt
pip3 install -r requirements/reqGit-shop.txt
pip3 uninstall -y django-cascade django-shop django-jet pinax-stripe

cd /c//Source/CMS/devenv/source/django-shop
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/djangocms-cascade
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/django-jet
yarn install
python setup.py build && python setup.py install

cd /c//Source/CMS/devenv/source/django-admin-interface
yarn install
python setup.py build && python setup.py install

pip3 uninstall -y django-cms
cd /c//Source/CMS/devenv/source/django-cms
yarn install
python setup.py build && python setup.py install

pip3 uninstall -y django
cd /c//Source/CMS/devenv/source/django
yarn install
python setup.py build && python setup.py install
