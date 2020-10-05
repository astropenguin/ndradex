# standard library
from distutils.command.build import build
from subprocess import run as sprun
from subprocess import PIPE


# dependencies
from setuptools import setup


# constants
RADEX_BUILD = [
    "make",
    "build",
    "LOGFILE=/dev/null",
    "MAXITER=999999",
]


# custom build class
class Build(build):
    def run(self):
        sprun(
            RADEX_BUILD,
            stdout=PIPE,
            stderr=PIPE,
            cwd="ndradex/bin",
            check=True,
        )
        build.run(self)


# main script
if __name__ == "__main__":
    setup(cmdclass=dict(build=Build))
