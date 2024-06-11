from setuptools import setup


setup(name='ztem2edi',
      version='0.1',
      description='Easy-install script to convert ZTEM data stored in a Geotools .gdb to EDI MT data files',
      url='http://github.com/eroots/ztem2edi',
      author='Eric Roots',
      author_email='eroots087@gmail.com',
      packages=['ztem2edi'],
      long_description=open('readme.rst').read(),
      scripts=[],
      entry_points={'console_scripts': ['ztem2edi = ztem2edi.ztem_to_edi:main']},
      install_requires=['numpy==1.20.3',
                        'pandas>=2.0, <3',
                        'geosoft'],
      include_package_data=False)
