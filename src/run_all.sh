# First three files should be run in the order listed
python3 run_extract_tr_long.py > run_extract_tr_long.log
python3 run_tr_long_to_wide.py
python3 run_trans_stats_dib.py > run_trans_stats_dib.log
