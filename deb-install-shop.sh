#!/usr/bin/env bash
pip3 install -r requirements/common-shop.txt
pip3 install -r requirements/reqGit-shop.txt
pip3 uninstall -y django django-cms django-cascade django-oscar django-jet pinax-stripe

cd ~/source/django
yarn install
python setup.py build && python setup.py install

cd ~/source/django-shop
yarn install
python setup.py build && python setup.py install

cd ~/source/djangocms-cascade
yarn install
python setup.py build && python setup.py install

cd ~/source/django-jet
yarn install
python setup.py build && python setup.py install

cd ~/source/pinax-stripe
yarn install
python setup.py build && python setup.py install

cd ~/source/django-cms
yarn install
python setup.py build && python setup.py install
