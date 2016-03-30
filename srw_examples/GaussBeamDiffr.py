# -*- coding: utf-8 -*-
#cd C:\d from old\RadiaBeam\RadSoft\SRW\2dipoleInterf
# python GaussBeamDiffr.py
from numpy import size
import pylab as py
from scipy.special import jv
from math import sin

print('1. Getting data from files saved by PractWfrSetUp1.py')
def ReadingFiles():
	f=open('WavefrontIN.txt',"r",1000)
	InSRW=[]
	for line in f.readlines():
		words = line.split()
		InSRW.append(words)
	f.close()

	f=open('WavefrontOut.txt',"r",1000)
	OutSRW=[]
	for line in f.readlines():
		words = line.split()
		OutSRW.append(words)
	f.close()
	
	f = open('InWavefrontOut.txt', 'r', 1000)
	InSRWdata=[]
	OutSRWdata=[]
	for line in f.readlines():
		words = line.split()
		InSRWdata.append(words[0])
		OutSRWdata.append(words[1])
	f.close()		
	return(InSRW, OutSRW, InSRWdata, OutSRWdata)

(InSRW, OutSRW, InSRWdata, OutSRWdata)=ReadingFiles()

print('2. Defining parameters for analytic calculation')
Aperture=float(OutSRWdata[8])
lam=2.4796e-6 #1.2398/0.5 eV
NptsIn=size(InSRW)
NptsOut=size(OutSRW)
Siz=float(OutSRWdata[5])
DriftLength=float(InSRWdata[8])
#print(Siz)
#print(NptsOut)
#print(DriftLength)

print('3. Computing intensity distribution as per Born & Wolf, Principles of Optics')
th=[]
sIn=[]
sOut=[]
Inte=[]
for i in range(NptsOut):
	thx=2.0*(i-NptsOut/2.0+0.5)*Siz/NptsOut/DriftLength
	th.append(thx)
	sOut.append(thx*DriftLength*1000)
#        print('angles:',[thx, thx*DriftLength*1000])
	x=3.1415*Aperture*sin(thx)/lam
	Inte.append((2*jv(1, x)/x)**2)

for i in range(NptsIn):
	sIn.append(2000.0*(i-NptsIn/2.0)*float(InSRWdata[5])/NptsIn)

print('4. Plotting')
py.plot(sOut, Inte, '-b.')
py.plot(sIn, InSRW, '--g.')
py.plot(sOut, OutSRW, '-r.')
py.xlabel('$x$')
py.ylabel('Normalized Intensity, a.u.')
py.title('Intensity distribution')                                
py.grid(True)
#py.savefig('besseln0to6.eps', format = 'eps')                                      
py.show()
print('done')