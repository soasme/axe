HERE = $(shell pwd)
VENV = $(HERE)/venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
TESTER = $(BIN)/py.test
INSTALL = $(BIN)/pip install -r requirements.txt

test:
	py.test tests

package:
	python setup.py sdist
