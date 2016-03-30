# -*- coding: utf-8 -*-
# version where we do check wiggler or undulator

# This unit will help to check SRW settings as:
# Photon energies of U/W harmonics
# Transverse sizes of the area where radiation sampling takes place; needs 
# Scaling of UR and WR radiation cone to the photon energy of interest
# Number of mech points for transverse calculations 
# Level of intensity per pixel that is minimal for SRW calculations
# Predict whether calculations are dominated by beam emittance or by radiation diffraction
# Check integration type (manual, wiggler or undulator)

#http://epaper.kek.jp/e94/PDF/EPAC1994_1241.PDF
#http://link.springer.com/article/10.1007/BF02721640
#http://www.aps.anl.gov/Science/Publications/techbulletins/content/files/APS_1422142.pdf
#http://escholarship.org/uc/item/8kz7n70d#page-46
#https://www.researchgate.net/publication/44657272_Practical_estimates_of_peak_flux_and_brilliance_of_undulator_radiation_on_even_harmonics

from __future__ import absolute_import, division, print_function, unicode_literals
from io import open
import copy
import numpy as np
#import scipy.integratefrom
import scipy.special as sp

# Constants and presets
Lam_Inf=1e12 # Wavelength 
K_woru=3 # Criterium for U vs W
sig_r_Inf=0 # sigma beam
sig_rp_Inf=1e12 # divergence beam

def IDStateType(lam_u,Bx,By):
    Ky=0.934*Bx*lam_u*100
    Kx=0.934*By*lam_u*100
    if (Kx > K_woru) or (Ky > K_woru):
        U_type='Wiggler'
    else:
        U_type='Undulator'
    if (Kx == 0) and (Ky == 0) or (Kx < 0) or (Ky < 0) or (lam_u<=0):
        U_state='NoField'
        print('No undulator field specified')
    elif (Kx>0) and (Ky==0):
        U_state='PlanarX'
    elif (Kx==0) and (Ky>0):
        U_state='PlanarY'
    else:
        U_state='Helical'
    return (Kx,Ky,U_state,U_type)

def IDPhotonEnergy(n_harm,lam_u,Bx,By,Gam,U_type,U_state):
    if (U_type=='Wiggler') and (U_state<>'NoField'):
        E_c=665.0255*(Bx**2+By**2)*(Gam*0.511E-3)**2 #eV
        Lam_c=1.2407002E-6/E_c
    elif (U_type=='Undulator') and (U_state<>'NoField'):
        Ky=0.934*Bx*lam_u*100
        Kx=0.934*By*lam_u*100
        Lam_c=lam_u/(2*n_harm)/Gam/Gam*(1+Kx**2/2+Ky**2/2) #m
        E_c=1.2407002E-6/Lam_c #eV
    else:
        E_c=0
        Lam_c=Lam_Inf
        print('No undulator field specified')
    return (E_c,Lam_c)

def UndulatorSourceSizeDivergence(lam_rn,L_id, U_type, U_state):
    #This only works for the case of a planar ID
    if (U_type=='Undulator') and (U_state<>'NoField'):
        sig_r=np.sqrt(lam_rn*L_id/2)/2/3.1415 #m
        sig_rp=np.sqrt(lam_rn/L_id/2)  #rad
    elif (U_type=='Wiggler') and (U_state<>'NoField'):
        sig_r=0
        sig_rp=Lam_Inf
    else:
        sig_r=sig_r_Inf
        sig_rp=sig_rp_Inf
        print('No undulator field specified')
    return (sig_r,sig_rp)
    
