python -m venv venv
source ./test/venv/Scripts/activate
source ./test/venv/bin/activate
pip install -e .

cd ./test
python test.py
