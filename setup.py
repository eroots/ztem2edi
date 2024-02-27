from setuptools import setup


setup(name='ztem2edi',
      version='0.1',
      description='Easy-install script to convert ZTEM data stored in a Geotools .gdb to EDI MT data files',
      url='http://github.com/eroots/ztem2edi',
      author='Eric Roots',
      author_email='eroots087@gmail.com',
      packages=[],
      long_description=open('readme.rst').read(),
      scripts=['ztem2edi.py'],
      entry_points={'console_scripts': ['ztem2edi = ztem2edi:main']},
      install_requires=['numpy==1.20.3',
                        'pandas=2.0',
                        'python==3.9',
                        'geosoft'],
      include_package_data=False)