def WigglerDivergence(lam_rn,L_id, Kx, Ky, Gam, U_type, U_state):
    if (U_type=='Undulator'):
        sig_rp=np.sqrt(lam_rn/L_id/2)  #rad
        Angle={
            'NoField': [0.0, 0.0],
            'PlanarX': [sig_rp, sig_rp],
            'PlanarY': [sig_rp, sig_rp],
            'Helical': [sig_rp, sig_rp],
        }        
    elif (U_type=='Wiggler'):
        Angle={
            'NoField': [0.0, 0.0],
            'PlanarX': [Kx/Gam, 1.0/Gam],
            'PlanarY': [1.0/Gam, Ky/Gam],
            'Helical': [Kx/Gam, Ky/Gam],
        }
    return (Angle.get(U_state))
    
def ElectronBeamSizeAndDivergence(ex,ey,bx,by,Dx,Dy,Dpx,Dpy,delta):
    sx=np.sqrt(ex*bx+(Dx*delta)**2)
    sy=np.sqrt(ey*by+(Dy*delta)**2)
    spx=np.sqrt(ex/bx+(Dpx*delta)**2)
    spy=np.sqrt(ey/by+(Dpy*delta)**2)
    return(sx,sy,spx,spy)
    
def UndulatorAngleCoordinateOscillation(Kx, Ky, Gam, lam_u):
    xpmax=Ky/Gam
    xmax=Ky/2/3.14159265359*lam_u/Gam # wrong formulae
    zslip=lam_u/4*Ky**2/Gam**2
    return (xpmax, xmax, zslip)

def integrand(o, x):
    return kv(o, x)

def SpectralFlux(N_u,Gam,EEc,I_b,Kx):
    #This only works for the case of a planar ID
    modBes=sp.integrate.quad(lambda x: scipy.special.kv(5.0/3.0, x),EEc,np.Inf)
    I_s=2.458E10*2*N_u*I_b*Gam*0.511*EEc*modBes[0] #I[phot/(sec mrad 0.1% BW)]
    return (I_s)

def SpectralCenBrightness(N_u,Gam,I_b):
    #This only works for the case of a planar ID
    I_s=1.325E10*2*N_u*I_b*1E-3*Gam*0.511E0*Gam*0.511E0*1.45 #I[phot/(sec mrad2 0.1% BW)]
    return (I_s)

def RadiatedPowerPlanarWiggler(lam_u,Bx,By,N_u,Gam,I_b):
    #This only works for the case of a planar ID
    L_id=N_u*lam_u
    P_W=1265.382/2*L_id*I_b*(Gam*0.511E-3)**2*(Bx**2+By**2) #Watts
    return (P_W, L_id)

def CentralPowerDensityPlanarWiggler(Bx,By,N_u,Gam,I_b):
    #This only works for the case of a planar ID and zero emittance
    P_Wdc=10.85*N_u*I_b*(Gam*0.511E-3)**2*np.sqrt(Bx**2+By**2) #W/mrad2
    return (P_Wdc)
    
def PolarizationState(Bx,By,phi):
    P1=(Bx**2-By**2)/(Bx**2+By**2)
    P2=2*Bx*By*np.cos(phi)/(Bx**2+By**2)
    P3=2*Bx*By*np.sin(phi)/(Bx**2+By**2)
    return (P1, P2, P3)

#def TuningCurveSpectralBrightness():

#def TuningCurveSpectralFlux():

def computeJJ(n, K):
    x=(n*K**2)/(4+2*K**2)
    JJ=sp.jv(int((n-1)/2), x)-sp.jv(int((n+1)/2), x)
    return JJ

