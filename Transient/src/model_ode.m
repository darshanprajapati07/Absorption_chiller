function dx = model_ode(t, x, uFun, P)
%MODEL_ODE  Lumped-parameter dynamic model of a single-effect H2O-LiBr
%   absorption chiller (generator, condenser, evaporator, absorber + SHX).
%   States x = [T_G M_G L_G T_C T_E M_E T_A M_A L_A]
%   T [degC], M (solution/refrigerant mass) [kg], L (LiBr mass) [kg].
%   Energy balances use d(Mc*T + M*h)/dt = sum(m*h)_in - sum(m*h)_out + Q.
u = uFun(t);
A = model_algebraic(x, u, P);
m_p = u(7);

%% Generator: weak solution in (T3, x_A); strong solution + vapour out
dMG = m_p - A.m_ss - A.m_GC;
dLG = m_p*A.x_A/100 - A.m_ss*A.x_G/100;
dxG = 100*(dLG - A.x_G/100*dMG)/A.M_G;
dTG = (m_p*(A.h3 - A.hG) - A.m_GC*(A.hvG - A.hG) + A.Q_gen - A.M_G*A.hGx*dxG) ...
      /(P.Mc.G + A.M_G*A.hGT);

%% Condenser: vapour in, saturated liquid out (no liquid hold-up)
dTC = (A.m_GC*(A.hvG - A.hfC) - A.Q_cond)/P.Mc.C;

%% Evaporator: liquid from condenser (throttled), vapour to absorber
dME = A.m_GC - A.m_EA;
dTE = (A.m_GC*(A.hfC - A.hfE) - A.m_EA*(A.hvE - A.hfE) + A.Q_evap) ...
      /(P.Mc.E + A.M_E*P.cpw);

%% Absorber: strong solution (T5) + vapour in, weak solution out
dMA = A.m_ss + A.m_EA - m_p;
dLA = A.m_ss*A.x_G/100 - m_p*A.x_A/100;
dxA = 100*(dLA - A.x_A/100*dMA)/A.M_A;
dTA = (A.m_ss*(A.h5 - A.hA) + A.m_EA*(A.hvE - A.hA) - A.Q_abs - A.M_A*A.hAx*dxA) ...
      /(P.Mc.A + A.M_A*A.hAT);

dx = [dTG; dMG; dLG; dTC; dTE; dME; dTA; dMA; dLA];
end
