from setuptools import setup
from imp import find_module, load_module

PROJECT_NAME = 'hatchery'
GITHUB_USER = 'ajk8'
GITHUB_ROOT = 'https://github.com/{}/{}'.format(GITHUB_USER, PROJECT_NAME)

found = find_module('_version', [PROJECT_NAME])
_version = load_module('{}._version'.format(PROJECT_NAME), *found)

setup(
    name=PROJECT_NAME,
    version=_version.__version__,
    description='Continuous delivery helpers for python projects',
    author='Adam Kaufman',
    author_email='kaufman.blue@gmail.com',
    url=GITHUB_ROOT,
    download_url='{}/tarball/{}'.format(GITHUB_ROOT, _version.__version__),
    license='MIT',
    packages=[PROJECT_NAME],
    package_data={PROJECT_NAME: ['snippets/*']},
    entry_points={'console_scripts': ['hatchery=hatchery.main:hatchery']},
    install_requires=[
        'funcy>=1.4',
        'docopt>=0.6.2',
        'wheel>=0.26.0',
        'ruamel.yaml>=0.11.3',
        'pypandoc>=1.1.3',
        'twine>=1.6.5',
        'microcache>=0.2',
        'workdir>=0.3.1',
        'gitpython>=1.0.2'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Testing'
    ],
    keywords='hatchery build test package upload pypi ci cd continuous delivery development'
)
