What nira_reader.py does
InfluxDB → fetch → export CSV → run Octave → git push
1. Fetch — queries nira_sensor measurement, nira_esp32 device tag, gets ch1_raw, ch4_raw, diff_c1_c4
2. Export — saves to two places automatically:

tests/data/<label>_<timestamp>.csv — timestamped archive, never overwritten
tests/analysis/clean_water.csv or micro_water.csv — overwrites for Octave to pick up

3. Quick stats — prints mean/std/min/max and detects microplastics on the spot:
  >> MICROPLASTICS LIKELY PRESENT   (if diff_c1_c4 > 92 ADC units)
  >> Water appears CLEAN
4. Octave analysis — runs nira_analysis.m automatically, saves 4 PNGs to tests/results/
5. Git push — stages tests/, commits with auto timestamp, pushes to GitHub

Setup
bash# 1. Install dependencies
pip install influxdb-client pandas

# 2. Set your credentials (or edit CONFIG in the script)
export NIRA_INFLUX_URL="http://your-influxdb-host:8086"
export NIRA_INFLUX_TOKEN="your_token"
export NIRA_INFLUX_ORG="your_org"
export NIRA_INFLUX_BUCKET="your_bucket"

# 3. Place in repo
cp nira_reader.py ~/Downloads/Microplastic_Detection/python/
cp requirements.txt ~/Downloads/Microplastic_Detection/python/

Usage examples
bash# Fetch last 1 hour, print stats only
python python/nira_reader.py

# Fetch specific test window and label it
python python/nira_reader.py \
  --start 2026-03-22T11:27:00Z \
  --stop  2026-03-22T11:36:00Z \
  --label test-0_cleanWater

# Fetch + run Octave analysis
python python/nira_reader.py --analyse

# Full pipeline: fetch + analyse + git push to GitHub
python python/nira_reader.py --push

# Dry run — fetch and print stats only, no files written
python python/nira_reader.py --dry-run
