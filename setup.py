"""Setup."""

from setuptools import setup

setup(
    name='saas',
    version='1.0',
    description='Screenshot as a service',
    author='Ludwig Kristoffersson',
    author_email='ludwig@kristoffersson.org',
    license='MIT',
    packages=['saas'],
    install_requires=[
        'wheel',
        'beeprint',
        'elasticsearch'
    ],
    entry_points={
        'console_scripts': [
            'saas = saas.saas:main'
        ]
    }
)
