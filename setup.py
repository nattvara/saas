"""Setup."""

from setuptools import setup, find_packages

setup(
    name='saas',
    version='1.0',
    description='Screenshot as a service',
    author='Ludwig Kristoffersson',
    author_email='ludwig@kristoffersson.org',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'wheel==0.32.*',
        'beeprint==2.4.*',
        'elasticsearch==6.3.*',
        'selenium==3.141.*',
        'fusepy==3.0.*',
        'psutil==4.3.*',
    ],
    entry_points={
        'console_scripts': [
            'saas = saas.saas:main'
        ]
    }
)
