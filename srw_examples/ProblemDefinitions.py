from srwlib import *

def EBeam(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14):
	elecBeam = SRWLPartBeam()
	elecBeam.Iavg = a1 #Average Current [A]
	elecBeam.partStatMom1.x = a2 #Initial Transverse Coordinates (initial Longitudinal Coordinate will be defined later on) [m]
	elecBeam.partStatMom1.y = a3
	elecBeam.partStatMom1.z = a4 #Initial Longitudinal Coordinate (set before the ID)
	elecBeam.partStatMom1.xp = a5 #Initial Relative Transverse Velocities
	elecBeam.partStatMom1.yp = a6
	elecBeam.partStatMom1.gamma = a7 #Relative Energy
	elecBeam.arStatMom2[0] = a8 #<(x-<x>)^2> 
	elecBeam.arStatMom2[1] = a9 #<(x-<x>)(x'-<x'>)>
	elecBeam.arStatMom2[2] = a10 #<(x'-<x'>)^2> 
	elecBeam.arStatMom2[3] = a11 #<(y-<y>)^2>
	elecBeam.arStatMom2[4] = a12 #<(y-<y>)(y'-<y'>)>
	elecBeam.arStatMom2[5] = a13 #<(y'-<y'>)^2>
	elecBeam.arStatMom2[10] = a14 #<(E-<E>)^2>/<E>^2
	return (elecBeam)

def Wavefront(Ne,Nx,Ny,zStart,eStart,eFin,AperI,elecBeam):
	wfr1 = SRWLWfr() #For spectrum vs photon energy
	wfr1.mesh.ne=Nx
	wfr1.allocate(Ne, Nx, Ny) #Numbers of points vs Photon Energy, Horizontal and Vertical Positions
	wfr1.mesh.zStart = zStart #Longitudinal Position [m] at which SR has to be calculated
	wfr1.mesh.eStart = eStart #Initial Photon Energy [eV]
	wfr1.mesh.eFin = eFin #Final Photon Energy [eV]
	wfr1.mesh.xStart = -1*AperI #Initial Horizontal Position [m]
	wfr1.mesh.xFin = AperI #Final Horizontal Position [m]
	wfr1.mesh.yStart = -1*AperI #Initial Vertical Position [m]
	wfr1.mesh.yFin = AperI #Final Vertical Position [m]
	wfr1.partBeam = elecBeam
	return (wfr1)

def ArPrec(a1,a2,a3,a4,a5):
	arPrecF = [0]*5 #for spectral flux vs photon energy
	arPrecF[0] = a1 #initial UR harmonic to take into account
	arPrecF[1] = a2 #final UR harmonic to take into account
	arPrecF[2] = a3 #longitudinal integration precision parameter
	arPrecF[3] = a4 #azimuthal integration precision parameter
	arPrecF[4] = a5 #calculate flux (1) or flux per unit surface (2)
	return (arPrecF)

def stk(a1,a2,a3,a4,a5,a6,AperI):
	stkF = SRWLStokes() #for spectral flux vs photon energy
	stkF.mesh.ne=a1
	stkF.allocate(a1, a2, a3) #numbers of points vs photon energy, horizontal and vertical positions
	stkF.mesh.zStart = a4  #longitudinal position [m] at which UR has to be calculated
	stkF.mesh.eStart = a5 #initial photon energy [eV]
	stkF.mesh.eFin = a6  #final photon energy [eV]
	stkF.mesh.xStart = -AperI #initial horizontal position [m]
	stkF.mesh.xFin = AperI #final horizontal position [m]
	stkF.mesh.yStart = -AperI #initial vertical position [m]
	stkF.mesh.yFin = AperI #final vertical position [m]
	return (stkF)