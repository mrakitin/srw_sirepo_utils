#!/bin/bash

# The script corrects the padding in the names of the intensity files to allow better sorting.
# E.g.:
#   mv -v res_intensity_energy_7788.887.dat  res_intensity_energy_07788.887.dat

pattern='res_intensity_energy_'

for i in $(ls ${pattern}????.???.dat*); do
    rest=$(echo $i | cut -d_ -f4)
    mv -v $i  ${pattern}0${rest}
done


