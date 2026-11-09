function P = p_sol(T, x, dT)
%P_SOL  Water vapour pressure [Pa] above H2O-LiBr solution.
%   T  : solution temperature [degC]
%   x  : LiBr mass fraction [wt%]
%   dT : calibration offset [K] so that the equilibrium matches Aspen
%        ELECNRTL (T_aspen = T_duhring + dT).
A = [-2.00755, 0.16976, -3.133362e-3, 1.97668e-5];
B = [124.937, -7.71649, 0.152286, -7.95090e-4];
a = A(1) + x.*(A(2) + x.*(A(3) + x.*A(4)));
b = B(1) + x.*(B(2) + x.*(B(3) + x.*B(4)));
Tref = (T - dT - b)./a;           % equivalent pure-water saturation temp.
P = psat_w(Tref);
end
