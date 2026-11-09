function P = calibrate_model(D)
%CALIBRATE_MODEL  Build model parameters so that the dynamic model's steady
%   state at the design inputs reproduces the Aspen base-case states.
%   Calibrated: equilibrium offsets, vapour conductances, UA values (G, C,
%   E, A, SHX), generator outflow constant, design water flows.
a = D.aspen;
P.D = D; P.cpw = D.cpw;
P.Mc = D.Mc; P.MG0 = D.M0.G; P.MA0 = D.M0.A; P.ME0 = D.M0.E; P.ME_dry = D.ME_dry;
P.eps_G = D.eps_G; P.eps_A = D.eps_A;

PC = psat_w(a.T_C);  PE = psat_w(a.T_E);

%% Equilibrium offsets
% pure equilibrium (used for steady-state validation against SENS-1)
P.dTG_eq = a.T_G - duhring_T(a.x_s, a.T_C);
P.dTA_eq = a.T_A - duhring_T(a.x_w, a.T_E);
% dynamic model: includes the small vapour-flow driving pressure difference
dPG = D.dP_frac_G*PC;  dPA = D.dP_frac_A*PE;
P.dTG = a.T_G - duhring_T(a.x_s, tsat_w(PC + dPG));
P.dTA = a.T_A - duhring_T(a.x_w, tsat_w(PE - dPA));
P.kG = a.m_ref/spos(dPG, P.eps_G);
fE0  = P.ME0/(P.ME0 + P.ME_dry);
P.kA = a.m_ref/(fE0*spos(dPA, P.eps_A));

%% Generator strong-solution outflow (level driven): m_ss = mss0*M_G/M_G0
P.mss0 = a.m_ss;

%% Solution heat exchanger: UA from Aspen T5 (counter-flow eps-NTU)
[hG, hGT] = h_sol(a.x_s, a.T_G);
[hA, hAT] = h_sol(a.x_w, a.T_A);
Qshx = a.m_ss*(hG - h_sol(a.x_s, a.T5));
CH = a.m_ss*hGT;  CC = a.m_p*hAT;
Cmin = min(CH, CC);  Cr = Cmin/max(CH, CC);
eps = Qshx/(Cmin*(a.T_G - a.T_A));
NTU = log((1 - eps*Cr)/(1 - eps))/(1 - Cr);
P.UA_shx = NTU*Cmin;

%% Model duties at the Aspen states
h3  = hA + Qshx/a.m_p;
h5  = hG - Qshx/a.m_ss;
TvG = min(a.T_G, duhring_T(a.x_w, a.T_C) + P.dTG_eq);  % vapour leaves at inlet equilibrium T
[hfC, ~]   = water_h(a.T_C);
[~, hvG]   = water_h(TvG);
[~, hvE]   = water_h(a.T_E);
Q_G = a.m_ss*hG + a.m_ref*hvG - a.m_p*h3;
Q_C = a.m_ref*(hvG - hfC);                 % rejected
Q_E = a.m_ref*(hvE - hfC);
Q_A = a.m_ss*h5 + a.m_ref*hvE - a.m_p*hA;  % rejected

%% External water flows and UA values
cp = D.cpw;
m_hw  = Q_G/(cp*D.hw.dT);
m_cw  = Q_A/(cp*D.cw.dT_A);
m_chw = Q_E/(cp*(D.chw.T_in - D.chw.T_out));
T_hw_out  = D.hw.T_in - D.hw.dT;
T_cw_mid  = D.cw.T_in + D.cw.dT_A;
T_cw_out  = T_cw_mid + Q_C/(m_cw*cp);
assert(T_hw_out > a.T_G && T_cw_mid < a.T_A && T_cw_out < a.T_C && D.chw.T_out > a.T_E, ...
    'Design water temperatures are thermodynamically infeasible.');
P.UA_G = m_hw*cp*log((D.hw.T_in - a.T_G)/(T_hw_out - a.T_G));
P.UA_A = m_cw*cp*log((a.T_A - D.cw.T_in)/(a.T_A - T_cw_mid));
P.UA_C = m_cw*cp*log((a.T_C - T_cw_mid)/(a.T_C - T_cw_out));
P.UA_E = m_chw*cp*log((D.chw.T_in - a.T_E)/(D.chw.T_out - a.T_E));

%% Nominal inputs u = [T_hw, m_hw, T_cw, m_cw, T_chw, m_chw, m_pump]
P.u0 = [D.hw.T_in, m_hw, D.cw.T_in, m_cw, D.chw.T_in, m_chw, a.m_p];
P.input_names = {'T_hw_in_C','m_hw_kg_s','T_cw_in_C','m_cw_kg_s','T_chw_in_C','m_chw_kg_s','m_pump_kg_s'};

%% Nominal state x = [T_G M_G L_G T_C T_E M_E T_A M_A L_A]
P.x0 = [a.T_G, P.MG0, P.MG0*a.x_s/100, a.T_C, a.T_E, P.ME0, a.T_A, P.MA0, P.MA0*a.x_w/100]';
P.state_names = {'T_G','M_G','L_G','T_C','T_E','M_E','T_A','M_A','L_A'};

%% Model duties at design (for the report)
P.design = struct('Q_gen',Q_G,'Q_cond',Q_C,'Q_evap',Q_E,'Q_abs',Q_A,'Q_shx',Qshx, ...
    'COP',Q_E/Q_G,'T3',T_from_h_sol(a.x_w,h3),'T_vap_G',TvG, ...
    'T_hw_out',T_hw_out,'T_cw_mid',T_cw_mid,'T_cw_out',T_cw_out,'T_chw_out',D.chw.T_out);

%% Consistency check: derivatives at the nominal point must be ~0
dx = model_ode(0, P.x0, @(t) P.u0, P);
scale = [1 100 100 1 1 10 1 100 100]';
P.design.max_dxdt = max(abs(dx./scale));
assert(P.design.max_dxdt < 1e-6, 'Calibration failed: nominal point is not a steady state (%.3g).', P.design.max_dxdt);
end
