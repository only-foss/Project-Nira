% =============================================================
% Project Nira — Open Hardware Microplastics Detector
% File:    nira_plot_timeseries.m
% Purpose: Time-series plot of CH1, CH4, and diff_c1_c4 for
%          both test conditions (clean water vs microplastics)
%
% SPDX-License-Identifier: MIT
% Copyright (C) 2026  only-foss
% Repository: https://github.com/only-foss/Project-Nira
% Hardware licensed under CERN-OHL-P v2
% <https://cern-ohl.web.cern.ch/>
% =============================================================

function nira_plot_timeseries(clean_ch1, clean_ch4, clean_diff, ...
                               micro_ch1, micro_ch4, micro_diff, results_dir)
  % NIRA_PLOT_TIMESERIES  Three-panel time-series plot.
  %
  %   nira_plot_timeseries(CLEAN_CH1, CLEAN_CH4, CLEAN_DIFF,
  %                        MICRO_CH1, MICRO_CH4, MICRO_DIFF,
  %                        RESULTS_DIR)
  %
  %   Inputs:
  %     CLEAN_CH1   — CH1 raw ADC values, clean water (Nx1)
  %     CLEAN_CH4   — CH4 raw ADC values, clean water (Nx1)
  %     CLEAN_DIFF  — diff_c1_c4 values, clean water (Nx1)
  %     MICRO_CH1   — CH1 raw ADC values, microplastics (Mx1)
  %     MICRO_CH4   — CH4 raw ADC values, microplastics (Mx1)
  %     MICRO_DIFF  — diff_c1_c4 values, microplastics (Mx1)
  %     RESULTS_DIR — output directory path (string)
  %
  %   Output:
  %     <RESULTS_DIR>/nira_01_timeseries.png

  fig = figure('Position', [100 100 1100 750], 'Visible', 'off');
  t_c = (1:length(clean_ch1))';
  t_m = (1:length(micro_ch1))';

  % ---- CH1 Raw -----
  subplot(3, 1, 1);
  plot(t_c, clean_ch1, 'b-o', 'MarkerSize', 3, 'LineWidth', 1.2); hold on;
  plot(t_m, micro_ch1, 'r-o', 'MarkerSize', 3, 'LineWidth', 1.2);
  legend('Clean Water', 'Microplastics', 'Location', 'northeast');
  ylabel('ADC Value');
  title('CH1 Raw Signal');
  grid on;

  % ---- CH4 Raw -----
  subplot(3, 1, 2);
  plot(t_c, clean_ch4, 'b-s', 'MarkerSize', 3, 'LineWidth', 1.2); hold on;
  plot(t_m, micro_ch4, 'r-s', 'MarkerSize', 3, 'LineWidth', 1.2);
  legend('Clean Water', 'Microplastics', 'Location', 'northeast');
  ylabel('ADC Value');
  title('CH4 Raw Signal');
  grid on;

  % ---- Differential -----
  subplot(3, 1, 3);
  plot(t_c, clean_diff, 'b-^', 'MarkerSize', 3, 'LineWidth', 1.4); hold on;
  plot(t_m, micro_diff, 'r-^', 'MarkerSize', 3, 'LineWidth', 1.4);
  xl = [1, max(length(clean_diff), length(micro_diff))];
  plot(xl, [0 0], 'k--', 'LineWidth', 1);
  legend('Clean Water', 'Microplastics', 'Zero', 'Location', 'northeast');
  xlabel('Sample Index');
  ylabel('\DeltaADC (CH1 - CH4)');
  title('Differential Signal: CH1 - CH4  (Key Detection Feature)');
  grid on;

  axes('Position', [0 0 1 1], 'Visible', 'off');
  text(0.5, 0.99, 'Project Nira - Sensor Time Series', ...
       'HorizontalAlignment', 'center', 'VerticalAlignment', 'top', ...
       'FontSize', 13, 'FontWeight', 'bold');

  out = fullfile(results_dir, 'nira_01_timeseries.png');
  print(fig, out, '-dpng', '-r150');
  close(fig);
  printf('  Saved: %s\n', out);

end
