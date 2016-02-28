# hatchery

A helper for continuous delivery of python packages

## What is the problem, exactly?

Python's packaging and distribution scheme is really designed for manual intervention, most notably as regards versions.  In your typical project, the version is hardcoded *somewhere* in the source tree, and the project history will be littered with messages like "bumped version to x.y."  Isn't this what tagging is for?  Also, why should a work in progress be given a version number in the first place?  It seems backwards.  It also is solvable.

Aside from that major issue, there are a number of minor annoyances that arise when handling python projects in github.  Chief among these is the problem of README files.  Github clearly prefers `README.md` files, and the markdown syntax widely available and very natural to use.  Pypi, on the other hand, requires the use of `README.rst` files (or at least that format) in order to display on the project's main site.  I find this more difficult to work with and, regardless, one should be able to use one's preferred README syntax.  Converting from one to the other is doable, so it should also be simple.

Finally, when doing any kind of modification of source files on the fly (a build process) it is important that the package tree be untouched.  This is largely due to the fact that an automated tagging process (critical to CD) falls down when the working copy is dirty.  As such, automated management of a working directory which can be safely ignored in VCS is an integrated part of `hatchery`.

## Core features

* Isolation of all source manipulations to a working directory (`.hatchery.work`)
* On-the-fly version management using the popular `_version.py` specification method
** Logic to make sure that only accepted (PEP)
* Optional on-the-fly readme conversion from `md` to `rst`
* Notion of "tasks" which must be run in a particular order
* Dictate as little project structure as possible (see below)

## Project prerequisites

As of the time of this writing, there are a few prerequisites that a project must meet in order to integrate with `hatchery`:

* The project should consist of a single root package which contains all of the python logic.  That package can be as large or as small as is needed, containing as many subpackages as you like, but there must only be one.
* There are some code requirements in `setup.py` and `<packagename>._version.py`.  Run `hatchery check` for more information.  And don't worry, if these prereqs aren't met, `hatchery` will tell you about it instead of doing something wonky.
* In order to make use of some of the features (running tests, registering and uploading releases of your project), you will have to maintain a configuration file.  More information below.

## Installation

```
$ pip install hatchery
```
As always, it is strongly recommended that you use this inside of a virtual environment.

## Configuration

As previously mentioned, in order to take full advantage of what `hatchery` has to offer, there is a little configuration that is required...and I do mean a little.  As of now, there are only 2 parameters that will do anything:

Parameter | Usage
--------- | -----
create_wheel | Create a wheel along with the source distribution during the packaging step.  Defaults to True.
pypi_repository | String parameter describing which pypi index server to upload packages to.  It actually refers to an alias which must be defined in your [pypirc file](https://docs.python.org/3.5/distutils/packageindex.html#the-pypirc-file)
readme_to_rst | Convert a README.md file to README.rst on the fly if the former is detected and the latter is not.  Defaults to True.
test_command | A list of arbitrary shell commands that should be run during the test task.  If any of them fails, the test will be considered a failure.

These parameters should be defined in [yaml format](https://en.wikipedia.org/wiki/YAML) in the file `.hatchery.yml` in the root of your project.  If you want to make any of them global across all your projects, you can also choose to define them in `~/.hatchery/hatchery.yml`; just remember that the project-level file's values will always win!

See `.hatchery.yml` in this repository for a contextual example.

Aside: there are lots of different opinions about how best to test one's code.  There are many frameworks, and many ways to execute them.  Allowing users to have complete control over this was a key design decision.  You want to use `tox`?  Go for it!  Prefer using `py.test` directly?  Fine by me.  Think `pylint` is important?  Throw it on there!  The point is, choose what testing feedback is important to you, and `hatchery` will execute it for you.

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
$ hatchery register --release-version=1.2.3
```

Create packages (with markdown -> rst conversion)
```
$ hatchery package --release-version=1.2.3 --convert-readme-to-rst
```

Upload your packages to the pypi repository defined in configuration
```
$ hatchery upload
```

String everything together in one go!
```
$ hatchery clean register test package upload --release-version=1.2.3 --convert-readme-to-rst
```

Find out what other great features you're missing out on
```
$ hatchery help
```

## Postscript

I wrote this utility because it helps me to work in the way in which I am most productive.  It will not be perfect for everyone...not yet.  If you think there's something missing that would help you find your happy path, please open up a feature request.  Better yet, implement it and throw up a pull request.  Feedback is welcome!
