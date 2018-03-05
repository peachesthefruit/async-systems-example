#!/bin/bash

gcc -o measure measure.c

REPEATS=5
MAX_LINKS=200

for file in './multi_crawler.py -c 2' './multi_crawler.py -c 4' './async_crawler.py'; do
  TIME=0
  MEM=0
  for i in `seq 1 $REPEATS`; do
    OUTPUT=`./measure $file -m $MAX_LINKS 2>&1 >/dev/null`
    t=`echo $OUTPUT | awk '{print $1}'`
    m=`echo $OUTPUT | awk '{print $3}'`
    TIME=`echo $TIME + $t | bc`
    MEM=`echo $MEM + $m | bc`
  done
  echo $file: `echo $TIME / $REPEATS | bc -l` sec, `echo $MEM / $REPEATS | bc -l` MB
done
