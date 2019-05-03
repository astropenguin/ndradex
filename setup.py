# from standard library
from distutils.command.build import build
from subprocess import run as sprun
from subprocess import PIPE

# from dependent packages
from setuptools import setup


# custom build
class Build(build):
    def run(self):
        cmd = ['make', 'build', 'LOGFILE=/dev/null']
        cp = sprun(cmd, stdout=PIPE, stderr=PIPE,
                   cwd='ndradex/bin', check=True)
        build.run(self)


# main function
if __name__ == '__main__':
    setup(cmdclass={'build': Build})
