from __future__ import print_function

import uti_plot
from matplotlib import pyplot as plt
from srwlib import *
from uti_math import matr_prod

print('SRWLIB Python Example # 15:')
print('Calculating propagation of a gaussian beam through a drift and comparison with the analytical calculation.')


def AnalyticEst(PhotonEnergy, WaistPozition, Waist, Dist):
    """Perform analytical estimation"""
    Lam = 1.24e-6 * PhotonEnergy
    zR = 3.1415 * Waist ** 2 / Lam
    wRMSan = []
    for l in range(len(Dist)):
        wRMSan.append(1 * Waist * sqrt(1 + (Lam * (Dist[l] - WaistPozition) / 4 / 3.1415 / Waist ** 2) ** 2))
    return wRMSan


def BLMatrixMult(LensMatrX, LensMatrY, DriftMatr, DriftMatr0):
    """Computes envelope in free space /not used/"""
    InitDriftLenseX = matr_prod(LensMatrX, DriftMatr0)
    tRMSfunX = matr_prod(DriftMatr, InitDriftLenseX)
    InitDriftLenseY = matr_prod(LensMatrY, DriftMatr0)
    tRMSfunY = matr_prod(DriftMatr, InitDriftLenseY)
    return (tRMSfunX, tRMSfunY)


def Container(DriftLength, f_x, f_y):
    """Container definition"""
    OpElement = []
    ppOpElement = []
    OpElement.append(SRWLOptL(_Fx=f_x, _Fy=f_y, _x=0, _y=0))
    OpElement.append(SRWLOptD(DriftLength))
    ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])  # note that I use sel-adjust for Num grids
    ppOpElement.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])
    OpElementContainer = []
    OpElementContainer.append(OpElement[0])
    OpElementContainer.append(OpElement[1])
    OpElementContainerProp = []
    OpElementContainerProp.append(ppOpElement[0])
    DriftMatr = [[1, DriftLength], [0, 1]]
    OpElementContainerProp.append(ppOpElement[1])
    LensMatrX = [[1, 0], [-1.0 / f_x, 1]]
    LensMatrY = [[1, 0], [-1.0 / f_y, 1]]
    opBL = SRWLOptC(OpElementContainer, OpElementContainerProp)
    return (opBL, LensMatrX, LensMatrY, DriftMatr)


def FWHM(X, Y):
    """The function searches x-values (roots) where y=0 based on linear interpolation, and calculates FWHM"""

    def _isPositive(num):
        return True if num > 0 else False

    positive = _isPositive(Y[0])
    list_of_roots = []
    for i in range(len(Y)):
        current_positive = _isPositive(Y[i])
        if current_positive != positive:
            list_of_roots.append(X[i - 1] + (X[i] - X[i - 1]) / (abs(Y[i]) + abs(Y[i - 1])) * abs(Y[i - 1]))
            positive = not positive
    if len(list_of_roots) == 2:
        return list_of_roots[1] - list_of_roots[0]
    else:
        raise Exception('Number of roots is more than 2!')


def FWHM_scipy(X, Y):
    """Computing FWHM (Full width at half maximum)"""
    try:
        from scipy.interpolate import UnivariateSpline
        spline = UnivariateSpline(X, Y, s=0)
        r1, r2 = spline.roots()  # find the roots
        return r2 - r1  # return the difference (full width)
    except ImportError:
        return FWHM(X, Y)


def qParameter(PhotonEnergy, Waist, RadiusCurvature):
    """Computing complex q parameter"""
    Lam = 1.24e-6 * PhotonEnergy
    qp = (1.0 + 0j) / complex(1 / RadiusCurvature, -Lam / 3.1415 / Waist ** 2)
    return qp, Lam


