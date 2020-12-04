#!/bin/bash

for f in third_party/waved-flags/svg/*.svg; do
  log=/tmp/$(basename $f).picosvg.log
  picosvg $f 2>&1 > $log || echo "ERROR, see $log"
done