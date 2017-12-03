#!/usr/bin/env bash

source activate sirepo

for f in res_intensity_*.dat; do
    DISPLAY= python $SRWPATH/SRWLIB_ExampleViewDataFile.py -j -f $f
    mv -v uti_plot-1.png ${f}.png
    rm -fv uti_plot-0.png
done
