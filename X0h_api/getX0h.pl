#!/usr/bin/perl -W
#--------------------------------------------------------------
# This example PERL script:
# - calls the X0h program from http://x-server.gmca.aps.anl.gov/
# - gets the scattering factors chi_0r and chi_0i
# - saves them into a file as a function of energy
#
# The script can use either the LWP PERL module or wget (external program).
# In the later case it can run on Microsoft Windows under Cygwin
# (http://www.cygwin.com).
#
#     		Author: Sergey Stepanov
#
# Version-1:    2005/12/31
# Version-1.1:  2006/11/08
#--------------------------------------------------------------
  use strict;
  use LWP::Simple;	# World-Wide Web library for Perl (libwww-perl)

#--------------Input parameters---------------------------
### Output file:
  my $file = 'X0h_example.dat';

### Energy range and the number of energy points
  my $E1 = 10;		# start energy
  my $E2 = 12;		# end energy
  my $n  = 3;		# number of pts (please stay within a few dozen!)
### Paramters can also be passed
### as command line arguments:
# my $E1 = $ARGV[0];	# start energy
# my $E2 = $ARGV[1];	# end energy
# my $n  = $ARGV[2];	# number of pts (please stay within a few dozen!)

### Energy step:
  my $dE = 0;
  if ($n > 1) {$dE = ($E2-$E1)/($n-1);}

  my $url = 'http://x-server.gmca.aps.anl.gov/cgi/X0h_form.exe';
###--------------Parameters of X0h CGI interface--------------
  my $xway = 2;		# 1 - wavelength, 2 - energy, 3 - line type
  my $wave = 0;        	# works with xway=2 or xway=3
# my $line = "Cu-Ka1";	# works with xway=3 only
  my $line = '';	# works with xway=3 only

### Target:
  my $coway = 0;	# 0 - crystal, 1 - other material, 2 - chemicalformula
### Crystal
  my $code = 'Germanium'; # works with coway=0 only
### Other material:
  my $amor = '';	# works with coway=1 only
### Chemical formula:
  my $chem = '';	# works with coway=2 only
### and density (g/cm3):
  my $rho = '';		# works with coway=2 only

### Miller indices:
  my $i1 = 0;
  my $i2 = 0;
  my $i3 = 0;

### Database Options for dispersion corrections df1, df2:
### -1 - Automatically choose DB for f',f"
###  0 - Use X0h data (5-25 keV or 0.5-2.5 A) -- recommended for Bragg diffraction.
###  2 - Use Henke data (0.01-30 keV or 0.4-1200 A) -- recommended for soft x-rays.
###  4 - Use Brennan-Cowan data (0.03-700 keV or 0.02-400 A)
### 10 - Compare results for all of the above sources.
  my $df1df2 = -1;

### Output options:
  my $modeout = 1;	# 0 - html out, 1 - quasy-text out with keywords
  my $detail  = 0;	# 0 - don't print coords, 1 = print coords
###-----------------------------------------------------------

### Open output file for writing:
  open (DAT,'>',$file) || die "Cannot open ${file}\n";	# overwrite DAT file
  select DAT; $|=1;					# set unbuffered output

### Print data header:
  print DAT "#Energy,      xr0,        xi0\n";

  for (my $i=0; $i<$n; $i++) { 			# Energy loop

     $wave = $E1 + $dE * $i;

     my $address=$url
                .'?xway='.$xway
                .'&wave='.$wave
                .'&line='.$line
                .'&coway='.$coway
                .'&code='.$code
                .'&amor='.$amor
                .'&chem='.$chem
                .'&rho='.$rho
                .'&i1='.$i1
                .'&i2='.$i2
                .'&i3='.$i3
                .'&df1df2='.$df1df2
                .'&modeout='.$modeout
                .'&detail='.$detail;

### Request X0h data from the server:
     my $buffer = get($address);
     my @content = split /\n/, $buffer;		# split page into lines
### Another way to fetch data using lynx:
#    my @content = `lynx -dump $address`;

     my $ncon = $#content + 1; 			# number of lines on page

     print DAT '   '.$wave;
     for (my $j=0; $j<$ncon; $j++) {		# loop over page lines
        my $x = $content[$j];
        chop $x;				# strip LF/CR
        if ( $x =~ m/xr0=/ ) {			# if contains "xr0="
      	   $x =~ s/^.*xr0=//g;			# erase everything before the data
           print DAT ',  '.$x;
        }
        if ( $x =~ m/xi0=/ ) {			# if contains "xi0="
      	   $x =~ s/^.*xi0=//g;			# erase everything before the data
           print DAT ',  '.$x;
        }
     }
     print DAT "\n";
  }
