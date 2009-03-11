#!/bin/sh

find pgcs -name "*.py" | xargs grep -Fni todo | sed -r "s,[[:space:]]*#,,"

exec python2.6 -t -3 -m pgcs.server localhost:8080 test.conf
