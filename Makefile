.PHONY: test

test:
	docker build -t gd-test -f tests/Dockerfile .
	docker run --rm -v "$$PWD":/w -w /w gd-test python -m unittest discover -s tests -v
