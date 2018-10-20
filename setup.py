from setuptools import find_packages, setup

setup(
  name='d1_examples',
  version='2.1.0',
  packages=find_packages(),
  include_package_data=True,
  zip_safe=False,
  install_requires=[
    'requests',
    'flask',
    'flask-headers',
    'gunicorn',
    'pyopenssl',
    'dataone.common',
  ],
)
