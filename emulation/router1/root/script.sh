rm -rf MulticastRouting/
cp -rf /hosthome/Desktop/pim/ MulticastRouting/
cd MulticastRouting
#pip-3.2 install --index-url=https://pypi.python.org/simple/ -r requirements.txt


tcpdump -i eth0 -w /hosthome/Desktop/test_pim/pim/TestResults/Router1_Source.pcap &
tcpdump -i eth1 -w /hosthome/Desktop/test_pim/pim/TestResults/Router1_Router2.pcap &
tcpdump -i eth2 -w /hosthome/Desktop/test_pim/pim/TestResults/Router1_Router3.pcap &
tcpdump -i eth3 -w /hosthome/Desktop/test_pim/pim/TestResults/Router1_Router4.pcap &

python3 Run.py -stop
python3 Run.py -start
python3 Run.py -t R1 10.5.5.7
python3 Run.py -aiigmp eth0
python3 Run.py -aiigmp eth1
python3 Run.py -aiigmp eth2
python3 Run.py -aiigmp eth3
python3 Run.py -aisr eth0
python3 Run.py -aisr eth1
python3 Run.py -aisr eth2
python3 Run.py -aisr eth3
python3 Run.py -v
