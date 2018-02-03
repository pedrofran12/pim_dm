rm -rf test/
cp -rf /hosthome/PycharmProjects/RPC/ test/
cd test
pip-3.2 install --index-url=https://pypi.python.org/simple/ -r requirements.txt

python3 Client.py
