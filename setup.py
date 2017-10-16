from setuptools import setup

setup(name='uvml',
      version='0.21',
      description='UVML Lab Code',
      url='https://github.com/mbe9a/uvml',
      author='Michael Eller',
      author_email='mbe9a@virginia.edu',
      license='MIT',
      packages=['uvml'],
      install_requires=[
          'vxi11', 'matplotlib', 'os', 'datetime', 'time', 'numpy', 'csv', 'statsmodels', 'shutil', 'mpl_toolkits'
      ],
      zip_safe=False)