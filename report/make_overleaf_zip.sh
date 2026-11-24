#!/bin/sh
# Refresh figures from outputs/fig and build report_overleaf.zip (upload via Overleaf: New Project > Upload Project).
set -e
cd "$(dirname "$0")"
for f in F0_setup F1_p4_example F2_power_vs_kappa_skew F2_power_vs_kappa_bc2 F3_rigging_bt_vs_bc \
         F4_elo_pred_vs_actual F5_formats_vs_kappa F6_bo3; do
  cp ../outputs/fig/$f.pdf figures/
done
rm -f report_overleaf.zip
zip -q report_overleaf.zip main.tex refs.bib figures/*.pdf
unzip -l report_overleaf.zip
