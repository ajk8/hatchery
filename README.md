# hatchery

[![Latest Version](https://img.shields.io/pypi/v/hatchery.svg)](https://pypi.python.org/pypi/hatchery)
[![Build Status](https://travis-ci.org/ajk8/hatchery.svg?branch=master)](https://travis-ci.org/ajk8/hatchery)
[![Coverage Status](https://coveralls.io/repos/github/ajk8/hatchery/badge.svg?branch=master)](https://coveralls.io/github/ajk8/hatchery?branch=master)

A helper for continuous delivery of python packages

## What is the problem, exactly?

Python's packaging and distribution scheme is really designed for manual intervention, most notably
as regards versions. In your typical project, the version is hardcoded *somewhere* in the source
tree, and the project history will be littered with messages like "bumped version to x.y." Isn't
this what tagging is for? Also, why should a work in progress be given a version number in the
first place? It seems backwards. It also is solvable.

Aside from that major issue, there are a number of minor annoyances that arise when handling python
projects in github. Chief among these is the problem of README files. Github clearly prefers
`README.md` files, and the markdown syntax widely available and very natural to use. Pypi, on the
other hand, requires the use of `README.rst` files (or at least that format) in order to display on
the project's main site. I find this more difficult to work with and, regardless, one should be
able to use one's preferred README syntax. Converting from one to the other is doable, so it should
also be simple.

Finally, when doing any kind of modification of source files on the fly (a build process) it is
important that the package tree be untouched. This is largely due to the fact that an automated
tagging process (critical to CD) falls down when the working copy is dirty. As such, automated
management of a working directory which can be safely ignored in VCS is an integrated part of
`hatchery`.

## Core features

* Isolation of all source manipulations to a working directory (`.hatchery.work`)
* On-the-fly version management using the popular `_version.py` specification method
  * Logic to make sure that only pypi-accepted
  (see [PEP-386](https://www.python.org/dev/peps/pep-0386/)) versions are used
* Optional on-the-fly readme conversion from `md` to `rst`
* Notion of "tasks" which must be run in a particular order
* Dictate as little project structure as possible (see below)

## Project prerequisites

As of the time of this writing, there are a few prerequisites that a project must meet in order
to integrate with `hatchery`:

* The project should consist of a single root package which contains all of the python logic. That
package can be as large or as small as is needed, containing as many subpackages as you like, but
there must only be one.
* There are some code requirements in `setup.py` and `<packagename>._version.py`. Run
`hatchery check` for more information. And don't worry, if these prereqs aren't met, `hatchery`
will tell you about it instead of doing something wonky.
* In order to make use of some of the features (running tests, registering and uploading releases
of your project), you will have to maintain a configuration file.  More information below.

### Top-level project

`hatchery` automatically infers the name of top-level package during operation based on the layout
of the file system, and it expects there to be exactly one. In order for this to work properly,
your project needs to look like this:

```
# the project directory is the path you cloned to
project_directory/

    .git/

    .hatchery.yml

    ...

    # the package name can be whatever you want, so long as it's not "tests"
    package_name/

        __init__.py

        ...

    # the "tests" directory is where your tests are stored, and will be ignored when determining
    # the top-level package -- any other directories which contain an __init__.py and are not
    # children of package_name will cause the inference to fail
    tests/

        __init__.py

        ...
```

So, if you want your tests in a python package, make sure it's called `tests`. If there are two
python packages which are not named `tests`, `hatchery` will throw an error. This is in service
of a unified package version. In order for `setup.py` (and `setuptools`) to infer the project
version from the package safely, there should only be one package from which to infer.

## Installation

```
$ pip install hatchery
```
As always, it is strongly recommended that you use this inside of a virtual environment.

## Configuration

As previously mentioned, in order to take full advantage of what `hatchery` has to offer, there is
a little configuration that is required...and I do mean a little.  There are a number of parameters
available, but most of them can just be left to their default values:

Parameter | Default value | Usage
--------- | ------------- | -----
`auto_push_tag` | `False` | Automatically run the tag-and-push logic after a successful upload operation
`create_wheel` | `True` | Create a wheel along with the source distribution during the packaging step
`git_remote_name` | `'origin'` | The name of the remote to push to when pushing a git tag
`pypi_repository` | `None` | String parameter describing which pypi index server to upload packages to. It actually refers to an alias which must be defined in your [pypirc file](https://docs.python.org/3.5/distutils/packageindex.html#the-pypirc-file)
`readme_to_rst` | `True` | Convert a README.md file to README.rst on the fly if the former is detected and the latter is not. This feature requires `pandoc` (OS-level dependency) ... so if you do not want to depend on `pandoc`, set to `False` and this feature won't be used.
`test_command` | `None` | A list of arbitrary shell commands that should be run during the test task. If any of them fails, the test will be considered a failure.

These parameters should be defined in [yaml format](https://en.wikipedia.org/wiki/YAML) in the
file `.hatchery.yml` in the root of your project.  If you want to make any of them global across
all your projects, you can also choose to define them in `~/.hatchery/hatchery.yml`; just remember
that the project-level file's values will always win!

A minimal `.hatchery.yml` might look like this:

```yaml
---

pypi_repository: pypi

test_command:
    - tox
```

See `.hatchery.yml` in this repository for a contextual example.

Aside: there are lots of different opinions about how best to test one's code. There are many
frameworks, and many ways to execute them. Allowing users to have complete control over this was
a key design decision. You want to use `tox`? Go for it! Prefer using `py.test` directly? Fine by
me. Think `pylint` is important? Throw it on there! The point is, choose what testing feedback is
important to you, and `hatchery` will faithfully execute it for you.

### Private pypi repositories

New feature alert! If you specify a full address of a pypi server as a value for `pypi_repository`,
`hatchery` will attempt to upload to that server, bypassing the pypirc file entirely. **This will
only work for anonymous-upload servers, and cannot be used for interaction with public servers
such as pypi.python.org!** Example:

```yaml
pypi_repository: https://pypi.mydomain.com
```

## Examples

Make sure you have all of the prerequisites in place
```
$ hatchery check
```

Run all tests defined in configuration
```
$ hatchery clean test
```

Register your project with the pypi repository defined in configuration
```
$ hatchery register
```

Create packages (with markdown -> rst conversion)
```
$ hatchery package --release-version=1.2.3
```

Upload your packages to the pypi repository defined in configuration
```
$ hatchery upload
```

String everything together in one go!
```
$ hatchery clean register test package upload --release-version=1.2.3
```

Find out what other great features you're missing out on
```
$ hatchery help
```

## Postscript

I wrote this utility because it helps me to work in the way in which I am most productive. It
will not be perfect for everyone...not yet. If you think there's something missing that would
help you find your happy path, please open up a feature request. Better yet, implement it and
throw up a pull request. Feedback is welcome!
