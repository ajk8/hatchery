from setuptools import setup
from imp import find_module, load_module

PROJECT_NAME = 'hatchery'
GITHUB_USER = 'ajk8'
GITHUB_ROOT = 'https://github.com/{}/{}'.format(GITHUB_USER, PROJECT_NAME)

found = find_module('_version', [PROJECT_NAME])
_version = load_module('_version', *found)

setup(
    name=PROJECT_NAME,
    version=_version.__version__,
    description='Continuous delivery helpers for python projects',
    author='Adam Kaufman',
    author_email='kaufman.blue@gmail.com',
    url='https://github.com/ajk8/' + PROJECT_NAME,
    download_url='{}/tarball/{}'.format(GITHUB_ROOT, _version.__version__),
    license='MIT',
    packages=[PROJECT_NAME],
    package_data={PROJECT_NAME: ['snippets/*']},
    entry_points={'console_scripts': ['hatchery=hatchery.main:hatchery']},
    install_requires=[
        'funcy>=1.4',
        'docopt>=0.6.2',
        'wheel>=0.26.0',
        'pyyaml>=3.11',
        'pypandoc>=1.1.3',
        'twine>=1.6.5',
        'microcache>=0.2',
        'workdir>=0.3'
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
