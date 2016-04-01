# -*- coding: utf-8 -*-
# cd C:\d from old\RadiaBeam\RadSoft\SRW\2dipoleInterf
# python PractWfrSetUp.py
"""Practicum on Wavefront Set-Up
"""
from __future__ import print_function  # Python 2.7 compatibility

import numpy as np
import pylab as py
import uti_plot
from srwlib import *

# Gaussian beam definition
GsnBm = SRWLGsnBm()
GsnBm.x = 0  # Transverse Coordinates of Gaussian Beam Center at Waist [m]
GsnBm.y = 0
GsnBm.z = 0.0  # Longitudinal Coordinate of Waist [m]
GsnBm.xp = 0  # Average Angles of Gaussian Beam at Waist [rad]
GsnBm.yp = 0
GsnBm.avgPhotEn = 0.5  # Photon Energy [eV]
GsnBm.pulseEn = 1.0E7  # Energy per Pulse [J] - to be corrected
GsnBm.repRate = 1  # Rep. Rate [Hz] - to be corrected
## 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
GsnBm.polar = 6
GsnBm.sigX = 2.0E-3  # Horiz. RMS size at Waist [m]
GsnBm.sigY = 2.0E-3  # Vert. RMS size at Waist [m]
GsnBm.sigT = 1E-12  # Pulse duration [fs] (not used?)
GsnBm.mx = 0  # Transverse Gauss-Hermite Mode Orders
GsnBm.my = 0

# Wavefront Definition
wfr = SRWLWfr()
NEnergy = 1  # Number of points along Energy
Nx = 300  # Number of points along X
Ny = 300  # Number of points along Y
wfr.allocate(NEnergy, Nx, Ny)  # Numbers of points vs Photon Energy (1), Horizontal and Vertical Positions (dummy)
wfr.mesh.zStart = 0.35  # Longitudinal Position [m] at which Electric Field has to be calculated, i.e. the position of the first optical element
wfr.mesh.eStart = 0.5  # Initial Photon Energy [eV]
wfr.mesh.eFin = 0.5  # Final Photon Energy [eV]
firstHorAp = 2.0E-3  # First Aperture [m]
firstVertAp = 2.0E-3  # [m]
wfr.mesh.xStart = -0.01  # Initial Horizontal Position [m]
wfr.mesh.xFin = 0.01  # Final Horizontal Position [m]
wfr.mesh.yStart = -0.01  # Initial Vertical Position [m]
wfr.mesh.yFin = 0.01  # Final Vertical Position [m]

# Precision parameters for SR calculation
meth = 2  # SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
npTraj = 1  # number of points for trajectory calculation (not needed)
relPrec = 0.01  # relative precision
zStartInteg = 0.0  # longitudinal position to start integration (effective if < zEndInteg)
zEndInteg = 0.0  # longitudinal position to finish integration (effective if > zStartInteg)
useTermin = 1  # Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
sampFactNxNyForProp = 1  # sampling factor for adjusting nx, ny (effective if > 0)
arPrecPar = [meth, relPrec, zStartInteg, zEndInteg, npTraj, useTermin, sampFactNxNyForProp]

# Calculating Initial Wavefront
srwl.CalcElecFieldGaussian(wfr, GsnBm, arPrecPar)
meshIn = deepcopy(wfr.mesh)
wfrIn = deepcopy(wfr)

# Plotting initial wavefront
arIin = array('f', [0] * wfrIn.mesh.nx * wfrIn.mesh.ny)
srwl.CalcIntFromElecField(arIin, wfrIn, 0, 0, 3, wfr.mesh.eStart, 0, 0)
plotMeshInX = [1000 * wfrIn.mesh.xStart, 1000 * wfrIn.mesh.xFin, wfrIn.mesh.nx]
plotMeshInY = [1000 * wfrIn.mesh.yStart, 1000 * wfrIn.mesh.yFin, wfrIn.mesh.ny]
uti_plot.uti_plot2d(arIin, plotMeshInX, plotMeshInY,
                    ['Horizontal Position [mm]', 'Vertical Position [mm]', 'Intensity Before Propagation [a.u.]'])

