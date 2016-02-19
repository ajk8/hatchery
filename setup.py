from setuptools import setup


with open('hatchery/_version.py') as f:
    exec(f.read())


setup(
    name='hatchery',
    version=__version__,
    description='Continuous delivery helpers for python projects',
    author='Adam Kaufman',
    author_email='kaufman.blue@gmail.com',
    url='https://github.com/ajk8/hatchery',
    download_url='https://github.com/ajk8/hatchery/tarball/' + __version__,
    license='MIT',
    packages=['hatchery'],
    package_data={'hatchery': ['snippets/*']},
    entry_points={'console_scripts': ['hatchery=hatchery.main:hatchery']},
    install_requires=[
        'funcy==1.6',
        'dirsync==2.1',
        'docopt==0.6.2',
        'six==1.10.0',
        'wheel==0.26.0',
        'pyyaml==3.11',
        'logbook==0.12.5'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development'
    ],
    keywords='virtualenv development'
)
