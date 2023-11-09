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

# XML-RPC related files
XMLRPCVER := 1.6
XMLRPCDIR := server

DESTDIR	:=
PREFIX  :=      /usr
DATADIR	:=	$(DESTDIR)/$(PREFIX)/share
LOADDIR	:=	loadsource

KLOAD	:=	$(LOADDIR)/linux-6.6.1.tar.xz
BLOAD	:=	$(LOADDIR)/dbench-4.0.tar.gz
LOADS	:=	$(KLOAD) $(BLOAD)

runit:
	[ -d $(HERE)/run ] || mkdir run
	$(PYTHON) rteval-cmd -D -L -v --workdir=$(HERE)/run --loaddir=$(HERE)/loadsource --duration=$(D) -f $(HERE)/rteval.conf -i $(HERE)/rteval $(EXTRA)

load:
	[ -d ./run ] || mkdir run
	$(PYTHON) rteval-cmd --onlyload -D -L -v --workdir=./run --loaddir=$(HERE)/loadsource -f $(HERE)/rteval/rteval.conf -i $(HERE)/rteval

sysreport:
	$(PYTHON) rteval-cmd -D -v --workdir=$(HERE)/run --loaddir=$(HERE)/loadsource --duration=$(D) -i $(HERE)/rteval --sysreport

clean:
	[ -f $(XMLRPCDIR)/Makefile ] && make -C $(XMLRPCDIR) clean || echo -n
	rm -f *~ rteval/*~ rteval/*.py[co] *.tar.bz2 *.tar.gz doc/*~ server/rteval-xmlrpc-*.tar.gz

realclean: clean
	[ -f $(XMLRPCDIR)/Makefile ] && make -C $(XMLRPCDIR) maintainer-clean || echo -n
	rm -rf run rpm

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

rteval-xmlrpc-$(XMLRPCVER).tar.gz :
	cd $(XMLRPCDIR) ;             \
	autoreconf --install ;           \
	./configure --prefix=$(PREFIX) ; \
	make distcheck
	cp $(XMLRPCDIR)/rteval-xmlrpc-$(XMLRPCVER).tar.gz $(HERE)/

rpm_prep:
	rm -rf rpm
	mkdir -p rpm/{BUILD,RPMS,SRPMS,SOURCES,SPECS}

rpms rpm: rpm_prep rtevalrpm loadrpm

rtevalrpm: rteval-$(VERSION).tar.bz2
	cp $^ rpm/SOURCES
	cp rteval.spec rpm/SPECS
	rpmbuild -ba --define "_topdir $(HERE)/rpm" rpm/SPECS/rteval.spec

rtevalsrpm: rteval-$(VERSION).tar.bz2
	cp $^ rpm/SOURCES
	cp rteval.spec rpm/SPECS
	rpmbuild -bs --define "_topdir $(HERE)/rpm" rpm/SPECS/rteval.spec


xmlrpcrpm: rteval-xmlrpc-$(XMLRPCVER).tar.gz
	cp rteval-xmlrpc-$(XMLRPCVER).tar.gz rpm/SOURCES/
	cp server/rteval-parser.spec rpm/SPECS/
	rpmbuild -ba --define "_topdir $(HERE)/rpm" rpm/SPECS/rteval-parser.spec

xmlsrpm: rteval-xmlrpc-$(XMLRPCVER).tar.gz
	cp rteval-xmlrpc-$(XMLRPCVER).tar.gz rpm/SOURCES/
	cp server/rteval-parser.spec rpm/SPECS/
	rpmbuild -bs --define "_topdir $(HERE)/rpm" rpm/SPECS/rteval-parser.spec

loadrpm:
	rm -rf rpm-loads
	mkdir -p rpm-loads/{BUILD,RPMS,SRPMS,SOURCES,SPECS}
	cp rteval-loads.spec rpm-loads/SPECS
	cp $(LOADS) rpm-loads/SOURCES
	rpmbuild -ba --define "_topdir $(HERE)/rpm-loads" rpm-loads/SPECS/rteval-loads.spec

rpmlint: rpms
	@echo "==============="
	@echo "running rpmlint"
	rpmlint -v $(shell find ./rpm -type f -name "*.rpm") 	 \
		$(shell find ./rpm-loads -type f -name "*.rpm")	 \
		$(shell find ./rpm/SPECS -type f -name "rteval*.spec") \
		$(shell find ./rpm-loads/SPECS -type f -name "rteval*.spec" )

help:
	@echo ""
	@echo "rteval Makefile targets:"
	@echo ""
	@echo "        runit:     do a short testrun locally [default]"
	@echo "        rpm:       run rpmbuild for all rpms"
	@echo "        rpmlint:   run rpmlint against all rpms/srpms/specfiles"
	@echo "        tarfile:   create the source tarball"
	@echo "        install:   install rteval locally"
	@echo "        clean:     cleanup generated files"
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