arIinY = array('f', [0] * wfrIn.mesh.ny)
srwl.CalcIntFromElecField(arIinY, wfrIn, 0, 0, 2, wfrIn.mesh.eStart, 0, 0)  # extracts intensity
uti_plot.uti_plot1d(arIinY, plotMeshInY, ['Vertical Position [mm]', 'Intensity [a.u.]',
                                          'Intensity Before Propagation\n(cut vs vertical position at x = 0)'])

# Element definition
Aperture = 0.00075  # Aperture radius, m
DriftLength = 1.0  # Drift length, m
OpElement = []
ppOpElement = []
# --------------------0----1----2----3----4----5----6----7----8----91011
OpElement.append(SRWLOptA('c', 'a', Aperture, Aperture))
ppOpElement.append([0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0, 0, 0])
OpElement.append(SRWLOptD(DriftLength))  # Drift space
ppOpElement.append([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0, 0, 0])

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
## [1, 1, 1, 1, 0, 4, 2, 4, 1, 0, 0, 0]

# Container definition 
OpElementContainer = []
OpElementContainer.append(OpElement[0])
OpElementContainer.append(OpElement[1])
OpElementContainerProp = []
OpElementContainerProp.append(ppOpElement[0])
OpElementContainerProp.append(ppOpElement[1])

opBL = SRWLOptC(OpElementContainer, OpElementContainerProp)
srwl.PropagElecField(wfr, opBL)  # Propagate Electric Field

Polar = 6
## 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
Intens = 0
## 0=Single-e I/1=Multi-e I/2=Single-e F/3=Multi-e F/4=Single-e RadPhase/5=Re single-e Efield/6=Im single-e Efield
DependArg = 3
## 0 - vs e, 1 - vs x, 2 - vs y, 3- vs x&y, 4-vs x&e, 5-vs y&e, 6-vs x&y&e
plotNum = 1000
plotMeshx = [plotNum * wfr.mesh.xStart, plotNum * wfr.mesh.xFin, wfr.mesh.nx]
plotMeshy = [plotNum * wfr.mesh.yStart, plotNum * wfr.mesh.yFin, wfr.mesh.ny]

# Plotting output wavefront
arIout = array('f', [0] * wfr.mesh.nx * wfr.mesh.ny)  # "flat" array to take 2D intensity data
arII = arIout
arIE = array('f', [0] * wfr.mesh.nx * wfr.mesh.ny)
srwl.CalcIntFromElecField(arII, wfr, Polar, Intens, DependArg, wfr.mesh.eStart, 0, 0)
uti_plot.uti_plot2d(arII, plotMeshx, plotMeshy,
                    ['Horizontal Position [mm]', 'Vertical Position [mm]', 'Intenisty, a.u.'])
# Plotting phase does not work. Why??
# srwl.CalcIntFromElecField(arIE, wfr, 5, 4, 3, wfr.mesh.eStart, 0, 0)
# uti_plot.uti_plot2d(arIE, plotMeshx, plotMeshy, ['Horizontal Position [mm]',  'Vertical Position [mm]', 'Phase, a.u.'])

arI1y = array('f', [0] * wfr.mesh.ny)
arRe = array('f', [0] * wfr.mesh.ny)
arIm = array('f', [0] * wfr.mesh.ny)
srwl.CalcIntFromElecField(arI1y, wfr, Polar, Intens, 2, wfr.mesh.eStart, 0, 0)  # extracts intensity
arI1ymax = max(arI1y)
arIinymax = max(arIinY)
for i in range(np.size(arI1y)):
    arI1y[i] = arI1y[i] / arI1ymax
for i in range(np.size(arIinY)):
    arIinY[i] = arIinY[i] / arIinymax
