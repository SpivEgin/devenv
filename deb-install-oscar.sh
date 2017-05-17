#!/usr/bin/env bash
pip3 install -r ${cwd}/requirements/common-oscar.txt
pip3 install -r ${cwd}/requirements/reqGit-oscar.txt
pip3 uninstall -y django django-cms django-cascade django-oscar django-jet pinax-stripe

cwd=$(pwd)


cd ${cwd}/source/django
npm install
python setup.py build && python setup.py install

cd ${cwd}/source/django-oscar
yarn install
python setup.py build && python setup.py install

cd ${cwd}/source/djangocms-cascade
yarn install
python setup.py build && python setup.py install

cd ${cwd}/source/django-jet
yarn install
python setup.py build && python setup.py install

cd ${cwd}/source/pinax-stripe
yarn install
python setup.py build && python setup.py install

cd ${cwd}/source/django-cms
yarn install
python setup.py build && python setup.py install
