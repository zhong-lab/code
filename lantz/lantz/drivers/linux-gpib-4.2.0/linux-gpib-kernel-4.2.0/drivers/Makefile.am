# driver/Makefile.am
# copyright (C) 2003 by Frank Mori Hess
# email : fmhess@users.sourceforge.net
#
#   This Makefile.am is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.

GPIB_MODULE_SUBDIR = gpib
GPIB_ABS_MODULE_SUBDIR = @abs_srcdir@/$(GPIB_MODULE_SUBDIR)

EXTRA_DIST = $(GPIB_MODULE_SUBDIR)

-include $(top_srcdir)/util/linux_flags/flags

#ignore errors from kernel's make modules in all-local, to avoid failure of make install
#on nfs filesystem with root_squash
all-local:
	-$(MAKE) -C $(LINUX_SRCDIR) V=1 modules\
		CC="$(LINUX_CC) -I@abs_top_srcdir@ -I@abs_top_srcdir@/compat/include" \
		CONFIG_GPIB_ISA="$(ENABLE_ISA)" \
		SUBDIRS="$(GPIB_ABS_MODULE_SUBDIR)"

clean-local:
	$(MAKE) -C $(LINUX_SRCDIR) V=1 clean\
		CC="$(LINUX_CC) -I@abs_top_srcdir@ -I@abs_top_srcdir@/compat/include" \
		SUBDIRS="$(GPIB_ABS_MODULE_SUBDIR)"

install-data-hook:
	$(MAKE) -C $(LINUX_SRCDIR) V=1 modules_install\
		CC="$(LINUX_CC) -I@abs_top_srcdir@ -I@abs_top_srcdir@/compat/include" \
		SUBDIRS="$(GPIB_ABS_MODULE_SUBDIR)" INSTALL_MOD_DIR="gpib"
	$(DEPMOD) -a

#make sure compiled files, etc don't make it into distribution tarballs
dist-hook:
	-find $(distdir) \( -name '*.[oas]' -o -name '*.ko' -o -name core -o -name '.*.cmd' -o -name '*.mod.c' \
		-o -name '*.o.d' -o -name 'modules.order' \) -type f -exec $(RM) {} \;
	-find $(distdir) -depth -name '.tmp_versions' -type d -exec $(RM) -r \{\} \;
