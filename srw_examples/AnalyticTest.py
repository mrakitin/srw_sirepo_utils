#C:\d from old\RadiaBeam\RadSoft\DCP\ProgressBar 
from __future__ import print_function #Python 2.7 compatibility
from srwlib import *
import os, time
import uti_plot
from AnalyticCalcA import IDStateType, IDPhotonEnergy, UndulatorSourceSizeDivergence,UndulatorAngleCoordinateOscillation,WigglerDivergence,ElectronBeamSizeAndDivergence
import numpy as np
from ProblemDefinitions import EBeam, Wavefront,ArPrec,stk

print('-> Testing Analytic predictions')

#***********Undulator
numPer = 50 #Number of ID Periods (without counting for terminations
undPer = 0.02 #Period Length [m]
Bx = 0.5 #Peak Horizontal field [T]
By = 1.0 #Peak Vertical field [T]
phBx = 0 #Initial Phase of the Horizontal field component
phBy = 0 #Initial Phase of the Vertical field component
sBx = -1 #Symmetry of the Horizontal field component vs Longitudinal position
sBy = 1 #Symmetry of the Vertical field component vs Longitudinal position
xcID = 0 #Transverse Coordinates of Undulator Center [m]
ycID = 0
zcID = 0 #Longitudinal Coordinate of Undulator Center [m]
sigEperE = 0.00089 #relative RMS energy spread
sigX = 33.33e-06 #horizontal RMS size of e-beam [m]
sigXp = 16.5e-06 #horizontal RMS angular divergence [rad]
sigY = 2.912e-06 #vertical RMS size of e-beam [m]
sigYp = 2.7472e-06 #vertical RMS angular divergence [rad]

#und = SRWLMagFldU([SRWLMagFldH(1, 'v', By, phBy, sBy, 1)], undPer, numPer) #SRWLMagFldH(1, 'h', Bx, phBx, sBx, 1)]
und = SRWLMagFldU([SRWLMagFldH(1, 'v', By, phBy, sBy, 1), SRWLMagFldH(1, 'h', Bx, phBx, sBx, 1)], undPer, numPer) 
magFldCnt = SRWLMagFldC([und], array('d', [xcID]), array('d', [ycID]), array('d', [zcID])) #Container of all Field Elements

#***********Electron Beam
elecBeam=EBeam(0.5,0,0,-0.5*undPer*(numPer + 4),0,0,3./0.51099890221e-03,sigX**2,0,sigXp**2,sigY**2,0,sigYp**2,sigEperE**2)

#***********Precision
meth = 1 #SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
relPrec = 0.01 #relative precision
zStartInteg = 0 #longitudinal position to start integration (effective if < zEndInteg)
zEndInteg = 0 #longitudinal position to finish integration (effective if > zStartInteg)
npTraj = 10000 #Number of points for trajectory calculation 
useTermin = 0 #Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
sampFactNxNyForProp = 0 #sampling factor for adjusting nx, ny (effective if > 0)
arPrecPar = [meth, relPrec, zStartInteg, zEndInteg, npTraj, useTermin, sampFactNxNyForProp]

#***********Wavefront
Nx=100
Ny=100
Ne=10000
AperI=0.001
AperXY=0.01
wfr1=Wavefront(Ne,1,1,20.,100,10000,AperI,elecBeam)
wfr2=Wavefront(1,Nx,Ny,20.,100,10000,AperXY,elecBeam)

Polar=6 ## 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
Intens=0 ## 0=Single-e I/1=Multi-e I/2=Single-e F/3=Multi-e F/4=Single-e RadPhase/5=Re single-e Efield/6=Im single-e Efield
DependArg=3 ## 0 - vs e, 1 - vs x, 2 - vs y, 3- vs x&y, 4-vs x&e, 5-vs y&e, 6-vs x&y&e

#***********Precision Parameters
arPrecF=ArPrec(1,9,1.5,1.5,1)
arPrecP=ArPrec(1.5,1,0,0,npTraj) #???