def compute_all(params):
    """Perform multiparticle analytical calc.

    Args:
        params (dict): input

    Returns:
        dict: copy of `params` and results
    """
    res = _merge_params(params)
    v = IDWaveLengthPhotonEnergy(
        params['period_len'],
        #TODO(robnagler) Why is this not res['Bx']?
        0,
        params['vertical_magnetic_field'],
        params['gamma'],
    )
    res.update(zip(('Kx', 'Ky', 'lam_rn', 'e_phn'), v))
    v = RadiatedPowerPlanarWiggler(
        params['period_len'],
        #TODO(robnagler) Why is this not res['Bx']?
        params['vertical_magnetic_field'],
        params['num_periods'],
        params['gamma'],
        params['avg_current'],
    )
    res.update(zip(('P_W', 'L_id'), v))
    res['E_c'] = CriticalEnergyWiggler(
        params['vertical_magnetic_field'],
        params['horizontal_magnetic_field'],
        params['gamma'],
    )
    res['P_Wdc'] = CentralPowerDensityPlanarWiggler(
        params['vertical_magnetic_field'],
        params['num_periods'],
        params['gamma'],
        params['avg_current'],
    )
    v = UndulatorSourceSizeDivergence(
        res['lam_rn'],
        res['L_id'],
    )
    res.update(zip(('RadSpotSize', 'RadSpotDivergence'), v))
    res['SpectralFluxValue'] = SpectralFlux(
        params['num_periods'],
        params['gamma'],
        1,
        params['avg_current'],
        res['Kx'],
    )
    res['RadBrightness'] = SpectralCenBrightness(
        params['num_periods'],
        params['gamma'],
        params['avg_current'],
    )
    res['lam_rn_3'] = res['lam_rn'] / 3.0
    res['lam_rn_5'] = res['lam_rn'] / 5.0
    res['e_phn_3'] = res['e_phn'] / 3.0
    res['e_phn_5'] = res['e_phn'] / 5.0
    return res


def _merge_params(params):
    """Convert params to args to :func:`compute_all`

    Args:
        params (dict): RT values in canonical form

    Returns:
        dict: Merged params
    """
    res = copy.deepcopy(self.params['undulator'])
    if res['orientation'] == 'VERTICAL':
        res['horizontal_magnetic_field'] = 0
        res['vertical_magnetic_field'] = res['magnetic_field']
    else:
        res['horizontal_magnetic_field'] = res['magnetic_field']
        res['vertical_magnetic_field'] = 0
    res.update(self.params['beam'])
    return res
JJ=computeJJ(1, 2)
#print(JJ)

'''
# Testing Analytic Calculations
Period_U=0.02
Bx_U=1
By_U=1
Gamma=3000/0.511
N_u=49
L_id=Period_U*N_u
n_harm=5

ex=1e-9
ey=1e-11
bx=3
by=1.3
Dx=0.1
Dy=0.0
DpX=0.0
DpY=0.0
delta=1e-3

(Kx,Ky,U_state,U_type)=IDStateType(Period_U,Bx_U,By_U)
print("ID Kx, Ky and state/type     (Kx,Ky,U_state,U_type): %1.3e %1.3e %s %s" % (Kx,Ky,U_state,U_type))
(E_r,Lam_r)=IDPhotonEnergy(n_harm,Period_U,Bx_U,By_U,Gamma,U_type,U_state)
print("ID photon energy and wavelength         (E_c,Lam_c): %1.3e %1.3e " % (E_r,Lam_r))
print("Wiggler divergence x and y             (al_x, al_y): %1.3e %1.3e " % (WigglerDivergence(Lam_r,L_id, Kx, Ky, Gamma, U_type, U_state)[0], WigglerDivergence(Lam_r,L_id, Kx, Ky, Gamma, U_type, U_state)[1]))
print("Undulator source size and divergence (sig_r,sig_rp): %1.3e %1.3e " % UndulatorSourceSizeDivergence(Lam_r,L_id, U_type, U_state))
print("Coordinate OScillation Amplitude (xpmax,xmax,zslip): %1.3e %1.3e %1.3e" % UndulatorAngleCoordinateOscillation(Kx, Ky, Gamma, Period_U))
(sx,sy,spx,spy)=ElectronBeamSizeAndDivergence(ex,ey,bx,by,Dx,Dy,DpX,DpY,delta)
print("Beam sizes and divergences          (sx,sy,spx,spy): %1.3e %1.3e %1.3e %1.3e" % (sx,sy,spx,spy))
'''