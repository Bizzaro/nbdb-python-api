python -m venv venv
source ./test/venv/Scripts/activate
pip install -e .

cd ./test
python test.py
