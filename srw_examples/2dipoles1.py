# -*- coding: utf-8 -*-
"""Simulation of SR from 2 dipole edges
"""
from __future__ import absolute_import, division, print_function

from pykern.pkdebug import pkdc, pkdp
from pykern import pkarray

import srwlib
from array import array
import uti_plot

print('1. Defining Particle for Trajectory Calculations...')
# Particle
part = srwlib.SRWLParticle()
part.x = 0.0 #beam.partStatMom1.x
part.y = 0.0 #beam.partStatMom1.y
part.xp = 0.0 #beam.partStatMom1.xp
part.yp = 0.0 #beam.partStatMom1.yp
part.gamma = 0.064/0.51099890221e-03 #Relative Energy beam.partStatMom1.gamma #
part.z = -0.0  #zcID #- 0.5*magFldCnt.MagFld[0].rz
part.relE0 = 1 #Electron Rest Mass
part.nq = -1 #Electron Charge

print('2. Defining Beam for Synchrotron Radiation Calculations...')
# Electron Beam
elecBeam = srwlib.SRWLPartBeam()
elecBeam.Iavg = 0.1 #Average Current [A]
elecBeam.partStatMom1.x = part.x #Initial Transverse Coordinates (initial Longitudinal Coordinate will be defined later on) [m]
elecBeam.partStatMom1.y = part.y
elecBeam.partStatMom1.z = part.z #Initial Longitudinal Coordinate (set before the ID)
elecBeam.partStatMom1.xp = part.xp #Initial Relative Transverse Velocities
elecBeam.partStatMom1.yp = part.yp
elecBeam.partStatMom1.gamma = part.gamma #Relative Energy
sigEperE = 0.1 #relative RMS energy spread
sigX = (1.5e-06/(64/0.511)*0.1)**(1/2) #horizontal RMS size of e-beam [m]
sigXp = (1.5e-06/(64/0.511)/0.1) **(1/2) #horizontal RMS angular divergence [rad]
sigY = sigX #vertical RMS size of e-beam [m]
sigYp = sigXp #vertical RMS angular divergence [rad]
elecBeam.arStatMom2[0] = sigX*sigX #<(x-<x>)^2> 
elecBeam.arStatMom2[1] = 0 #<(x-<x>)(x'-<x'>)>
elecBeam.arStatMom2[2] = sigXp*sigXp #<(x'-<x'>)^2> 
elecBeam.arStatMom2[3] = sigY*sigY #<(y-<y>)^2>
elecBeam.arStatMom2[4] = 0 #<(y-<y>)(y'-<y'>)>
elecBeam.arStatMom2[5] = sigYp*sigYp #<(y'-<y'>)^2>
elecBeam.arStatMom2[10] = sigEperE*sigEperE #<(E-<E>)^2>/<E>^2

print('3. Defining Magnetic Elements...')
# Elements
L_bend=0.05
L_drift=0.02
L_total=0.2 #2*L_bend+L_drift
bend1=srwlib.SRWLMagFldM(_G=-0.85, _m=1, _n_or_s='n', _Leff=L_bend, _Ledge=0.01)
bend2=srwlib.SRWLMagFldM(_G=0.85, _m=1, _n_or_s='n', _Leff=L_bend, _Ledge=0.01)
drift1 = srwlib.SRWLMagFldM(_G=0.0,_m=1, _n_or_s='n', _Leff=L_drift) #Drift

print('4. Collecting Elements into Container...')
# Container
arZero = array('d', [0]*3)
arZc = array('d', [-L_bend/2-L_drift/2, 0, L_bend/2+L_drift/2])
magFldCnt = srwlib.SRWLMagFldC() #Container
magFldCnt.allocate(3) #Magnetic Field consists of 1 part
magFldCnt = srwlib.SRWLMagFldC([bend1, drift1, bend2], arZero, arZero, arZc)

# Container for a single dipole
#arZero = array('d', [0]*1)
#arZc = array('d', [-L_bend])
#magFldCnt = srwlib.SRWLMagFldC([bend1], arZero, arZero, arZc)

print('5. Making Allocation for Trajectory Waveform ...')
#Definitions and allocation for the Trajectory waveform
arPrecPar = [1] 
npTraj = 10001 # number of trajectory points along longitudinal axis
partTraj = srwlib.SRWLPrtTrj()
partTraj.partInitCond = part
partTraj.allocate(npTraj, True)
partTraj.ctStart = -L_total/2
partTraj.ctEnd = L_total/2 

print('6. Calculating Trajectory ...')
# Calculating Trajectory
partTraj = srwlib.srwl.CalcPartTraj(partTraj, magFldCnt, arPrecPar)
ctMesh = [partTraj.ctStart, partTraj.ctEnd, partTraj.np]

print('7. Plotting Trajectory ...')
uti_plot.uti_plot1d(partTraj.arX, ctMesh, ['ct [m]', 'Horizontal Position [m]'])
uti_plot.uti_plot1d(partTraj.arY, ctMesh, ['ct [m]', 'Vertical Position [m]'])
uti_plot.uti_plot1d(partTraj.arXp, ctMesh, ['ct [m]', 'Horizontal angle [rad]'])
uti_plot.uti_plot_show()