if __name__ == '__main__':
    # 1. Defining Beam structure
    GsnBm = SRWLGsnBm()  # Gaussian Beam structure (just parameters)
    GsnBm.x = 0  # Transverse Coordinates of Gaussian Beam Center at Waist [m]
    GsnBm.y = 0
    GsnBm.z = 0  # Longitudinal Coordinate of Waist [m]
    GsnBm.xp = 0  # Average Angles of Gaussian Beam at Waist [rad]
    GsnBm.yp = 0
    GsnBm.avgPhotEn = 0.5  # 5000 #Photon Energy [eV]
    GsnBm.pulseEn = 0.001  # Energy per Pulse [J] - to be corrected
    GsnBm.repRate = 1  # Rep. Rate [Hz] - to be corrected
    GsnBm.polar = 1  # 1- linear horizontal
    GsnBm.sigX = 1e-03  # /2.35 #Horiz. RMS size at Waist [m]
    GsnBm.sigY = 2e-03  # /2.35 #Vert. RMS size at Waist [m]
    GsnBm.sigT = 10e-12  # Pulse duration [fs] (not used?)
    GsnBm.mx = 0  # Transverse Gauss-Hermite Mode Orders
    GsnBm.my = 0

    # 2. Defining wavefront structure
    wfr = SRWLWfr()  # Initial Electric Field Wavefront
    wfr.allocate(1, 100, 100)  # Numbers of points vs Photon Energy (1), Horizontal and Vertical Positions (dummy)
    wfr.mesh.zStart = 3.0  # Longitudinal Position [m] at which Electric Field has to be calculated, i.e. the position of the first optical element
    wfr.mesh.eStart = GsnBm.avgPhotEn  # Initial Photon Energy [eV]
    wfr.mesh.eFin = GsnBm.avgPhotEn  # Final Photon Energy [eV]
    firstHorAp = 20.e-03  # First Aperture [m]
    firstVertAp = 30.e-03  # [m]
    wfr.mesh.xStart = -0.5 * firstHorAp  # Initial Horizontal Position [m]
    wfr.mesh.xFin = 0.5 * firstHorAp  # Final Horizontal Position [m]
    wfr.mesh.yStart = -0.5 * firstVertAp  # Initial Vertical Position [m]
    wfr.mesh.yFin = 0.5 * firstVertAp  # Final Vertical Position [m]
    DriftMatr0 = [[1, wfr.mesh.zStart], [0, 1]]

    # 3. Setting up propagation parameters
    sampFactNxNyForProp = 5  # sampling factor for adjusting nx, ny (effective if > 0)
    arPrecPar = [sampFactNxNyForProp]

    # 4. Defining optics properties
    f_x = 3e+0  # focusing strength, m in X
    f_y = 4e+0  # focusing strength, m in Y
    StepSize = 0.3  # StepSize in meters along optical axis
    InitialDist = 0  # Initial drift before start sampling RMS x/y after the lens
    TotalLength = 6.0  # Total length after the lens
    NumSteps = int((TotalLength - InitialDist) / StepSize)  # Number of steps to sample RMS x/y after the lens

    # 5. Starting the cycle through the drift after the lens
    xRMS = []
    yRMS = []
    s = []
    WRx = []
    WRy = []
    print('z        xRMS         yRMS       mesh.nx  mesh.ny       xStart       yStart')
    for j in range(NumSteps):
        # Calculating Initial Wavefront and extracting Intensity:
        srwl.CalcElecFieldGaussian(wfr, GsnBm, arPrecPar)
        arI0 = array('f', [0] * wfr.mesh.nx * wfr.mesh.ny)  # "flat" array to take 2D intensity data
        srwl.CalcIntFromElecField(arI0, wfr, 6, 0, 3, wfr.mesh.eStart, 0, 0)  # extracts intensity
        wfrP = deepcopy(wfr)
        InitialDist = InitialDist + StepSize
        (opBL, LensMatrX, LensMatrY, DriftMatr) = Container(InitialDist, f_x, f_y)
        srwl.PropagElecField(wfrP, opBL)  # Propagate E-field

        # Selecting radiation properties
        Polar = 6  # 0- Linear Horizontal /  1- Linear Vertical 2- Linear 45 degrees / 3- Linear 135 degrees / 4- Circular Right /  5- Circular /  6- Total
        Intens = 0  # 0=Single-e I/1=Multi-e I/2=Single-e F/3=Multi-e F/4=Single-e RadPhase/5=Re single-e Efield/6=Im single-e Efield
        DependArg = 3  # 0 - vs e, 1 - vs x, 2 - vs y, 3- vs x&y, 4-vs x&e, 5-vs y&e, 6-vs x&y&e
        plotNum = 1000
        plotMeshx = [plotNum * wfrP.mesh.xStart, plotNum * wfrP.mesh.xFin, wfrP.mesh.nx]
        plotMeshy = [plotNum * wfrP.mesh.yStart, plotNum * wfrP.mesh.yFin, wfrP.mesh.ny]

        # Extracting output wavefront
        arII = array('f', [0] * wfrP.mesh.nx * wfrP.mesh.ny)  # "flat" array to take 2D intensity data
        arIE = array('f', [0] * wfrP.mesh.nx * wfrP.mesh.ny)
        srwl.CalcIntFromElecField(arII, wfrP, Polar, Intens, DependArg, wfrP.mesh.eStart, 0, 0)
        arIx = array('f', [0] * wfrP.mesh.nx)
        srwl.CalcIntFromElecField(arIx, wfrP, 6, Intens, 1, wfrP.mesh.eStart, 0, 0)
        arIy = array('f', [0] * wfrP.mesh.ny)
        srwl.CalcIntFromElecField(arIy, wfrP, 6, Intens, 2, wfrP.mesh.eStart, 0, 0)
        x = []
        y = []
        arIxmax = max(arIx)
        arIxh = []
        arIymax = max(arIx)
        arIyh = []
        for i in range(wfrP.mesh.nx):
            x.append((i - wfrP.mesh.nx / 2.0) / wfrP.mesh.nx * (wfrP.mesh.xFin - wfrP.mesh.xStart))
            arIxh.append(float(arIx[i] / arIxmax - 0.5))
        for i in range(wfrP.mesh.ny):
            y.append((i - wfrP.mesh.ny / 2.0) / wfrP.mesh.ny * (wfrP.mesh.yFin - wfrP.mesh.yStart))
            arIyh.append(float(arIy[i] / arIymax - 0.5))
        xRMS.append(FWHM(x, arIxh))
        yRMS.append(FWHM(y, arIyh))
        s.append(InitialDist)
        (tRMSfunX, tRMSfunY) = BLMatrixMult(LensMatrX, LensMatrY, DriftMatr, DriftMatr0)
        WRx.append(tRMSfunX)
        WRy.append(tRMSfunY)
        print(InitialDist, xRMS[j], yRMS[j], wfrP.mesh.nx, wfrP.mesh.ny, wfrP.mesh.xStart, wfrP.mesh.yStart)

    # 6. Analytic calculations
    xRMSan = AnalyticEst(GsnBm.avgPhotEn, wfr.mesh.zStart + s[0], GsnBm.sigX, s)
    (qxP, Lam) = qParameter(GsnBm.avgPhotEn, GsnBm.sigX, wfr.mesh.zStart + s[0])
    qx0 = complex(0, 3.1415 / Lam * GsnBm.sigX ** 2)
    qy0 = complex(0, 3.1415 / Lam * GsnBm.sigY ** 2)
    Wthx = []
    Wthy = []
    for m in range(len(s)):
        Wx = (WRx[m][0][0] * qx0 + WRx[m][0][1]) / (WRx[m][1][0] * qx0 + WRx[m][1][1])  # MatrixMultiply(WR,qxP)
        RMSbx = sqrt(1.0 / (-1.0 / Wx).imag / 3.1415 * Lam) * 2.35
        Wthx.append(RMSbx)
        Wy = (WRy[m][0][0] * qy0 + WRy[m][0][1]) / (WRy[m][1][0] * qy0 + WRy[m][1][1])  # MatrixMultiply(WR,qxP)
        RMSby = sqrt(1.0 / (-1.0 / Wy).imag / 3.1415 * Lam) * 2.35
        Wthy.append(RMSby)

    # 7. Plotting
    plt.plot(s, xRMS, '-r.', label="X envelope via SRW")
    plt.plot(s, Wthx, '--ro', label="X envelope via analytical propagator")
    plt.plot(s, yRMS, '-b.', label="Y envelope via SRW")
    plt.plot(s, Wthy, '--bo', label="Y envelope via analytical propagator")
    plt.legend()
    plt.xlabel('Distance along beam line, [m]')
    plt.ylabel('Horizontal and Vertical RMS beam sizes, [m]')
    plt.title('Gaussian beam envelopes through a drift after a lens')
    plt.grid()
    plt.show()
    plt.clf()

    uti_plot.uti_plot2d(arII, plotMeshx, plotMeshy,
                        ['Horizontal Position [mm]', 'Vertical Position [mm]', 'Intenisty, [a.u.]'])
    uti_plot.uti_plot_show()

    print('Exit')
