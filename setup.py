#!/usr/bin/env python3

import re
from setuptools import setup


with open('./trading212/__init__.py', 'r') as f:
    version = re.search(r'(?<=__version__ = .)([\d\.]*)', f.read()).group(1)

with open('./README.md', 'r') as f:
    readme = f.read()


if __name__ == '__main__':
    setup(
        name='trading212-web-api',
        version=version,
        author='Zsolt Mester',
        author_email='',
        description='Unoffial client for Trading212 API broker',
        long_description=readme,
        license='MIT',
        url='https://github.com/meister245/trading212-web-api',
        project_urls={
            "Code": "https://github.com/meister245/trading212-web-api",
            "Issue tracker": "https://github.com/meister245/trading212-web-api/issues",
        },
        packages=[
            'trading212'
        ],
        install_requires=[
            'requests',
            'cachetools',
            'ratelimit',
            'html5lib',
            'beautifulsoup4',
        ],
        extras_require={
            'dev': ['pytest']
        },
        python_requires='>=3.8',
        include_package_data=False
    )
