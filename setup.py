from setuptools import find_packages, setup

setup(
  name='d1_examples',
  version='2.2.0',
  packages=find_packages(),
  include_package_data=True,
  zip_safe=False,
  install_requires=[
    'requests',
    'flask',
    'flask-headers',
    'gunicorn',
    'dataone.common',
    'python-dateutil',
  ],
)
