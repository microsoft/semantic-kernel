update:
	curl https://mkcert.org/generate/ | ./strip-non-ascii > certifi/cacert.pem

publish:
	python -m build
	twine upload --skip-existing --sign dist/*
