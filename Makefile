.PHONY: install train test clean

install:
	pip install -e ".[dev]"

install-app:
	pip install -e ".[app]"
	cd app && npm install

train:
	python -m educast.experiments.runner --experiment all

train-one:
	python -m educast.experiments.runner --experiment $(EXP)

server:
	python -m educast.server

test:
	pytest tests/ -v

clean:
	rm -rf results/*.json results/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
