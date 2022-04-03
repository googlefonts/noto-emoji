#!/bin/bash

SRC_DIR=""
DST_DIR=""

SCOUR_ARGS="--strip-xml-prolog --enable-viewboxing --enable-id-stripping --enable-comment-stripping --shorten-ids --no-line-breaks --strip-xml-space"

while [ $# != 0 ]; do
  case "$1" in
    -s) SRC_DIR=${2}
        shift
        shift
        ;;
    -d) DST_DIR=${2}
        shift
        shift
        ;;
    *) echo "unrecognized arg $1"
       exit 1
       ;;
  esac
done

if [ -z "$SRC_DIR" ]; then
  echo "missing source directory"
  exit 1;
fi

if [ ! -d "$SRC_DIR" ]; then
  echo "source directory '$SRC_DIR' does not exist"
  exit 1;
fi

if [ -z "$DST_DIR" ]; then
  echo "missing destination directory"
  exit 1
fi

if [ ! -d "$DST_DIR" ]; then
  echo "creating destination directory '$DST_DIR'"
  mkdir -p "$DST_DIR"
fi

for file in "$SRC_DIR"/*.svg; do
  dst="${file##*/}"
  scour $SCOUR_ARGS -i "$file" -o "$DST_DIR/$dst"
done
  
