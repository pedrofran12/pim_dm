rm -rf MulticastRouting/
cp -rf /hosthome/Desktop/pim_code/ MulticastRouting/
cd MulticastRouting
pip-3.2 install -r requirements.txt

python3 Run.py -stop
python3 Run.py -start
python3 Run.py -ai eth0
python3 Run.py -v
