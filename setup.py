from setuptools import setup, find_packages

# Read the contents of the README
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ocs-authentication',
    version='0.0.1',
    description='Authentication backends and utilities for the OCS applications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/observatorycontrolsystem/ocs-authentication',
    packages=find_packages(),
    python_requires='>=3.7',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    install_requires=[
        'django>=3.2,<4.0',
        'djangorestframework>=3.12,<3.13',
        'requests>=2.22,<2.27',
    ],
    extras_require={
        'tests': ['pytest']
    }
)
