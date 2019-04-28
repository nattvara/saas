"""Setup."""

from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
readme = path.join(this_directory, 'README.md')
with open(readme, encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='saas',
    version='1.2',
    description='Screenshot as a service',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Ludwig Kristoffersson',
    author_email='ludwig@kristoffersson.org',
    url='https://github.com/nattvara/saas',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.7',
    install_requires=[
        'wheel==0.32.*',
        'beeprint==2.4.*',
        'elasticsearch==6.3.*',
        'selenium==3.141.*',
        'fusepy==3.0.*',
        'psutil==4.3.*',
    ],
    package_data={
        'extensions': [
            'idcac_2.9.8.xpi',
            'referer_header.xpi',
            'uBlock0_1.18.14.xpi',
        ]
    },
    entry_points={
        'console_scripts': [
            'saas = saas.saas:main'
        ]
    }
)
