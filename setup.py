#!/usr/bin/env python3

import os
import re
import sys

from setuptools import find_packages, setup


def get_version(*file_paths):
    """Retrieves the version from django_simple_2fa/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)

    raise RuntimeError('Unable to find version string.')


version = get_version('django_simple_2fa', '__init__.py')

if sys.argv[-1] == 'publish':
    try:
        import wheel

        print('Wheel version: ', wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.md').read()
requirements = open('requirements.txt').readlines()

setup(
    name='django-simple-2fa',
    version=version,
    description='',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Michael Sulyak',
    author_email='michael@sulyak.info',
    url='https://github.com/rebotics/django-simple-2fa',
    packages=find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    zip_safe=False,
    keywords='django-simple-2fa',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django :: 5',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
