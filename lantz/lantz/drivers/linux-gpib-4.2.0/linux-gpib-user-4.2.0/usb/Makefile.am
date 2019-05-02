# Makefile.am
# copyright (C) 2004 by Frank Mori Hess
# email : fmhess@users.sourceforge.net
#
#   This Makefile.am is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.

SUBDIRS = agilent_82357a ni_usb_gpib
EXTRA_DIST = 99-gpib-generic.rules
UDEV_RULES_DIR = $(sysconfdir)/udev/rules.d

install-data-local: 99-gpib-generic.rules
	test -d $(DESTDIR)$(UDEV_RULES_DIR) && test -e $(DESTDIR)$(UDEV_RULES_DIR)/99-gpib-generic.rules ||\
		$(INSTALL_DATA) -D $(srcdir)/99-gpib-generic.rules $(DESTDIR)$(UDEV_RULES_DIR)/99-gpib-generic.rules

