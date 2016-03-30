# -*- coding: utf-8 -*-
#cd C:\d from old\RadiaBeam\RadSoft\SRW\2dipoleInterf
# python GaussBeamDiffr.py
from __future__ import print_function #Python 2.7 compatibility
from srwlib import *
from numpy import size
import pylab as py
from scipy.special import jv
from math import sin, cos
import sys
import uti_plot

print(' 1. Defining parameters for analytic calculation')
Aperture= 0.00005/1.0 #0.00005
SlitSeparation=0.0003/1.0 #0.0003
lam=2.4796e-6 #1.2398/0.5 eV
NptsOut=1000 #size(OutSRW)
Siz=0.1 #float(OutSRWdata[5])
DriftLength=1.0 #float(InSRWdata[8])

print(' 2. Computing intensity distribution as per Born & Wolf, Principles of Optics')

print(' 3. Gaussian beam definition')
GsnBm = SRWLGsnBm()
GsnBm.x = 0 #Transverse Coordinates of Gaussian Beam Center at Waist [m]
GsnBm.y = 0
GsnBm.z = 0.0 #Longitudinal Coordinate of Waist [m]
GsnBm.xp = 0 #Average Angles of Gaussian Beam at Waist [rad]
GsnBm.yp = 0
GsnBm.avgPhotEn = 0.5 #Photon Energy [eV]
GsnBm.pulseEn = 1.0E7 #Energy per Pulse [J] - to be corrected
GsnBm.repRate = 1 #Rep. Rate [Hz] - to be corrected
## 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
GsnBm.polar = 6 
GsnBm.sigX = 1.0E-3 #Horiz. RMS size at Waist [m]
GsnBm.sigY = 1.0E-3 #Vert. RMS size at Waist [m]
GsnBm.sigT = 1E-12 #Pulse duration [fs] (not used?)
GsnBm.mx = 0 #Transverse Gauss-Hermite Mode Orders
GsnBm.my = 0

print(' 4. Wavefront Definition')
wfr = SRWLWfr()
NEnergy=1 #Number of points along Energy
Nx=200 # Number of points along X
Ny=200 #Number of points along Y
wfr.allocate(NEnergy, Nx, Ny) #Numbers of points vs Photon Energy (1), Horizontal and Vertical Positions (dummy)
wfr.mesh.zStart = 1.0 #Longitudinal Position [m] at which Electric Field has to be calculated, i.e. the position of the first optical element
wfr.mesh.eStart = 0.5 #Initial Photon Energy [eV]
wfr.mesh.eFin = 0.5 #Final Photon Energy [eV]
Aperture1=2E-2
firstHorAp = Aperture1 #First Aperture [m]
firstVertAp = Aperture1 #[m] 
wfr.mesh.xStart = -Aperture1 #Initial Horizontal Position [m]
wfr.mesh.xFin = Aperture1 #Final Horizontal Position [m]
wfr.mesh.yStart = -Aperture1 #Initial Vertical Position [m]
wfr.mesh.yFin = Aperture1 #Final Vertical Position [m]

print(' 5. Precision parameters for SR calculation')
meth = 2 #SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
npTraj = 1 # number of points for trajectory calculation (not needed) 
relPrec = 0.01 #relative precision
zStartInteg = 0.0 #longitudinal position to start integration (effective if < zEndInteg)
zEndInteg = 0.0 #longitudinal position to finish integration (effective if > zStartInteg)
useTermin = 1 #Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
sampFactNxNyForProp=1 #sampling factor for adjusting nx, ny (effective if > 0)
arPrecPar = [meth, relPrec, zStartInteg, zEndInteg, npTraj, useTermin, sampFactNxNyForProp]

print(' 6. Calculating Initial Wavefront') 
srwl.CalcElecFieldGaussian(wfr, GsnBm, arPrecPar)
meshIn=deepcopy(wfr.mesh)
wfrIn=deepcopy(wfr)

print(' 7. Element definition')
OpElement=[]
ppOpElement=[]
#--------------------0----1----2----3----4----5----6----7----8----91011
## OpElement.append(SRWLOptA('c', 'a', Aperture, Aperture)) 
## ppOpElement.append([0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0, 0, 0]) 

## [0]: Auto-Resize (1) or not (0) Before propagation
## [1]: Auto-Resize (1) or not (0) After propagation
## [2]: Relative Precision for propagation with Auto-Resizing (1. is nominal)
## [3]: Allow (1) or not (0) for semi-analytical treatment of the quadratic (leading) phase terms at the propagation
## [4]: Do any Resizing on Fourier side, using FFT, (1) or not (0)
## [5]: Horizontal Range modification factor at Resizing (1. means no modification)
## [6]: Horizontal Resolution modification factor at Resizing
## [7]: Vertical Range modification factor at Resizing
## [8]: Vertical Resolution modification factor at Resizing
## [9]: Type of wavefront Shift before Resizing (not yet implemented)
## [10]: New Horizontal wavefront Center position after Shift (not yet implemented)
## [11]: New Vertical wavefront Center position after Shift (not yet implemented) 
OpElement.append(SRWLOptA("r", "a", 0.01, SlitSeparation+2*Aperture, 0.0, 0.0))
ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])
OpElement.append(SRWLOptA("r", "o", 0.01, SlitSeparation, 0.0, 0.0))
ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])
OpElement.append(SRWLOptD(DriftLength))
ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])