#***********UR Stokes Parameters (mesh) for Spectral Flux
stkF=stk(wfr1.mesh.ne,1,1,wfr2.mesh.zStart,wfr2.mesh.eStart,wfr2.mesh.eFin,AperI)
stkP=stk(1,Nx,Ny,wfr2.mesh.zStart,wfr2.mesh.eStart,wfr2.mesh.eFin,AperXY)

#--------------------------------------Testing Analytic Calcs
n_harm=1
(Kx,Ky,U_state,U_type)=IDStateType(undPer,Bx,By)
print("ID Kx, Ky and state/type     (Kx,Ky,U_state,U_type): %1.2e %1.2e %s %s" % (Kx,Ky,U_state,U_type))
(E_r,Lam_r)=IDPhotonEnergy(n_harm,undPer,Bx,By, elecBeam.partStatMom1.gamma,U_type,U_state)
print("ID photon energy and wavelength         (E_c,Lam_c): %1.2e %1.2e " % (E_r,n_harm*Lam_r))
print("Wiggler divergence x and y             (al_x, al_y): %1.2e %1.2e " % (WigglerDivergence(Lam_r,undPer*numPer, Kx, Ky, elecBeam.partStatMom1.gamma, U_type, U_state)[0], WigglerDivergence(Lam_r,undPer*numPer, Kx, Ky, elecBeam.partStatMom1.gamma, U_type, U_state)[1]))
print("Undulator source size and divergence (sig_r,sig_rp): %1.2e %1.2e " % UndulatorSourceSizeDivergence(Lam_r,undPer*numPer, U_type, U_state))
print("Coordinate Oscillation Amplitude (xpmax,xmax,zslip): %1.2e %1.2e %1.3e" % UndulatorAngleCoordinateOscillation(Ky, Kx, elecBeam.partStatMom1.gamma, undPer))
#(sx,sy,spx,spy)=ElectronBeamSizeAndDivergence(ex,ey,bx,by,Dx,Dy,DpX,DpY,delta)
#print("Beam sizes and divergences          (sx,sy,spx,spy): %1.3e %1.3e %1.3e %1.3e" % (sx,sy,spx,spy))

print('1) Check size of observation area')
if (U_type=='Undulator') and (U_state<>'NoField'):
    (sig_r,sig_rp)=UndulatorSourceSizeDivergence(n_harm*Lam_r,numPer*undPer, U_type, U_state)
elif (U_type=='Wiggler') and (U_state<>'NoField'):
    (sig_r,sig_rp)=WigglerDivergence(n_harm*Lam_r,undPer*numPer, Kx, Ky, elecBeam.partStatMom1.gamma, U_type, U_state)
# Convolution with electron beam and calculation of beam size
Size1apX=np.sqrt(sig_rp**2+sigXp**2)*wfr1.mesh.zStart*10
Size1apY=np.sqrt(sig_rp**2+sigYp**2)*wfr1.mesh.zStart*10
print(" Estimated area of intesity and Defined Aperture: %1.2e %1.2e %1.2e" % (Size1apX, Size1apY, AperXY))

print('2) Check type of calculation')
Method={
        0: 'manual', 
        1: 'auto-undulator',
        2: 'auto-wiggler'
        }
print(" Type of ID / type of calculation: %s %s " % (U_type, Method.get(meth)))

print('3) Check choice of wavelength range')
for i_h in range(1, arPrecF[1], 2):
    (E_r,Lam_r)=IDPhotonEnergy(i_h,undPer,Bx,By, elecBeam.partStatMom1.gamma,U_type,U_state)
    print("Harmonic: %d %1.3e eV" % (i_h, E_r))
print("Desired photon energy for SRW calculations: %1.3e" % (wfr2.mesh.eFin))

print('4) Redefining calculation parameters for initial time estimate')

