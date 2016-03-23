#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

from distutils import log
from distutils.command.build import build
from distutils.versionpredicate import VersionPredicate
from distutils.core import setup


class check_and_build( build ):
    
    def run(self):
        chk = True
        for req in require_python:
            chk &= self.check_python(req)
        for req in require_packages:
            chk &= self.check_package(req)
        if not chk: 
            sys.exit(1)
        build.run(self)

    def check_python(self, req):
        chk = VersionPredicate(req)
        ver = '.'.join([str(v) for v in sys.version_info[:2]])
        if not chk.satisfied_by(ver):
            log.error("Invalid python version, expected {0}".format(req))
            return False
        return True

    def check_package(self, req):
        chk = VersionPredicate(req)
        try:
            mod = __import__(chk.name)
        except:
            log.error("Missing mandatory {0} python module".format(chk.name))
            return False
        for v in [ '__version__', 'version' ]:
            ver = getattr(mod, v, None)
            break
        try:
            if ver and not chk.satisfied_by(ver):
                log.error("Invalid module version, expected {0}".format(req))
                return False
        except:
            pass
        return True

require_python = [ 'python (>=3.1)' ]
require_packages = []


setup(name = 'free_stuff',
      version     = time.strftime("%Y%m%d-dev"),
      description  = "utiliies for debuging python scripts",
      author  = "freeh4cker",
      author_email = "freeh4cker@gmail.com",
      license      = "BSD3-clause" ,
      classifiers = [
                     'Operating System :: POSIX',
                     'Programming Language :: Python :: 3.x :: Only',
                     'Topic :: informatics',
                    ] ,
      package_dir={ 'debug' : 'src/debug'},
      packages    = ['debug'],
      cmdclass= { 'build' : check_and_build ,
                 },
      )

