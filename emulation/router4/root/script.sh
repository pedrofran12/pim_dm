cd pim_dm

python3 Run.py -stop
python3 Run.py -start
python3 Run.py -t R4 10.5.5.7
python3 Run.py -aiigmp eth0
python3 Run.py -aiigmp eth1
python3 Run.py -aisr eth0
python3 Run.py -aisr eth1
python3 Run.py -v
