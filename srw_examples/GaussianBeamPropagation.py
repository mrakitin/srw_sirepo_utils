from __future__ import print_function 
from srwlib import *
import numpy as np
from scipy.interpolate import UnivariateSpline
import os, sys, copy
import uti_plot
import pylab as py

print('Calculating propagation of a gaussian beam through a drift')
# 1. Defining Beam structure
GsnBm = SRWLGsnBm() #Gaussian Beam structure (just parameters)
GsnBm.x = 0 #Transverse Coordinates of Gaussian Beam Center at Waist [m]
GsnBm.y = 0
GsnBm.z = 0 #Longitudinal Coordinate of Waist [m]
GsnBm.xp = 0 #Average Angles of Gaussian Beam at Waist [rad]
GsnBm.yp = 0
GsnBm.avgPhotEn = 0.5 #5000 #Photon Energy [eV]
GsnBm.pulseEn = 0.001 #Energy per Pulse [J] - to be corrected
GsnBm.repRate = 1 #Rep. Rate [Hz] - to be corrected
GsnBm.polar = 1 #1- linear horizontal
GsnBm.sigX = 1e-03 #/2.35 #Horiz. RMS size at Waist [m]
GsnBm.sigY = 2e-03 #/2.35 #Vert. RMS size at Waist [m]
GsnBm.sigT = 10e-12 #Pulse duration [fs] (not used?)
GsnBm.mx = 0 #Transverse Gauss-Hermite Mode Orders
GsnBm.my = 0

# 2. Defining wavefront structure
wfr = SRWLWfr() #Initial Electric Field Wavefront
wfr.allocate(1, 100, 100) #Numbers of points vs Photon Energy (1), Horizontal and Vertical Positions (dummy)
wfr.mesh.zStart = 3.0 #Longitudinal Position [m] at which Electric Field has to be calculated, i.e. the position of the first optical element
wfr.mesh.eStart = GsnBm.avgPhotEn #Initial Photon Energy [eV]
wfr.mesh.eFin = GsnBm.avgPhotEn #Final Photon Energy [eV]
firstHorAp = 20.e-03 #First Aperture [m]
firstVertAp = 30.e-03 #[m] 
wfr.mesh.xStart = -0.5*firstHorAp #Initial Horizontal Position [m]
wfr.mesh.xFin = 0.5*firstHorAp #Final Horizontal Position [m]
wfr.mesh.yStart = -0.5*firstVertAp #Initial Vertical Position [m]
wfr.mesh.yFin = 0.5*firstVertAp #Final Vertical Position [m]
DriftMatr0=np.matrix([[1, wfr.mesh.zStart], [0, 1]])

# 3. Setting up propagation parameters
sampFactNxNyForProp = 5 #sampling factor for adjusting nx, ny (effective if > 0)
arPrecPar = [sampFactNxNyForProp]

# 4. Defining optics properties
f_x=3e+0 # focusing strength, m in X
f_y=4e+0 # focusing strength, m in Y
StepSize=0.3 # StepSize in meters along optical axis
InitialDist=0 # Initial drift before start sampling RMS x/y after the lens
TotalLength=6.0 # Total length after the lens
NumSteps=np.int((TotalLength-InitialDist)/StepSize) # Number of steps to sample RMS x/y after the lens

# Computing complex q parameter
def qParameter(PhotonEnergy, Waist,RadiusCurvature):
    Lam=1.24e-6*PhotonEnergy
    qp=(1.0+0j)/(np.complex(1/RadiusCurvature, -Lam/3.1415/Waist**2))
    return qp, Lam

# Computing FWHM
def FWHM(X,Y):
    spline = UnivariateSpline(X, Y, s=0)
    r1, r2 = spline.roots() # find the roots
    return r2-r1 #return the difference (full width)
    
def AnalyticEst(PhotonEnergy, WaistPozition, Waist, Dist):
    Lam=1.24e-6*PhotonEnergy
    zR=3.1415*Waist**2/Lam
    wRMSan=[]
    for l in range(np.size(Dist)):
        wRMSan.append(1*Waist*np.sqrt(1+(Lam*(Dist[l]-WaistPozition)/4/3.1415/Waist**2)**2))
    return wRMSan

