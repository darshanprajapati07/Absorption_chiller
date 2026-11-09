function P = psat_w(T)
%PSAT_W  Saturation pressure of water [Pa] from temperature [degC].
%   IAPWS-IF97 region 4 saturation-pressure equation (vectorised).
n = [0.11670521452767e4, -0.72421316703206e6, -0.17073846940092e2, ...
     0.12020824702470e5, -0.32325550322333e7,  0.14915108613530e2, ...
    -0.48232657361591e4,  0.40511340542057e6, -0.23855557567849, ...
     0.65017534844798e3];
Tk = T + 273.15;
th = Tk + n(9)./(Tk - n(10));
A  = th.^2 + n(1)*th + n(2);
B  = n(3)*th.^2 + n(4)*th + n(5);
C  = n(6)*th.^2 + n(7)*th + n(8);
P  = (2*C./(-B + sqrt(B.^2 - 4*A.*C))).^4 * 1e6;
end
