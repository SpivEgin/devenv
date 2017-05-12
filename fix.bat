REM C:\Source\CMS\nLegionMarket\xP34env0\Scripts\activate

REM ls
cd \Source\CMS\devenv\source\djangocms-cascade
yarn install
python setup.py build && python setup.py install

cd \Source\CMS\devenv\source\django-jet
yarn install
python setup.py build && python setup.py install

cd \Source\CMS\devenv\source\pinax-stripe
yarn install
python setup.py build && python setup.py install

cd \Source\CMS\devenv\source\django-cms
yarn install
python setup.py build && python setup.py install
