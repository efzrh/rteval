# SPDX-License-Identifier: GPL-2.0-or-later
HERE	:=	$(shell pwd)
ifneq (, $(wildcard /usr/bin/python3))
	PYTHON = python3
else
	PYTHON = python2
endif
PACKAGE :=	rteval
VERSION :=      $(shell $(PYTHON) -c "from rteval import RTEVAL_VERSION; print(RTEVAL_VERSION)")
D	:=	10

DESTDIR	:=
PREFIX  :=      /usr
DATADIR	:=	$(DESTDIR)/$(PREFIX)/share
LOADDIR	:=	loadsource

KLOAD	:=	$(LOADDIR)/linux-6.10.5.tar.xz
BLOAD	:=	$(LOADDIR)/dbench-4.0.tar.gz
LOADS	:=	$(KLOAD) $(BLOAD)

runit:
	[ -d $(HERE)/run ] || mkdir run
	$(PYTHON) rteval-cmd -D -L -v --workdir=$(HERE)/run --loaddir=$(HERE)/loadsource --duration=$(D) -f $(HERE)/rteval.conf -i $(HERE)/rteval $(EXTRA)

load:
	[ -d ./run ] || mkdir run
	$(PYTHON) rteval-cmd --onlyload -D -L -v --workdir=./run --loaddir=$(HERE)/loadsource -f $(HERE)/rteval/rteval.conf -i $(HERE)/rteval

sysreport:
	[ -d $(HERE)/run ] || mkdir run
	$(PYTHON) rteval-cmd -D -v --workdir=$(HERE)/run --loaddir=$(HERE)/loadsource --duration=$(D) -i $(HERE)/rteval --sysreport

clean:
	rm -f *~ rteval/*~ rteval/*.py[co] *.tar.bz2 *.tar.gz doc/*~

realclean: clean
	rm -rf run

install: install_loads install_rteval

install_rteval: installdirs
	if [ "$(DESTDIR)" = "" ]; then \
		$(PYTHON) setup.py install; \
	else \
		$(PYTHON) setup.py install --root=$(DESTDIR); \
	fi

install_loads:	$(LOADS)
	[ -d $(DATADIR)/rteval/loadsource ] || mkdir -p $(DATADIR)/rteval/loadsource
	for l in $(LOADS); do \
		install -m 644 $$l $(DATADIR)/rteval/loadsource; \
	done

installdirs:
	[ -d $(DATADIR)/rteval ] || mkdir -p $(DATADIR)/rteval

tarfile: rteval-$(VERSION).tar.bz2

rteval-$(VERSION).tar.bz2:
	$(PYTHON) setup.py sdist --formats=bztar --owner root --group root
	mv dist/rteval-$(VERSION).tar.bz2 .
	rmdir dist

help:
	@echo ""
	@echo "rteval Makefile targets:"
	@echo ""
	@echo "        runit:     do a short testrun locally [default]"
	@echo "        tarfile:   create the source tarball"
	@echo "        install:   install rteval locally"
	@echo "        clean:     cleanup generated files"
	@echo "        realclean: Same as clean plus directory run"
	@echo "        sysreport: do a short testrun and generate sysreport data"
	@echo "        tags:      generate a ctags file"
	@echo "        cleantags: remove the ctags file"
	@echo ""

.PHONY: tags
tags:
	ctags -R --extra=+fq --python-kinds=+cfmvi rteval-cmd rteval

.PHONY: cleantags
cleantags:
	rm -f tags