print('8. Switching to Synchrotron Radiation Calculations ...')

el1=0 # This FLAG defines type of calculation: 
#       Either filament beam calculation or for heat load calc

if el1==0:
    wfr2 = srwlib.SRWLWfr() #For intensity distribution at fixed photon energy
else:
    wfr2 = srwlib.SRWLStokes() 

print('9. Defining SR Wavefront ...')
# Defining SR Wavefront
wfr2.mesh.ne= 1             
wfr2.mesh.nx=401
wfr2.mesh.ny=401
wfr2.allocate(wfr2.mesh.ne, wfr2.mesh.nx, wfr2.mesh.ny) #Numbers of points vs Photon Energy, Horizontal and Vertical Positions
wfr2.mesh.zStart = 0.3 #Longitudinal Position [m] at which SR has to be calculated
wfr2.mesh.eStart = 2.1 #Initial Photon Energy [eV]
wfr2.mesh.eFin = 2.1 #Final Photon Energy [eV]
wfr2.mesh.xStart = -0.01 #Initial Horizontal Position [m]
wfr2.mesh.xFin = 0.01 #Final Horizontal Position [m]
wfr2.mesh.yStart = -0.01 #Initial Vertical Position [m]
wfr2.mesh.yFin = 0.01 #Final Vertical Position [m]
wfr2.partBeam = elecBeam

#This defines mesh for "thick" beam calculation
meshRes = srwlib.SRWLRadMesh(wfr2.mesh.eStart, wfr2.mesh.eFin, wfr2.mesh.ne, wfr2.mesh.xStart, 
wfr2.mesh.xFin, wfr2.mesh.nx, wfr2.mesh.yStart, wfr2.mesh.yFin, wfr2.mesh.ny, wfr2.mesh.zStart) #to ensure correct final mesh if _opt_bl==None

print('10. Defining Precision of SR Calculations ...')
# Defining Precision of SR Calculations ...
meth = 2 #SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
relPrec = 0.01 #relative precision
zStartInteg = partTraj.ctStart #0 #longitudinal position to start integration (effective if < zEndInteg)
zEndInteg =  partTraj.ctEnd #0 #longitudinal position to finish integration (effective if > zStartInteg)
npTraj = 2000 #Number of points for trajectory calculation 
useTermin = 0 #Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
sampFactNxNyForProp = 0 #sampling factor for adjusting nx, ny (effective if > 0)
arPrecPar = [meth, relPrec, zStartInteg, zEndInteg, npTraj, useTermin, sampFactNxNyForProp]

if el1==0:
    print('11. Calculating SR Wavefront ...')            
    srwlib.srwl.CalcElecFieldSR(wfr2, elecBeam, magFldCnt, arPrecPar)
else:
# This computes heat load     
#   print('11. Calculating SR Heat Load ...')  
#   srwlib.srwl.CalcPowDenSR(wfr2, elecBeam, 0, magFldCnt, arPrecPar)
#This computes "thick" electron beam
    print('11. Calculating SR Wavefront vua multi-electron propagation...')     
    srwlib.srwl_wfr_emit_prop_multi_e(elecBeam,magFldCnt, meshRes, meth, 
    relPrec, 1, _n_part_avg_proc=1, _n_save_per=100, 
    _file_path=None, _sr_samp_fact=-1, _opt_bl=None, _pres_ang=0, _char=0, 
    _x0=0, _y0=0, _e_ph_integ=0, _rand_meth=1)

print('12. Extracting Intensity from calculated Electric Field ...')
## Note that when I select Intens=0 SRW computes a single electron Rad x-y distribution
## Note that when I select Intens=1 SRW computes the thick-beam Rad x-y distribution
if el1==0:
    print('13. Plotting results ...')
    Intens=1
#   2-D distribution
    arI2 = array('f', [0]*wfr2.mesh.nx*wfr2.mesh.ny) #"flat" array to take 2D intensity data
    srwlib.srwl.CalcIntFromElecField(arI2, wfr2, 6, Intens, 3, wfr2.mesh.eStart, 0, 0)
    uti_plot.uti_plot2d(arI2, [1000*wfr2.mesh.xStart, 1000*wfr2.mesh.xFin, wfr2.mesh.nx], 
    [1000*wfr2.mesh.yStart, 1000*wfr2.mesh.yFin, wfr2.mesh.ny], 
    ['Horizontal Position [mm]', 'Vertical Position [mm]', 
    'Intensity at ' + str(wfr2.mesh.eStart) + ' eV'])
                
#   1-D distribution
    arI1 = array('f', [0]*wfr2.mesh.nx)
    srwlib.srwl.CalcIntFromElecField(arI1, wfr2, 6, Intens, 1, wfr2.mesh.eStart, 0, 0)
    uti_plot.uti_plot1d(arI1, [wfr2.mesh.xStart, wfr2.mesh.xFin*0, wfr2.mesh.nx], 
    ['Horizontal coordinate [mm]', 'Intensity [ph/s/.1%bw/mm^2]', 'Distribution'])