# 5. Container definition    
def Container(DriftLength, f_x, f_y): 
    OpElement=[]
    ppOpElement=[]
    OpElement.append(SRWLOptL(_Fx=f_x, _Fy=f_y, _x=0, _y=0))
    OpElement.append(SRWLOptD(DriftLength))
    ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0]) # note that I use sel-adjust for Num grids
    ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])
    OpElementContainer=[]
    OpElementContainer.append(OpElement[0])
    OpElementContainer.append(OpElement[1])
    OpElementContainerProp=[]
    OpElementContainerProp.append(ppOpElement[0])
    DriftMatr=np.matrix([[1, DriftLength], [0, 1]])
    OpElementContainerProp.append(ppOpElement[1])
    LensMatrX=np.matrix([[1, 0], [-1.0/f_x, 1]])
    LensMatrY=np.matrix([[1, 0], [-1.0/f_y, 1]])
    opBL = SRWLOptC(OpElementContainer, OpElementContainerProp)
    return (opBL, LensMatrX, LensMatrY, DriftMatr)

# Computes envelope in free space /not used/
def BLMatrixMult(LensMatrX, LensMatrY, DriftMatr, DriftMatr0):    
    InitDriftLenseX=np.dot(LensMatrX,DriftMatr0)
    tRMSfunX=np.dot(DriftMatr,InitDriftLenseX)
    InitDriftLenseY=np.dot(LensMatrY,DriftMatr0)
    tRMSfunY=np.dot(DriftMatr,InitDriftLenseY)
    return (tRMSfunX, tRMSfunY)

# 5. Starting the cycle through the drift after the lens
xRMS=[]
yRMS=[]    
s=[]
WRx=[]
WRy=[]
print('z        xRMS         yRMS       mesh.nx  mesh.ny       xStart       yStart')
for j in range(NumSteps):
# Calculating Initial Wavefront and extracting Intensity:
    srwl.CalcElecFieldGaussian(wfr, GsnBm, arPrecPar)
    arI0 = array('f', [0]*wfr.mesh.nx*wfr.mesh.ny) #"flat" array to take 2D intensity data
    srwl.CalcIntFromElecField(arI0, wfr, 6, 0, 3, wfr.mesh.eStart, 0, 0) #extracts intensity
    wfrP = deepcopy(wfr)
    InitialDist=InitialDist+StepSize
    (opBL, LensMatrX, LensMatrY, DriftMatr)=Container(InitialDist, f_x, f_y)
    srwl.PropagElecField(wfrP, opBL) # Propagate E-field

# Selecting radiation properties 
    Polar=6 # 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
    Intens=0 # 0=Single-e I/1=Multi-e I/2=Single-e F/3=Multi-e F/4=Single-e RadPhase/5=Re single-e Efield/6=Im single-e Efield
    DependArg=3 # 0 - vs e, 1 - vs x, 2 - vs y, 3- vs x&y, 4-vs x&e, 5-vs y&e, 6-vs x&y&e
    plotNum=1000
    plotMeshx = [plotNum*wfrP.mesh.xStart, plotNum*wfrP.mesh.xFin, wfrP.mesh.nx]
    plotMeshy = [plotNum*wfrP.mesh.yStart, plotNum*wfrP.mesh.yFin, wfrP.mesh.ny]
    
