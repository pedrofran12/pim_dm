rm -rf MulticastRouting/
cp -rf /hosthome/Desktop/pim/ MulticastRouting/
cd MulticastRouting
pip-3.2 install --index-url=https://pypi.python.org/simple/ -r requirements.txt

python3 Server.py