else:
    print('13. Plotting results ...')
#   1-D distribution
#   plotMeshX = [1000*wfr2.mesh.xStart, 1000*wfr2.mesh.xFin*0, wfr2.mesh.nx]
#   powDenVsX = array('f', [0]*wfr2.mesh.nx)
#   for i in range(wfr2.mesh.nx): powDenVsX[i] = wfr2.arS[wfr2.mesh.nx*int(wfr2.mesh.ny*0.5) + i]
#   uti_plot.uti_plot1d(powDenVsX, plotMeshX, ['Horizontal Position [mm]', 'Power Density [W/mm^2]', 'Power Density\n(horizontal cut at y = 0)'])
		
    arI1 = array('f', [0]*wfr2.mesh.nx)
    srwlib.srwl.CalcIntFromElecField(arI1, wfr2, 6, 0, 3, wfr2.mesh.eStart, 0, 0)
    uti_plot.uti_plot1d(arI1, [wfr2.mesh.xStart, wfr2.mesh.xFin*0, wfr2.mesh.nx], 
    ['Photon Energy [eV]', 'Intensity [ph/s/.1%bw/mm^2]', 'Distribution'])
		
#   2-D distribution
#   arI2 = array('f', [0]*wfr2.mesh.nx*wfr2.mesh.ny) #"flat" array to take 2D intensity data
#   srwlib.srwl.CalcIntFromElecField(arI2, meshRes, 6, 0, 3, wfr2.mesh.eStart, 0, 0)
#   uti_plot.uti_plot2d(arI2, [1000*wfr2.mesh.xStart, 1000*wfr2.mesh.xFin, wfr2.mesh.nx], 
#   [1000*wfr2.mesh.yStart, 1000*wfr2.mesh.yFin, wfr2.mesh.ny], 
#   ['Horizontal Position [mm]', 'Vertical Position [mm]', 
#   'Intensity at ' + str(wfr2.mesh.eStart) + ' eV'])

print('14. Saving results ...')
f = open('Trajectory.txt', 'w')
ctStep = 0
if partTraj.np > 0:
    ctStep = (partTraj.ctEnd - partTraj.ctStart)/(partTraj.np - 1)
ct = partTraj.ctStart
for i in range(partTraj.np):
    resStr = str(ct) + '\t' + repr(partTraj.arX[i]) + '\t' + repr(partTraj.arXp[i]) + '\t' + repr(partTraj.arY[i]) + '\t' + repr(partTraj.arYp[i]) + '\t' + repr(partTraj.arZ[i]) + '\t' + repr(partTraj.arZp[i])
    if(hasattr(partTraj, 'arBx')):
        resStr += '\t' + repr(partTraj.arBx[i])
    if(hasattr(partTraj, 'arBy')):
        resStr += '\t' + repr(partTraj.arBy[i])
    if(hasattr(partTraj, 'arBz')):
        resStr += '\t' + repr(partTraj.arBz[i])
    f.write(resStr + '\n')        
    ct += ctStep
f.close()

f = open('1DprofileSR.txt', 'w')
xStep = 0
if wfr2.mesh.nx > 0:
    xStep = (wfr2.mesh.xFin - wfr2.mesh.xStart)/(wfr2.mesh.nx - 1)
x = wfr2.mesh.xStart
for i in range(wfr2.mesh.nx ):
    resStr = str(x) + '\t' + repr(arI1[i]) + '\t' 
    f.write(resStr + '\n')        
    x += xStep
f.close()

uti_plot.uti_plot_show()
print('done')

def EmittanceOptimizer(sigX,sigY,sigXp,sigYp): 
    elecBeam.arStatMom2[0] = sigX*sigX 
    elecBeam.arStatMom2[2] = sigXp*sigXp  
    elecBeam.arStatMom2[3] = sigY*sigY 
    elecBeam.arStatMom2[5] = sigYp*sigYp 
    srwlib.srwl.CalcElecFieldSR(wfr2, elecBeam, magFldCnt, arPrecPar)
    arI1 = array('f', [0]*wfr2.mesh.nx)
    srwlib.srwl.CalcIntFromElecField(arI1, wfr2, 6, 1, 1, wfr2.mesh.eStart, 0, 0)
    return (arI1) 

def read_data(SFileName="1DprofileSR.txt", TFileName="Trajectory.txt"):
#   Reading SPECTRUM
#    SFileName="Spectrum.txt"
    f=open(SFileName,"r",1000)
    e_p=[]
    I_rad=[]
    for line in f.readlines():
        words = line.split()
        e_p.append(words[0])
        I_rad.append(words[1])
    f.close()

#   Reading TRAJECTORY
#    TFileName="Trajectory.txt"
    f=open(TFileName,"r",10000)
    z_dist=[]
    x_trajectory=[]
    for line in f.readlines():
        words = line.split()
        z_dist.append(words[0])
        x_trajectory.append(words[1])
    f.close()

    uti_plot.uti_plot1d(x_trajectory, [1, 10000, 10000], 
    ['ct [um]', 'Horizontal Position [m]'])
    uti_plot.uti_plot_show()

read_data()