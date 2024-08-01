#!/bin/bash
for f in $FILES
do
 echo "$f"
 mv $f "$f.temp";envsubst < "$f.temp" | tee $f >/dev/null;rm -rf "$f.temp"
done