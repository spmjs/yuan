# Makefile for project yuan
.PHONY: clean-pyc clean-build docs

all: install
	@cp githooks/* .git/hooks/
	@chmod -R +x .git/hooks/

# Development
install:
	@pip install -r dev-reqs.txt

server:
	@python manager.py runserver


database:
	@python manager.py createdb

# translate
babel-extract:
	@pybabel extract -F babel.cfg -o messages.pot .

babel-init:
	@pybabel init -i messages.pot -d yuan/translations -l zh

babel-compile:
	@pybabel compile -d yuan/translations

babel-update: babel-extract
	@pybabel update -i messages.pot -d yuan/translations

# Common Task
clean: clean-build clean-pyc

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info


clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +

files := $(shell find . -name '*.py' ! -path "*__init__.py*" ! -path "*docs/*")
lint:
	@flake8 ${files} --ignore=E127

options =
testing:
	@nosetests ${options}

print-test:
	@$(MAKE) testing options=--nocapture

coverage:
	@rm -f .coverage
	@nosetests --with-cov --cov yuan tests/
	@rm .coverage

# Sphinx Documentation
docs:
	@$(MAKE) -C docs html
