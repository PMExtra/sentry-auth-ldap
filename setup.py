#!/usr/bin/env python
"""
sentry-auth-ldap
================

An extension for Sentry which authenticates users from
an LDAP server and auto-adds them to an organization in sentry.
"""
from setuptools import setup, find_namespace_packages

with open("README.md", "r") as readme:
    long_description = readme.read()

install_requires = [
    'django-auth-ldap==4.1.0',
    'sentry>=21.9.0',
]

setup(
    name='sentry-auth-ldap',
    version='21.9.11',
    author='Chad Killingsworth <chad.killingsworth@banno.com>, Barron Hagerman <barron.hagerman@banno.com>, PM Extra <pm@jubeat.net>',
    author_email='pm@jubeat.net',
    url='https://github.com/PMExtra/sentry-auth-ldap',
    description='A Sentry extension to add an LDAP server as an authentication source.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_namespace_packages(),
    license='Apache-2.0',
    zip_safe=False,
    install_requires=install_requires,
    include_package_data=True,
    download_url='https://github.com/PMExtra/sentry-auth-ldap',
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development'
    ],
    project_urls={
        'Bug Tracker': 'https://github.com/PMExtra/sentry-auth-ldap/issues',
        'CI': 'https://github.com/PMExtra/sentry-auth-ldap/actions',
        'Source Code': 'https://github.com/PMExtra/sentry-auth-ldap',
    },
)
