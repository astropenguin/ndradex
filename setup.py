# from standard library
from distutils.command.build import build
from subprocess import run as sprun
from subprocess import PIPE

# from dependent packages
from setuptools import setup

# module constants
RADEX_BUILD = ['make', 'build', 'LOGFILE=/dev/null', 'MAXITER=999999']

# custom build
class Build(build):
    def run(self):
        cp = sprun(RADEX_BUILD, stdout=PIPE, stderr=PIPE,
                   cwd='ndradex/bin', check=True)
        build.run(self)


# main function
if __name__ == '__main__':
    setup(cmdclass={'build': Build})
