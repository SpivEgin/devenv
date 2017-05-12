#!/usr/bin/env bash
pip3 install -r requirements/common-oscar.txt
pip3 install -r requirements/reqGit-oscar.txt
pip3 uninstall -y django-cascade django-oscar django-jet pinax-stripe

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

pip3 uninstall -y django-cms
cd /c//Source/CMS/devenv/source/django-cms
yarn install
python setup.py build && python setup.py install

pip3 uninstall -y django
cd /c//Source/CMS/devenv/source/django
yarn install
python setup.py build && python setup.py install