# Extracting output wavefront
    arII=array('f', [0]*wfrP.mesh.nx*wfrP.mesh.ny) #"flat" array to take 2D intensity data
    arIE = array('f', [0]*wfrP.mesh.nx*wfrP.mesh.ny)
    srwl.CalcIntFromElecField(arII, wfrP, Polar, Intens, DependArg, wfrP.mesh.eStart, 0, 0)
    arIx = array('f', [0]*wfrP.mesh.nx)
    srwl.CalcIntFromElecField(arIx, wfrP, 6, Intens, 1, wfrP.mesh.eStart, 0, 0)
    arIy = array('f', [0]*wfrP.mesh.ny)
    srwl.CalcIntFromElecField(arIy, wfrP, 6, Intens, 2, wfrP.mesh.eStart, 0, 0)
    x=[]
    y=[]
    arIxmax=max(arIx)
    arIxh=[]
    arIymax=max(arIx)
    arIyh=[]
    for i in range(wfrP.mesh.nx):
        x.append((i-wfrP.mesh.nx/2.0)/wfrP.mesh.nx*(wfrP.mesh.xFin-wfrP.mesh.xStart))
        arIxh.append(float(arIx[i]/arIxmax-0.5))
    for i in range(wfrP.mesh.ny):
        y.append((i-wfrP.mesh.ny/2.0)/wfrP.mesh.ny*(wfrP.mesh.yFin-wfrP.mesh.yStart))
        arIyh.append(float(arIy[i]/arIymax-0.5))          
    xRMS.append(FWHM(x,arIxh))
    yRMS.append(FWHM(y,arIyh))
    s.append(InitialDist)
    (tRMSfunX, tRMSfunY)=BLMatrixMult(LensMatrX, LensMatrY, DriftMatr, DriftMatr0)
    WRx.append(tRMSfunX)
    WRy.append(tRMSfunY)
    print(InitialDist, xRMS[j], yRMS[j], wfrP.mesh.nx, wfrP.mesh.ny, wfrP.mesh.xStart, wfrP.mesh.yStart)

# 6. Analytic calculations
xRMSan=AnalyticEst(GsnBm.avgPhotEn, wfr.mesh.zStart+s[0], GsnBm.sigX, s)
(qxP, Lam)=qParameter(GsnBm.avgPhotEn, GsnBm.sigX, wfr.mesh.zStart+s[0])
qx0=np.complex(0, 3.1415/Lam*GsnBm.sigX**2)
qy0=np.complex(0, 3.1415/Lam*GsnBm.sigY**2)
Wthx=[]
Wthy=[]
for m in range(np.size(s)):
    Wx=(WRx[m][0,0]*qx0+WRx[m][0,1])/(WRx[m][1,0]*qx0+WRx[m][1,1]) #MatrixMultiply(WR,qxP)
    RMSbx=np.sqrt(1.0/np.imag(-1.0/Wx)/3.1415*Lam)*2.35
    Wthx.append(RMSbx)
    Wy=(WRy[m][0,0]*qy0+WRy[m][0,1])/(WRy[m][1,0]*qy0+WRy[m][1,1]) #MatrixMultiply(WR,qxP)
    RMSby=np.sqrt(1.0/np.imag(-1.0/Wy)/3.1415*Lam)*2.35
    Wthy.append(RMSby)
#    print(s[m],(RMSbx-xRMS[m])/xRMS[m]*100, (RMSby-yRMS[m])/yRMS[m]*100)

# 7. Plotting
py.plot(s,xRMS, '-r.', label="X envelope via SRW")
py.plot(s,Wthx, '--ro', label="X envelope via ABCD propagator") 
py.plot(s,yRMS, '-b.', label="Y envelope via SRW")
py.plot(s,Wthy, '--bo', label="Y envelope via ABCD propagator") 
py.legend()
py.xlabel('Distance along beam line, m')
py.ylabel('Horizontal and Vertical RMS beam sizes, m')
py.title('Gaussian beam envelopes through a drift after a lense')

#uti_plot.uti_plot1d(arIx, [wfrP.mesh.xStart, wfrP.mesh.xFin*0, wfrP.mesh.nx], 
#['Horizontal coordinate [mm]', 'Intensity [ph/s/.1%bw/mm^2]', 'Distribution'])
#uti_plot.uti_plot2d(arII, plotMeshx, plotMeshy, 
#['Horizontal Position [mm]',  'Vertical Position [mm]', 'Intenisty, a.u.'])
#uti_plot.uti_plot_show()

py.grid()
py.show()

sys.exit("Exit")