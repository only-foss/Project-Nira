% =============================================================
% Project Nira — Open Hardware Microplastics Detector
% File:    nira_plot_scatter.m
% Purpose: CH1 vs CH4 scatter plot showing the directional
%          channel shift between clean water and microplastic
%          conditions. Uses plot() for full Octave compatibility
%          (avoids scatter() MarkerFaceAlpha issues).
%
% SPDX-License-Identifier: MIT
% Copyright (C) 2026  only-foss
% Repository: https://github.com/only-foss/Project-Nira
% Hardware licensed under CERN-OHL-P v2
% <https://cern-ohl.web.cern.ch/>
% =============================================================

function nira_plot_scatter(clean_ch1, clean_ch4, micro_ch1, micro_ch4, results_dir)
  % NIRA_PLOT_SCATTER  CH1 vs CH4 scatter plot.
  %
  %   nira_plot_scatter(CLEAN_CH1, CLEAN_CH4,
  %                     MICRO_CH1, MICRO_CH4, RESULTS_DIR)
  %
  %   Inputs:
  %     CLEAN_CH1   — CH1 raw ADC values, clean water (Nx1)
  %     CLEAN_CH4   — CH4 raw ADC values, clean water (Nx1)
  %     MICRO_CH1   — CH1 raw ADC values, microplastics (Mx1)
  %     MICRO_CH4   — CH4 raw ADC values, microplastics (Mx1)
  %     RESULTS_DIR — output directory path (string)
  %
  %   Output:
  %     <RESULTS_DIR>/nira_04_scatter.png
  %
  %   The diagonal dashed line (CH1 = CH4) marks zero differential.
  %   Points above the line → CH1 > CH4 (positive diff, microplastics).
  %   Points below the line → CH1 < CH4 (negative diff, clean water).

  fig = figure('Position', [100 100 700 600], 'Visible', 'off');

  plot(clean_ch1, clean_ch4, 'o', 'MarkerSize', 6, ...
       'MarkerFaceColor', [0.2 0.5 0.9], ...
       'MarkerEdgeColor', [0.1 0.3 0.7], ...
       'LineStyle', 'none');
  hold on;
  plot(micro_ch1, micro_ch4, 'o', 'MarkerSize', 6, ...
       'MarkerFaceColor', [0.9 0.3 0.3], ...
       'MarkerEdgeColor', [0.7 0.1 0.1], ...
       'LineStyle', 'none');

  % Diagonal reference line: CH1 = CH4 (diff = 0)
  all_vals = [clean_ch1; micro_ch1; clean_ch4; micro_ch4];
  ax_min   = min(all_vals) - 100;
  ax_max   = max(all_vals) + 100;
  plot([ax_min ax_max], [ax_min ax_max], 'k--', 'LineWidth', 1.2);
  text(ax_min + 60, ax_min + 160, 'CH1 = CH4  (diff=0)', ...
       'FontSize', 8, 'Color', [0.4 0.4 0.4]);

  % Centroid markers
  plot(mean(clean_ch1), mean(clean_ch4), 'bx', ...
       'MarkerSize', 14, 'LineWidth', 3);
  plot(mean(micro_ch1), mean(micro_ch4), 'rx', ...
       'MarkerSize', 14, 'LineWidth', 3);

  legend('Clean Water', 'Microplastics', 'CH1=CH4 line', ...
         'Centroid (clean)', 'Centroid (micro)', 'Location', 'northwest');
  xlabel('CH1 Raw (ADC)');
  ylabel('CH4 Raw (ADC)');
  title('Project Nira - CH1 vs CH4 Channel Scatter', ...
        'FontSize', 12, 'FontWeight', 'bold');
  grid on;
  axis equal;
  xlim([ax_min ax_max]);
  ylim([ax_min ax_max]);

  out = fullfile(results_dir, 'nira_04_scatter.png');
  print(fig, out, '-dpng', '-r150');
  close(fig);
  printf('  Saved: %s\n', out);

end