RedF=10 # reduction factor for Ne, Nx, Ny
RedA=1 # reduction factor for accuracies
FactorScan=1.2
ticStokes=[]
for i in range(4):
    RedA=(RedA*FactorScan)
    stktF=stk(wfr1.mesh.ne/RedF,1,1,wfr2.mesh.zStart,wfr2.mesh.eStart,wfr2.mesh.eFin,AperI)
    tic = time.clock()
    arPrecF[2] = arPrecF[2]/RedA #longitudinal integration precision parameter
    arPrecF[3] = arPrecF[3]/RedA #azimuthal integration precision parameter
    srwl.CalcStokesUR(stktF, elecBeam, und, arPrecF)
    toc = time.clock()
    ticStokes.append(toc - tic)
    print("* Time elapsed spectral calculations 1/Redc: %1.1f %1.3e" % (RedA, (toc - tic)))

RedF=10 # reduction factor for Ne, Nx, Ny
RedA=3 # reduction factor for accuracies
FactorScan=1.1
ticPowerDen=[]
for i in range(4):
    RedF=np.round(RedF*FactorScan)
    stktP=stk(1,Nx/RedF,Ny/RedF,wfr2.mesh.zStart,wfr2.mesh.eStart,wfr2.mesh.eFin,AperXY)
    tic = time.clock()
    arPrecP[4]=arPrecP[4]/RedA
    srwl.CalcPowDenSR(stktP, elecBeam, 0, magFldCnt, arPrecP)
    toc = time.clock()
    ticPowerDen.append(toc - tic)
    print("# Time elapsed heat load calculations 1/Redc: %1.1f %1.3e" % (RedF, (toc - tic)))

#Power Spectrum and Density
#print(stktF.mesh.ne)
uti_plot.uti_plot1d(stktF.arS, [stktF.mesh.eStart, stktF.mesh.eFin, stktF.mesh.ne], ['Photon Energy [eV]', 'Flux [ph/s/.1%bw]', 'Flux through Finite Aperture'])
plotMeshX = [1000*stktP.mesh.xStart, 1000*stktP.mesh.xFin, stktP.mesh.nx]
plotMeshY = [1000*stktP.mesh.yStart, 1000*stktP.mesh.yFin, stktP.mesh.ny]
uti_plot.uti_plot2d(stktP.arS, plotMeshX, plotMeshY, ['Horizontal Position [mm]', 'Vertical Position [mm]', 'Power Density'])
uti_plot.uti_plot_show()

#-----------------------------------------------------------

print('5) Main calculation segment')
tic = time.clock()
arPrecF[2] = 1.0 #arPrecF[2]*RedF #longitudinal integration precision parameter
arPrecF[3] = 1.0 #arPrecF[2]*RedF #azimuthal integration precision parameter
srwl.CalcStokesUR(stkF, elecBeam, und, arPrecF)
toc = time.clock()
print("Time elapsed spectral calculations: %1.3e" % (toc - tic))

tic = time.clock()
arPrecP[4]=arPrecP[4]*RedF
srwl.CalcPowDenSR(stkP, elecBeam, 0, magFldCnt, arPrecP)
toc = time.clock()
print("Time elapsed heat load calculations: %1.3e" % (toc - tic))

print('6.) Plotting results \n', end='')
tic = time.clock()
#Power Spectrum and Density
uti_plot.uti_plot1d(stkF.arS, [stkF.mesh.eStart, stkF.mesh.eFin, stkF.mesh.ne], ['Photon Energy [eV]', 'Flux [ph/s/.1%bw]', 'Flux through Finite Aperture'])
plotMeshX = [1000*stkP.mesh.xStart, 1000*stkP.mesh.xFin, stkP.mesh.nx]
plotMeshY = [1000*stkP.mesh.yStart, 1000*stkP.mesh.yFin, stkP.mesh.ny]
uti_plot.uti_plot2d(stkP.arS, plotMeshX, plotMeshY, ['Horizontal Position [mm]', 'Vertical Position [mm]', 'Power Density'])

uti_plot.uti_plot_show() 
toc = time.clock()
print("5) Time elapsed plotting: %1.3e" % (toc - tic))
print('done')

