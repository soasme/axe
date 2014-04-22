HERE = $(shell pwd)
VENV = $(HERE)/venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
TESTER = $(BIN)/py.test
INSTALL = $(BIN)/pip install -r requirements.txt
VTENV_OPTS ?= --distribute

$(PYTHON):
	virtualenv $(VTENV_OPTS) $(VENV)

init:
	virtualenv venv

test:
	$(TESTER) tests
