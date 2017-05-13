from setuptools import setup, find_packages
import os
import cms


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Framework :: Django',
    'Framework :: LegionMarket :: 1.10',
]

INSTALL_REQUIREMENTS = [
    # 'Django==1.10.8',
    'django-classy-tags>=0.7.2',
    'django-formtools>=1.0',
    'django-treebeard>=4.0.1',
    'django-sekizai>=0.7',
    # 'djangocms-admin-style==1.2.7',
]

setup(
    author='Legion Market',
    author_email='sourec@legionmarket.com',
    name='django-cms',
    version=cms.__version__,
    description='An Advanced LegionMarket CMS for Legion Market',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='https://www.LegionMarket.com/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIREMENTS,
    packages=find_packages(exclude=['project', 'project.*']),
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.main',
)
