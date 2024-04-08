from setuptools import setup, find_packages

setup(
    name='vrbcibackend',
    version='1.0.0',
    url='https://github.com/mo-gaafar/vr-bci-companion',
    author='Mohamed Gaafar',
    author_email='mohamed_gaafar@ieee.org',
    description='This is a fastapi backend for interfacing purposes',
    packages=find_packages(exclude=['tests']),
    package_dir={'': 'src'},
    requires=['fastapi', 'pymongo', 'bson', 'typing', 'database', 'pydantic', 'uvicorn',
              'fastapi', 'pymongo', 'bson', 'typing', 'database', 'pydantic', 'uvicorn'],
)
