#!/bin/env/python

import os
from subprocess import call

if __name__ == '__main__':
    # Generate a report from the coverage output - either via coveralls.io
    # or locally, depending on the execution environment
    if 'TRAVIS' in os.environ:
        rc = call('coveralls')
        raise SystemExit(rc)
    else:
        # Generate a printed report that skips completely covered files, and a
        # HTML report for detailed viewing in a browser
        rc = call(['coverage', 'report', '--skip-covered'])
        if rc:
            raise SystemExit(rc)
        
        rc = call(['coverage', 'html'])
        raise SystemExit(rc)
