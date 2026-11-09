function A = model_algebraic(x, u, P)
%MODEL_ALGEBRAIC  All flows, duties and temperatures for one state/input.
%   x = [T_G M_G L_G T_C T_E M_E T_A M_A L_A]
%   u = [T_hw m_hw T_cw m_cw T_chw m_chw m_pump]
cp = P.cpw;
A.T_G = x(1); A.M_G = x(2); A.T_C = x(4); A.T_E = x(5); A.M_E = x(6);
A.T_A = x(7); A.M_A = x(8);
A.x_G = 100*x(3)/x(2);           % strong solution [wt%]
A.x_A = 100*x(9)/x(8);           % weak solution [wt%]
m_p = u(7);

%% Pressures and vapour flows
A.P_C = psat_w(A.T_C);           % high pressure [Pa]
A.P_E = psat_w(A.T_E);           % low pressure [Pa]
A.Psol_G = p_sol(A.T_G, A.x_G, P.dTG);
A.Psol_A = p_sol(A.T_A, A.x_A, P.dTA);
A.m_GC = P.kG*spos(A.Psol_G - A.P_C, P.eps_G);              % desorbed vapour
fE     = A.M_E/(A.M_E + P.ME_dry);
A.m_EA = P.kA*fE*spos(A.P_E - A.Psol_A, P.eps_A);           % absorbed vapour
A.m_ss = P.mss0*A.M_G/P.MG0;                                 % strong solution
A.m_p  = m_p;

%% Enthalpies
[A.hG, A.hGT, A.hGx] = h_sol(A.x_G, A.T_G);
[A.hA, A.hAT, A.hAx] = h_sol(A.x_A, A.T_A);
A.T_vG = min(A.T_G, duhring_T(A.x_A, A.T_C) + P.dTG_eq);    % vapour leaving generator
[~, A.hvG] = water_h(A.T_vG);
[A.hfC, ~] = water_h(A.T_C);
[A.hfE, A.hvE] = water_h(A.T_E);

%% Solution heat exchanger (counter-flow eps-NTU)
CH = A.m_ss*A.hGT;  CC = m_p*A.hAT;
Cmin = min(CH, CC);  Cr = Cmin/max(CH, CC);
NTU = P.UA_shx/Cmin;
if abs(1 - Cr) < 1e-6
    eps = NTU/(1 + NTU);
else
    eps = (1 - exp(-NTU*(1 - Cr)))/(1 - Cr*exp(-NTU*(1 - Cr)));
end
A.Q_shx = eps*Cmin*(A.T_G - A.T_A);
A.h5 = A.hG - A.Q_shx/A.m_ss;
A.h3 = A.hA + A.Q_shx/m_p;
A.T5 = T_from_h_sol(A.x_G, A.h5);
A.T3 = T_from_h_sol(A.x_A, A.h3);

%% External heat exchange (vessel at uniform temperature, eps = 1-exp(-NTU))
Chw = u(2)*cp;  Ccw = u(4)*cp;  Cchw = u(6)*cp;
A.Q_gen  = Chw*(u(1) - A.T_G)*(1 - exp(-P.UA_G/Chw));        % into generator
A.T_hw_out = u(1) - A.Q_gen/Chw;
A.Q_abs  = Ccw*(A.T_A - u(3))*(1 - exp(-P.UA_A/Ccw));        % rejected by absorber
A.T_cw_mid = u(3) + A.Q_abs/Ccw;
A.Q_cond = Ccw*(A.T_C - A.T_cw_mid)*(1 - exp(-P.UA_C/Ccw));  % rejected by condenser
A.T_cw_out = A.T_cw_mid + A.Q_cond/Ccw;
A.Q_evap = Cchw*(u(5) - A.T_E)*(1 - exp(-P.UA_E/Cchw));      % into evaporator
A.T_chw_out = u(5) - A.Q_evap/Cchw;

%% Stored energy (for the energy-conservation check)
A.U = P.Mc.G*A.T_G + A.M_G*A.hG + P.Mc.A*A.T_A + A.M_A*A.hA + ...
      P.Mc.C*A.T_C + P.Mc.E*A.T_E + A.M_E*A.hfE;
end
