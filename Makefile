install:
	pip install -r requirements.txt

run-dev:
	python src/main.py

test:
	python -m unittest discover tests
