% =============================================================
% Project Nira — Open Hardware Microplastics Detector
% File:    nira_plot_histogram.m
% Purpose: Overlapping probability-density histograms of
%          diff_c1_c4 with Gaussian fits and detection threshold.
%          Uses patch polygons for FaceAlpha compatibility
%          across all GNU Octave versions (no extra packages).
%
% SPDX-License-Identifier: MIT
% Copyright (C) 2026  only-foss
% Repository: https://github.com/only-foss/Project-Nira
% Hardware licensed under CERN-OHL-P v2
% <https://cern-ohl.web.cern.ch/>
% =============================================================

function nira_plot_histogram(clean_diff, micro_diff, threshold, results_dir)
  % NIRA_PLOT_HISTOGRAM  Overlapping histograms + Gaussian fits.
  %
  %   nira_plot_histogram(CLEAN_DIFF, MICRO_DIFF, THRESHOLD, RESULTS_DIR)
  %
  %   Inputs:
  %     CLEAN_DIFF  — diff_c1_c4 values, clean water (Nx1)
  %     MICRO_DIFF  — diff_c1_c4 values, microplastics (Mx1)
  %     THRESHOLD   — detection threshold scalar (ADC units)
  %     RESULTS_DIR — output directory path (string)
  %
  %   Output:
  %     <RESULTS_DIR>/nira_03_histogram.png

  fig = figure('Position', [100 100 800 480], 'Visible', 'off');

  all_vals = [clean_diff; micro_diff];
  edges    = linspace(min(all_vals) - 50, max(all_vals) + 50, 30);
  bin_w    = edges(2) - edges(1);

  % Normalised histograms built as patch polygons
  % (avoids bar() FaceAlpha issues on older Octave versions)
  h1 = histc(clean_diff, edges);
  h2 = histc(micro_diff, edges);
  h1 = h1 / (sum(h1) * bin_w);
  h2 = h2 / (sum(h2) * bin_w);

  [px1, py1] = nira_bar_poly(edges, h1);
  [px2, py2] = nira_bar_poly(edges, h2);

  patch(px1, py1, [0.2 0.5 0.9], 'FaceAlpha', 0.55, 'EdgeColor', 'none');
  hold on;
  patch(px2, py2, [0.9 0.3 0.3], 'FaceAlpha', 0.55, 'EdgeColor', 'none');

  % Gaussian fit overlays
  x_fit   = linspace(min(all_vals) - 100, max(all_vals) + 100, 400);
  mu_c    = mean(clean_diff); sig_c = std(clean_diff);
  mu_m    = mean(micro_diff); sig_m = std(micro_diff);
  gauss_c = (1/(sig_c*sqrt(2*pi))) * exp(-0.5*((x_fit - mu_c)/sig_c).^2);
  gauss_m = (1/(sig_m*sqrt(2*pi))) * exp(-0.5*((x_fit - mu_m)/sig_m).^2);

  plot(x_fit, gauss_c, 'b-', 'LineWidth', 2);
  plot(x_fit, gauss_m, 'r-', 'LineWidth', 2);

  % Vertical reference lines (threshold + means)
  yl = [0, max([h1; h2; gauss_c'; gauss_m']) * 1.15];
  plot([threshold threshold], yl,        'g--', 'LineWidth', 2);
  plot([mu_c mu_c],           yl * 0.85, 'b:',  'LineWidth', 1.5);
  plot([mu_m mu_m],           yl * 0.85, 'r:',  'LineWidth', 1.5);
  text(threshold + 5, yl(2) * 0.95, sprintf('Thr=%.0f', threshold), ...
       'Color', [0 0.6 0], 'FontSize', 8);
  text(mu_c + 5, yl(2) * 0.78, sprintf('mu=%.0f', mu_c), ...
       'Color', 'b', 'FontSize', 8);
  text(mu_m + 5, yl(2) * 0.78, sprintf('mu=%.0f', mu_m), ...
       'Color', 'r', 'FontSize', 8);
  ylim(yl);

  legend('Clean Water', 'Microplastics', 'Gaussian (clean)', ...
         'Gaussian (micro)', 'Location', 'northeast');
  xlabel('\DeltaADC (CH1 - CH4)');
  ylabel('Probability Density');
  title('Project Nira - Differential Signal Distribution', ...
        'FontSize', 12, 'FontWeight', 'bold');
  grid on;

  out = fullfile(results_dir, 'nira_03_histogram.png');
  print(fig, out, '-dpng', '-r150');
  close(fig);
  printf('  Saved: %s\n', out);

end

% ------------------------------------------------------------------
function [px, py] = nira_bar_poly(edges, heights)
  % NIRA_BAR_POLY  Build staircase polygon vertices for a histogram.
  %   Returns PX, PY suitable for patch() from bin EDGES and HEIGHTS.
  n  = length(edges);
  px = zeros(1, 4*(n-1));
  py = zeros(1, 4*(n-1));
  for k = 1:n-1
    idx     = (k-1)*4 + (1:4);
    px(idx) = [edges(k) edges(k+1) edges(k+1) edges(k)];
    py(idx) = [0        0          heights(k)  heights(k)];
  end
end