uti_plot.uti_plot1d(arI1y, plotMeshy, ['Vertical Position [mm]', 'Intensity [a.u.]',
                                       'Intensity After Propagation\n(cut vs vertical position at x = 0)'])

srwl.CalcIntFromElecField(arRe, wfr, Polar, 5, 2, wfr.mesh.eStart, 0, 0)
srwl.CalcIntFromElecField(arIm, wfr, Polar, 6, 2, wfr.mesh.eStart, 0, 0)

# Computing number of point per period of oscillation (i.e. within a single -pi...pi)
sIn = []
Phs = []
jj = [-1 * wfr.mesh.nx / 2]
NumJ = [0]
Delta = 0.2
j = 0
maxArre = max(arRe)
for i in range(wfr.mesh.nx):
    sIn.append(2000.0 * (i - wfr.mesh.nx / 2.0) * wfr.mesh.xFin / wfr.mesh.nx)
    Phs.append(atan2(arIm[i], arRe[i]))
    arRe[i] = arRe[i] / maxArre
    arIm[i] = arIm[i] / maxArre
    if (i > 2) & (abs(Phs[i] - Phs[i - 1]) > (3.1415 - Delta)):
        j = j + 1
        jj.append((i - 1 * wfr.mesh.nx / 2) / 1.0)
        NumJ.append(log(jj[j] - jj[j - 1] + 0.1, 10))
py.plot(sIn, arRe, '-r.')
py.plot(sIn, arIm, '-b.')
py.plot(sIn, Phs, '-g.')
uti_plot.uti_plot_show()
py.plot(jj, NumJ, '-k.')
uti_plot.uti_plot_show()

# Saving data to files
f = open('WavefrontIN.txt', 'w')
for i in range(np.size(arIinY)):
    f.write(repr(arIinY[i]) + '\n')
f.close()

f = open('WavefrontOut.txt', 'w')
for i in range(np.size(arI1y)):
    f.write(repr(arI1y[i]) + '\n')
f.close()


# Plotting a report
def Areport():
    print('Max Inten B and A propagation:', [arIinymax, arI1ymax])
    print('Num of y mesh pts B and A propagation:', [np.size(arIinY), np.size(arI1y)])
    print('Num of x mesh pts B and A propagation:', [wfrIn.mesh.nx, wfr.mesh.nx])
    print('Num of y mesh pts B and A propagation:', [wfrIn.mesh.ny, wfr.mesh.ny])
    print('Wfr xS size [mm] B and A propagation:', [wfrIn.mesh.xStart, wfr.mesh.xStart])
    print('Wfr xE size [mm] B and A propagation:', [wfrIn.mesh.xFin, wfr.mesh.xFin])
    print('Wfr yS size [mm] B and A propagation:', [wfrIn.mesh.yStart, wfr.mesh.yStart])
    print('Wfr yE size [mm] B and A propagation:', [wfrIn.mesh.yFin, wfr.mesh.yFin])
    f = open('InWavefrontOut.txt', 'w')
    f.write(repr(arIinymax) + '\t' + repr(arIinymax) + '\n')
    f.write(repr(np.size(arIinY)) + '\t' + repr(np.size(arI1y)) + '\n')
    f.write(repr(wfrIn.mesh.nx) + '\t' + repr(wfr.mesh.nx) + '\n')
    f.write(repr(wfrIn.mesh.ny) + '\t' + repr(wfr.mesh.ny) + '\n')
    f.write(repr(wfrIn.mesh.xStart) + '\t' + repr(wfr.mesh.xStart) + '\n')
    f.write(repr(wfrIn.mesh.xFin) + '\t' + repr(wfr.mesh.xFin) + '\n')
    f.write(repr(wfrIn.mesh.yStart) + '\t' + repr(wfr.mesh.yStart) + '\n')
    f.write(repr(wfrIn.mesh.yFin) + '\t' + repr(wfr.mesh.yFin) + '\n')
    f.write(repr(DriftLength) + '\t' + repr(Aperture) + '\n')
    f.close()


Areport()
uti_plot.uti_plot_show()
