#/bin/bash

source activate sirepo

python srw_peaks.py  # calls chx_spectrum.py inside

python chx_intensity_prop.py


