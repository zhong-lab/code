
dnl Process this file with autoconf to produce a configure script.

AC_INIT([linux-gpib-kernel], [4.2.0])

AC_CONFIG_SRCDIR([drivers/gpib/sys/osfuncs.c])
AM_INIT_AUTOMAKE
AM_MAINTAINER_MODE
AC_CONFIG_MACRO_DIR([m4])

dnl create a config.h file (Automake will add -DHAVE_CONFIG_H)
AC_CONFIG_HEADERS([config.h])

AC_SUBST([VERSION])

[ISODATE=`date +%Y-%m-%d`]
AC_SUBST([ISODATE])

AC_CANONICAL_HOST

AC_ARG_ENABLE([isa],[  --enable-isa		Enable support for ISA cards in GPIB kernel drivers],
	[ENABLE_ISA=$enableval],[ENABLE_ISA="no"])
if test "$ENABLE_ISA" = "yes" ; then
	AC_DEFINE([GPIB_CONFIG_ISA],[1],[Define to enable ISA support in drivers])
fi
AC_SUBST([ENABLE_ISA])
AC_ARG_ENABLE([pcmcia],[  --enable-pcmcia	Enable support for PCMCIA cards in GPIB kernel drivers],
	[ENABLE_PCMCIA=$enableval],[ENABLE_PCMCIA="no"])
if test "$ENABLE_PCMCIA" = "yes" ; then
	AC_DEFINE([GPIB_CONFIG_PCMCIA],[1],[Define to enable pcmcia support in drivers])
fi
AC_ARG_ENABLE([driver-debug],[  --enable-driver-debug	Enable debug spam to console in GPIB kernel drivers],
	[ENABLE_DRIVER_SPAM=$enableval],[ENABLE_DRIVER_SPAM="no"])
if test "$ENABLE_DRIVER_SPAM" = "yes" ; then
	AC_DEFINE([GPIB_CONFIG_KERNEL_DEBUG],[1],[Define to enable debug spam to console in drivers])
fi

dnl check kernel source directory
AC_ARG_WITH([linux-srcdir],
	[  --with-linux-srcdir=DIR	location of Linux kernel source directory [[DIR=/lib/modules/$(uname -r)/build/]]],
	[LINUX_SRCDIR=$withval],[LINUX_SRCDIR=/lib/modules/$(uname -r)/build/])
if test "$LINUX_SRCDIR" = "no" ; then
	AC_MSG_WARN([A Linux kernel source directory is required to compile driver modules.  Use --with-linux-srcdir=DIR.])
fi
AC_SUBST([LINUX_SRCDIR])
AC_MSG_CHECKING([Linux kernel directory])
if [[ ! -d "$LINUX_SRCDIR" ]]; then
	AC_MSG_WARN([Linux kernel directory $LINUX_SRCDIR does not exist.  Specify using --with-linux-srcdir=DIR.])
fi
if [[ ! -f "$LINUX_SRCDIR/.config" ]]; then
	AC_MSG_WARN([Kernel source tree at $LINUX_SRCDIR is not configured.  Copy the
	appropriate configuration file to $LINUX_SRCDIR/.config and then run 'make oldconfig'
	in the kernel source directory.])
fi
AC_MSG_RESULT([ok])
dnl get compile flags for modules from linux kernel source tree
AC_MSG_CHECKING([Linux kernel compile flags])
FLAGDIR=$(pwd)/util/linux_flags
env LDFLAGS="" CFLAGS="" make --quiet -C ${LINUX_SRCDIR} V=1 SUBDIRS=${FLAGDIR} LINUXDIR=${LINUX_SRCDIR} modules > /dev/null
if [[ $? != 0 ]]; then
	AC_MSG_WARN([Failed to get compile flags from Linux kernel directory.])
fi
AC_MSG_RESULT([ok])

dnl Checks for programs.
AC_PATH_PROG([DEPMOD], [depmod], [true], [PATH:/sbin:/usr/sbin:/usr/local/sbin])
if test "$DEPMOD" = "true" ; then
	AC_MSG_WARN([unable to find the 'depmod' program.  Is it in your path?])
fi

AC_OUTPUT([\
	Makefile \
	drivers/Makefile \
]
)

