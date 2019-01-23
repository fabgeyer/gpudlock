#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open

with open('README.md', 'r', 'utf-8') as fd:
    long_description = fd.read()

setup(
    name='gpudlock',
    version='0.20190119',
    description='Distributed locking of GPUs',
    long_description=long_description,
    url='https://github.com/fabgeyer/gpudlock',
    author='fabgeyer',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
    ],
    keywords='gpu',
    packages=find_packages(),
    install_requires=['redlock-py'],
    entry_points={
        'console_scripts': [
            'gpudlock=gpudlock:main',
        ],
    },
)
