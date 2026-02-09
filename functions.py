import numpy as np

# ************************ GEOMETRY ************************

# calculate dish volume [m3]
def dish_volume(r):
    dish = r[('Bottom Dish Type', '-')]
    Di = r[('Internal Diameter', 'm')]
    if dish == "ASME 2:1 Elliptical":
        C = 1/2
    elif dish == "Hemispherical":
        C = 1
    elif dish == "ASME Torispherical" or dish == "Torispherical":
        t = r[('Wall Thickness', 'mm')]/1e3
        Do = r[('Outside Diameter', 'm')]
        Rk = r[('Knuckle Radius', 'm')]
        C = 0.30939 + 1.7197*(Rk-0.06*Do)/Di - 0.16116*t/Do + 0.98997*(t/Do)**2
    elif dish == "DIN Torispherical":
        t = r[('Wall Thickness', 'mm')]/1e3
        Do = r[('Outside Diameter', 'm')]
        C = 0.37802 + 0.05073*(t/Do) + 1.3762

    return (Di**3 * C * np.pi / 12)


# ************************FLUID DYNAMICS ************************

# Reynolds number [-]
def Re_STR(p,d,N,mu):
    '''
    Reynolds number for stirred tank
    p: density [kg/m3]
    d: impeller diameter [m]
    N: impeller speed [rpm]
    mu: viscosity [cP]
    '''
    return p*(N/60)*(d**2)/(mu/1000)

# Impeller power input; P = Po rho_L N^3 D^5 [W]
# This is per impeller; sum all powers for multiple impellers
def power_input(Po, rho_L, N, D):
    '''
    Po: impeller power [W]
    rho_L: liquid density [kg/m3]
    N: impeller speed [rps]
    D: impeller diameter [m]
    '''
    return Po * rho_L * (N/60)**3 * D**5

# Mixing time [s]
def tm1(Km, V, N, D):
    '''
    Km: mixing constant
    V: liquid volume [L]
    N: impeller speed [rpm]
    D: impeller diameter [m]
    '''
    return Km*(V/1000)*(N/60)**(-1/3)*D**(-5)

# Mixing time (from Dynochem) [s]
def tm2(H, T, D, V, eps, mu, rho_L, regime="Turbulent"):
    '''
    H: height of liquid [m]
    T: tank diameter [m]
    D: impeller diameter [m]
    V: liquid volume [m3]
    eps: power per unit volume (kW/m3)
    '''
    if regime == "Turbulent":
        # tmix = C1 eps^(-1/3) (T/D)^1/3 T ^2/3
        # calculate constant; 5.4(H/T)^1.4/(V/(T^2H))^1/3
        C = 5.4 * (H/T)**1.4 / ((V/(T**2 * H))**(1/3))
        tmix = C * eps**(-1/3) * (T/D)**(1/3) * T**(2/3)

    elif regime == "Transitional":
        # tmix = C eps^-2/3 mu/rho_L (T/D)^2/3 T^-2/3
        # calculate constant; 38025/(V/(T^2H))^2/3
        C = 38025 / (V/(T**2 * H))**(2/3)
        tmix = C * eps**(-2/3) * (mu/rho_L) * (T/D)**(2/3) * T**(-2/3)
        
    else:
        tmix = None

    return tmix

# Micro-mixing rate [1/s]
def micro_mixing_rate(eps, nu):
    '''
    Micro-mixing rate. Engulfment model.

    eps: power per unit mass [W/kg]=[m2/s3]
    nu: kinematic viscosity [m2/s]
    '''
    C = 0.05776
    return C * (eps / nu)**0.5

# kolmogorov length scale [m]
def kolmogorov_length(eps, nu):
    '''
    Kolmogorov time scale

    eps: power per unit mass [W/kg]=[m2/s3]
    nu: kinematic viscosity [m2/s]
    '''
    return (nu**3 / eps)**0.25

# taylor length scale [m]

# vessel average shear rate [1/s]
def shear_vessel(P, V, mu):
    '''
    Vessel average shear rate

    P: power [W]
    V: volume [m3]
    mu: viscosity [Pa.s]
    '''
    return (P/V/mu)**(1/2)

# impeller average shear rate [1/s]
def shear_impeller(P, d, mu):
    '''
    Impeller average shear rate

    P: power [W]
    d: impeller diameter [m]
    mu: viscosity [Pa.s]
    '''
    Vimp = (np.pi * d**2/4) * (d/4)
    return (0.3* P/(Vimp * mu))**(1/2)

