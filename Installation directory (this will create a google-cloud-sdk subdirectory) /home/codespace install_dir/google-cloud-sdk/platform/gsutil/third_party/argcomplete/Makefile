test_deps:
	pip install .[test]

lint: test_deps
	./setup.py flake8

test: lint test_deps
	coverage run --source=argcomplete --omit=argcomplete/my_shlex.py ./test/test.py -v

init_docs:
	cd docs; sphinx-quickstart

docs:
	$(MAKE) -C docs html

install: clean
	pip install wheel
	python setup.py bdist_wheel
	pip install --upgrade dist/*.whl

clean:
	-rm -rf build dist
	-rm -rf *.egg-info

.PHONY: test test_deps docs install clean lint lint_deps

include common.mk
