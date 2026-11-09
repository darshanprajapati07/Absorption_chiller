function y = spos(d, e)
%SPOS  Smooth max(d,0) with smoothing width e (keeps the ODE differentiable).
y = 0.5*(d + sqrt(d.^2 + e^2));
end
