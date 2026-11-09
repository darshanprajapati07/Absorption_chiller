function T = duhring_T(x, Tref)
%DUHRING_T  Equilibrium solution temperature [degC] of H2O-LiBr.
%   x    : LiBr mass fraction [wt%]  (valid 45-70 wt%)
%   Tref : saturation temperature of pure water at the same pressure [degC]
%   Source: ASHRAE Handbook - Fundamentals, Duhring correlation
%   T = sum(B_n x^n) + Tref*sum(A_n x^n)
A = [-2.00755, 0.16976, -3.133362e-3, 1.97668e-5];
B = [124.937, -7.71649, 0.152286, -7.95090e-4];
T = (B(1) + x.*(B(2) + x.*(B(3) + x.*B(4)))) + ...
    Tref.*(A(1) + x.*(A(2) + x.*(A(3) + x.*A(4))));
end