print(' 8. Container definition')
OpElementContainer=[]
OpElementContainer.append(OpElement[0])
OpElementContainer.append(OpElement[1])
OpElementContainer.append(OpElement[2])
OpElementContainerProp=[]
OpElementContainerProp.append(ppOpElement[0])
OpElementContainerProp.append(ppOpElement[1])
OpElementContainerProp.append(ppOpElement[2])

opBL = SRWLOptC(OpElementContainer, OpElementContainerProp)
srwl.PropagElecField(wfr, opBL) # Propagate Electric Field

print(' 9. Selecting data to plot') 
Polar=6 ## 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
Intens=0 ## 0=Single-e I/1=Multi-e I/2=Single-e F/3=Multi-e F/4=Single-e RadPhase/5=Re single-e Efield/6=Im single-e Efield
DependArg=3 ## 0 - vs e, 1 - vs x, 2 - vs y, 3- vs x&y, 4-vs x&e, 5-vs y&e, 6-vs x&y&e
plotNum=1000
plotMeshx = [plotNum*wfr.mesh.xStart, plotNum*wfr.mesh.xFin, wfr.mesh.nx]
plotMeshy = [plotNum*wfr.mesh.yStart, plotNum*wfr.mesh.yFin, wfr.mesh.ny]

print(' 10. Plotting initial and output wavefront')
arIin = array('f', [0]*wfrIn.mesh.nx*wfrIn.mesh.ny) 
srwl.CalcIntFromElecField(arIin, wfrIn, 0, 0, 3, wfr.mesh.eStart, 0, 0)
plotMeshInX = [1000*wfrIn.mesh.xStart, 1000*wfrIn.mesh.xFin, wfrIn.mesh.nx]
plotMeshInY = [1000*wfrIn.mesh.yStart, 1000*wfrIn.mesh.yFin, wfrIn.mesh.ny]
uti_plot.uti_plot2d(arIin, plotMeshInX, plotMeshInY, ['Horizontal Position [mm]', 'Vertical Position [mm]', 'Intensity Before Propagation [a.u.]'])
arIinY = array('f', [0]*wfrIn.mesh.ny)
srwl.CalcIntFromElecField(arIinY, wfrIn, 0, 0, 2, wfrIn.mesh.eStart, 0, 0) #extracts intensity
uti_plot.uti_plot1d(arIinY, plotMeshInY, ['Vertical Position [mm]', 'Intensity [a.u.]', 'Intensity Before Propagation\n(cut vs vertical position at x = 0)'])

arIout = array('f', [0]*wfr.mesh.nx*wfr.mesh.ny) #"flat" array to take 2D intensity data
arII=arIout
arIE = array('f', [0]*wfr.mesh.nx*wfr.mesh.ny)
srwl.CalcIntFromElecField(arII, wfr, Polar, Intens, DependArg, wfr.mesh.eStart, 0, 0)
uti_plot.uti_plot2d(arII, plotMeshx, plotMeshy, ['Horizontal Position [mm]',  'Vertical Position [mm]', 'Intenisty, a.u.'])
uti_plot.uti_plot_show()

print(' 11. Extracting intensity for comparison with analytic calculation')
arI1y = array('f', [0]*wfr.mesh.ny)
srwl.CalcIntFromElecField(arI1y, wfr, Polar, Intens, 2, wfr.mesh.eStart, 0, 0) #extracts intensity vs y
print('before:',[wfrIn.mesh.yStart, wfrIn.mesh.xFin, wfrIn.mesh.nx, wfrIn.mesh.ny])
print('after :',[wfr.mesh.yStart, wfr.mesh.xFin, wfr.mesh.nx, wfr.mesh.ny])

yC=[]
Inte=[]
arI1ymax=max(arI1y)
for i in range(size(arI1y)):
    arI1y[i]=arI1y[i]/arI1ymax
    thx=2.0*(i-wfr.mesh.ny/2.0)*wfr.mesh.yFin/wfr.mesh.ny
    yC.append(thx)
    xA=3.1415*Aperture*sin(thx)/lam
    xS=3.1415*SlitSeparation*sin(thx)/lam
    Inte.append((sin(xA)/(xA+1e-12)*cos(xS))**2)

print(' 12. Plotting comparison')
py.plot(yC, Inte, '-b.')
py.plot(yC, arI1y, '-r.')
py.xlabel('$x$')
py.ylabel('Normalized Intensity, a.u.')
py.title('Intensity distribution')                                
py.grid(True)
py.show()

sys.exit("done")