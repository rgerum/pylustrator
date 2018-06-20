from setuptools import setup

setup(name='pylustrator',
      version="0.7.2",
      description='Adds interactivity to arrange panels in matplotlib',
      author='Richard Gerum',
      author_email='richard.gerum@fau.de',
      license='GPLv3',
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
