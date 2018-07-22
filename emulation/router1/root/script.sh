rm -rf MulticastRouting/
cp -rf /hosthome/Desktop/pim/ MulticastRouting/
cd MulticastRouting

python3 Run.py -stop
python3 Run.py -start
python3 Run.py -t R1 10.0.0.5
python3 Run.py -ai eth0
python3 Run.py -v
