from setuptools import setup

setup(name='Pylustration',
      version="0.7",
      description='Adds interactivity to arrange panels in matplotlib',
      author='Richard Gerum',
      author_email='richard.gerum@fau.de',
      license='MIT',
      packages=['pylustration'],
      install_requires=[
          'numpy',
          'matplotlib'
      ],
      )
