#!/bin/bash

# Script to compile fftw-2.1.5.
# Maksim Rakitin
# 2016-05-02

#---> Dirs and files:
root_dir=$PWD
gcc_dir=$root_dir/cpp/gcc
py_dir=$root_dir/py
ext_dir=$root_dir/ext_lib
fftw_dir=$ext_dir/fftw-2.1.5
fftw_file=$ext_dir/fftw-2.1.5.tar.gz
log_fftw=$root_dir/log_fftw.log

if [ -z "$1" ]; then
    #---> Compile FFTW2:
    echo "    Compiling FFTW2..."

    cd $ext_dir
    if [ ! -f "$fftw_file" ]; then
        # wget http://www.fftw.org/fftw-2.1.5.tar.gz
        wget https://raw.githubusercontent.com/ochubar/SRW/master/ext_lib/fftw-2.1.5.tar.gz > /dev/null 2>&1
    fi

    if [ -d "$fftw_dir" ]; then
        rm -rf $fftw_dir
    fi

    tar -zxf fftw-2.1.5.tar.gz
    cd $fftw_dir

    echo "        Configuring FFTW2..."
    ./configure --enable-float --with-pic --prefix=$fftw_dir/tmp >> $log_fftw 2>&1

    echo "        Updating CFLAGS..."
    sed 's/^CFLAGS = /CFLAGS = -fPIC /' -i $fftw_dir/Makefile

    echo "        Making FFTW2..."
    make >> $log_fftw 2>&1 && \
    make install >> $log_fftw 2>&1 && \
    cp fftw/.libs/libfftw.a $ext_dir

    echo "    Compilation of FFTW2 finished."
    echo ""
elif [ "$1" == "clean" ]; then
    #---> Clean:
    echo "    Cleaning..."
    rm -rf $fftw_dir
    rm -rf $ext_dir/libfftw.a $gcc_dir/libsrw.a $gcc_dir/srwlpy.so $py_dir/build/
    echo ""
fi
