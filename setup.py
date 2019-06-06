from setuptools import setup

setup(name='pylustrator',
      version="0.9.2",
      description='Adds interactivity to arrange panels in matplotlib',
      long_description=open('readme.rst').read(),
      url='https://bitbucket.org/fabry_biophysics/pylustrator',
      license="GPLv3",
      author='Richard Gerum',
      author_email='richard.gerum@fau.de',
      packages=['pylustrator'],
      install_requires=[
          'numpy',
          'matplotlib',
          'pyqt5',
          'qtpy',
          'qtawesome',
          'scikit-image'
      ],
      )
