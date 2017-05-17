#!/usr/bin/env bash
pip3 install -r requirements/common-shop.txt
pip3 install -r requirements/reqGit-shop.txt
pip3 uninstall -y django-cms django-shop django-jet pinax-stripe

cwd=$(pwd)

cd ${cwd}/source/django-jet
yarn install
python setup.py build && python setup.py install

pip3 uninstall -y django
cd ${cwd}/source/django
npm install
python setup.py build && python setup.py install

pip uninstall -y django-cms
cd ${cwd}/source/django-cms
yarn install
python setup.py build && python setup.py install

pip uninstall -y django-cascade
cd ${cwd}/source/djangocms-cascade
yarn install
python setup.py build && python setup.py install

cd ${cwd}/source/django-admin-interface
yarn install
python setup.py build && python setup.py install

pip3 install djangorestframework==3.5.2
