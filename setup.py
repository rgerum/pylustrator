from setuptools import setup

long_description = ""
try:
    long_description = open('readme.rst').read()
except FileNotFoundError:
    pass

setup(name='pylustrator',
      version="0.9.2",
      description='Adds interactivity to arrange panels in matplotlib',
      long_description=long_description,
      url='https://bitbucket.org/fabry_biophysics/pylustrator',
      license="GPLv3",
      author='Richard Gerum',
      author_email='richard.gerum@fau.de',
      packages=['pylustrator'],
      install_requires=[
          'natsort',
          'numpy',
          'matplotlib',
          'pyqt5',
          'qtpy',
          'qtawesome',
          'scikit-image'
      ],
      )
