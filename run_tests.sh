#!/bin/bash
set -e
docker build -f Dockerfile.test -t sigilgateapp-test .
docker run --rm sigilgateapp-test "$@"
