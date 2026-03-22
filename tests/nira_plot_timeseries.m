% =============================================================
% nira_plot_timeseries.m
% Time-series plot: ch1, ch4, and diff for both test conditions
% Project Nira - https://github.com/only-foss/Project-Nira
% =============================================================

function nira_plot_timeseries(clean_ch1, clean_ch4, clean_diff, ...
                               micro_ch1, micro_ch4, micro_diff)

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
  % zero reference line
  xl = [1, max(length(clean_diff), length(micro_diff))];
  plot(xl, [0 0], 'k--', 'LineWidth', 1);
  legend('Clean Water', 'Microplastics', 'Zero', 'Location', 'northeast');
  xlabel('Sample Index');
  ylabel('\DeltaADC (CH1 - CH4)');
  title('Differential Signal: CH1 - CH4  (Key Detection Feature)');
  grid on;

  % Main title via annotation (sgtitle needs Octave >= 8; use this instead)
  axes('Position', [0 0 1 1], 'Visible', 'off');
  text(0.5, 0.99, 'Project Nira - Sensor Time Series', ...
       'HorizontalAlignment', 'center', 'VerticalAlignment', 'top', ...
       'FontSize', 13, 'FontWeight', 'bold');

  print(fig, 'nira_01_timeseries.png', '-dpng', '-r150');
  close(fig);
  printf('  Saved: nira_01_timeseries.png\n');

end