# tip speed [m/s]
def tip_speed(N, d):
    '''
    Tip speed

    N: impeller speed [rpm]
    d: impeller diameter [m]
    '''
    return (np.pi * d * N)/60


# *************** MASS TRANSFER: G-L GAS DRAWDOWN ***************

def Nmin_gas_drawdown(D, H_sub, gassing_system="vortexing", g=9.81):
    '''
    Minimum stir speed at which drawdown occurs [rpm]

    Fr: Critical Froude number at which gassing begins N^2D^2/(g.H_sub) [-]
    g: Acceleration due to gravity, default is 9.81 [m/s2]
    H_sub: Submergence of upper impeller [m]
    D: Diameter of upper impeller [m]

    Ref.: Dynochem Basis GLD
    '''
    if gassing_system=="vortexing":
        Fr = 0.15
    elif gassing_system=="self-aspirating":
        Fr = 0.20

    return (Fr * g * H_sub/(D**2))**0.5 * 60

def kLa_gas_drawdown(A, b, P, M):
    '''
    kLa correlation for gas-liquid mass transfer from headspace.
    Using only power input.

    A: Empirical constant
    b: Empirical constant
    P: Power [W]
    M: Liquid mass [kg]

    Ref.: Dynochem Basis GLD
    '''
    return A * (P/M)**b

def kLa_gas_drawdown_2(C, b, P, M, H_sub, D, e):
    '''
    kLa correlation for gas-liquid mass transfer from headspace.
    Using power input and submergence.

    C: Empirical constant
    b: Empirical constant
    P: Power [W]
    M: Liquid mass [kg]
    H_sub: Submergence of upper impeller [m]
    D: Diameter of upper impeller [m]
    e: Empirical constant

    Ref.: Dynochem Basis GLD
    '''
    return C * (P/M)**b * (H_sub/D)**e

# *************** PARTICLE SUSPENSION ***************

# Zwietering correlation for Njs
def Njs_Z(S, nu, rho_L, rho_S, X, d_P, D, g=9.81):
    '''
    Just suspended speed using Zwietering correlation.

    S: geometric constant for Zwietering correlation
    nu: kinematic viscosity [m2/s]
    rho_L: liquid density [kg/m3]
    rho_S: solid density [kg/m3]
    X: mass ratio of solid to liquid (m_S/m_L * 100) [%]
    d_P: particle diameter [m]
    D: impeller diameter [m]
    g: acceleration due to gravity [m/s2], default is 9.81

    NJS = S nu^0.1 (g Drho/rho_L)^0.45 X^0.13 d_P^0.2 D^–0.85

    '''
    return S * (nu**(0.1)) * ((g*(rho_S - rho_L)/(rho_L))**(0.45)) * (X**0.13) * ((d_P)**(0.2)) * (D**(-0.85))

# Grenville, Mak, Brown correlation for Njs
def Njs_GMB(z, Po, D, rho_L, rho_S, Xv, d_P, C, g=9.81):
    '''
    Just suspended speed using GMB correlation.

    z: geometric constant in GMB [-]
    Po: impeller power [-]
    D: impeller diameter [m]
    g: acceleration due to gravity [m/s2], default is 9.81
    rho_L: liquid density [kg/m3]
    rho_S: solid density [kg/m3]
    Xv: volume fraction of solid (V_solid/V_slurry * 100) [%]
    d_P: particle diameter [m]
    C: impeller clearance [m]

    NJS = z Po^(-0.333) D^(-0.667) (g Drho/rho_L)^(0.5) Xv^(0.154) dP^(0.167) (C/D)^(0.1)
    '''
    return z * (Po**(-0.333)) * (D**(-0.667)) * ((g * (rho_S - rho_L) / rho_L)**(0.5)) * (Xv**(0.154)) * (d_P**(0.167)) * (C/D)**(0.1)

# ************************ STREAMLIT ************************

def custom_badge(background_color, text_color, font_size="14px", padding="5px 10px", border_radius="5px"):
    badge_style = f"""
    display: inline-block;
    background-color: {background_color};
    color: {text_color};
    font-size: {font_size};
    padding: {padding};
    border-radius: {border_radius};
    margin: 2px;
    """
    return badge_style