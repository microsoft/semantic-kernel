name = $(shell grep title retry_decorator/__init__.py | cut -d "'" -f2)
ver = $(shell grep version retry_decorator/__init__.py| cut -d "'" -f2 )

tar:
	git archive --prefix="$(name)-$(ver)/" master | bzip2 --best > "$(name)-$(ver).tar.bz2"
