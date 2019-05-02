# Makefile.am
# copyright (C) 2004 by Frank Mori Hess
# email : fmhess@users.sourceforge.net
#
#   This Makefile.am is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.

EXTRA_DIST = ni_usb_gpib.in ni_usb_gpib.usermap 99-ni_usb_gpib.rules.in
CLEANFILES = 99-ni_usb_gpib.rules ni_usb_gpib
HOTPLUG_USB_CONF_DIR=$(sysconfdir)/hotplug/usb
USB_FIRMWARE_DIR=$(datadir)/usb
UDEV_RULES_DIR=$(sysconfdir)/udev/rules.d

do_subst = $(SED) -e 's,[@]sbindir[@],$(sbindir),g'\
	-e 's,[@]datadir[@],$(datadir),g'\
	-e 's,[@]hotplug_usb_conf_dir[@],$(HOTPLUG_USB_CONF_DIR),g'

99-ni_usb_gpib.rules: 99-ni_usb_gpib.rules.in
	$(do_subst) < $(srcdir)/99-ni_usb_gpib.rules.in >99-ni_usb_gpib.rules

ni_usb_gpib: ni_usb_gpib.in
	$(do_subst) < $(srcdir)/ni_usb_gpib.in >ni_usb_gpib

install-data-local: 99-ni_usb_gpib.rules ni_usb_gpib
	test -e $(DESTDIR)$(HOTPLUG_USB_CONF_DIR)/ni_usb_gpib ||\
		$(INSTALL_SCRIPT) -D ni_usb_gpib $(DESTDIR)$(HOTPLUG_USB_CONF_DIR)/ni_usb_gpib
	test -e $(DESTDIR)$(HOTPLUG_USB_CONF_DIR)/ni_usb_gpib.usermap ||\
		$(INSTALL_DATA) -D $(srcdir)/ni_usb_gpib.usermap $(DESTDIR)$(HOTPLUG_USB_CONF_DIR)/ni_usb_gpib.usermap
	$(INSTALL) -d $(DESTDIR)$(USB_FIRMWARE_DIR)/ni_usb_gpib
	test -d $(DESTDIR)$(UDEV_RULES_DIR) && test -e $(DESTDIR)$(UDEV_RULES_DIR)/99-ni_usb_gpib.rules ||\
		$(INSTALL_DATA) -D 99-ni_usb_gpib.rules $(DESTDIR)$(UDEV_RULES_DIR)/99-ni_usb_gpib.rules
