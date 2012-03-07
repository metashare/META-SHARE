#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.61])
AC_INIT([xdiff], [0.9.6], [yuanwang@cs.wisc.edu])
AC_CONFIG_SRCDIR([xdiff-config.h.in])
AC_CONFIG_HEADERS([xdiff-config.h])
AC_CONFIG_AUX_DIR([aux-build])
AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE([1.7 foreign])

# Checks for programs.
AC_PROG_CXX
AC_PROG_CC
AC_PROG_INSTALL

# Checks for libraries.
# FIXME: Replace `main' with a function in `-lc':
AC_CHECK_LIB([c], [main])
# FIXME: Replace `main' with a function in `-lpthread':
AC_CHECK_LIB([pthread], [main])

# Checks for header files.
AC_CHECK_HEADERS([stdlib.h sys/time.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_HEADER_STDBOOL
AC_TYPE_SIZE_T

# Checks for library functions.
AC_FUNC_STRTOD
AC_CHECK_FUNCS([gettimeofday])

# hash_map (C++)
AC_LANG_PUSH([C++])

# Some autoconf macros change CPPFLAGS/CXXFLAGS/LDFLAGS/LIBS. Let's backup
# these variables in order to restore the defaults. (Optional libraries
# should compile without other optional libraries being present.)
savedCPPFLAGS=$CPPFLAGS
savedCXXFLAGS=$CXXFLAGS
savedLDFLAGS=$LDFLAGS
savedLIBS=$LIBS

# Define flop- and cheap-specific CPPFLAGS/CXXFLAGS/LDFLAGS/LIBS
# cf. Autoconf manual or ./configure --help for a description
unset XDIFFCPPFLAGS XDIFFCXXFLAGS XDIFFLDFLAGS XDIFFLIBS

AC_CHECK_HEADERS([hash_map],,
   [AC_CHECK_HEADERS([ext/hash_map],[]
   ,[AC_MSG_ERROR("No hash_map header found")],)])

# --------------------------------------------------------------------
# IBM ICU library.
# --------------------------------------------------------------------

AX_LIB_ICU([],
  [
    icu=yes
    export XDIFFCPPFLAGS="$ICU_CPPFLAGS_SEARCHPATH $XDIFFCPPFLAGS"
    export XDIFFLDFLAGS="$ICU_LDFLAGS_SEARCHPATH $XDIFFLDFLAGS"
    export XDIFFLIBS="$ICU_LIBS $XDIFFLIBS"
  ],
  [icu=no])
AM_CONDITIONAL(ICU, [test "x$icu" = "xyes"])

# --------------------------------------------------------------------
# XML support, i.e. Xerces C++ library.
# --------------------------------------------------------------------

XERCESCDIR=""
AC_ARG_WITH(xml,
  [AC_HELP_STRING([--with-xml@<:@=ARG@:>@],
    [use Xerces C++ library from a standard location (ARG=yes),
     from the specified location (ARG=<path>),
     or disable it (ARG=no).
     @<:@ARG=no@:>@ ])],
  [
    case "${withval}" in
        yes) xml="yes" ;;
        no)  xml="no" ;;
        *)   xml="yes"
             XERCESCDIR=${withval} ;;
    esac
  ],
  [xml="yes"])

if test "x$xml" = "xyes" && test "x${XERCESCDIR}" != "x" ; then
  if test -d "${XERCESCDIR}" ; then
    LDFLAGS="-L${XERCESCDIR}/lib $LDFLAGS"
  else
    AC_MSG_WARN([directory ${XERCESCDIR} not found for --with-xml; DISABLED])
    xml="no"
  fi
fi
if test "x$xml" = "xyes" ; then
  LDFLAGS="$ICU_LDFLAGS_SEARCHPATH $LDFLAGS"
  LIBS="$ICU_LIBS $LIBS"
  AC_CHECK_LIB([xerces-c], [main], [ xml="yes" ],
    [
      xml="no"
      AC_MSG_WARN([Xerces C++ library not found for --with-xml; DISABLED])
    ])
fi
if test "x$xml" = "xyes" ; then
  XDIFFCPPFLAGS="-I${XERCESCDIR}/include $XDIFFCPPFLAGS"
  XDIFFLDFLAGS="-L${XERCESCDIR}/lib $XDIFFLDFLAGS"
  XDIFFLIBS="-lxerces-c $XDIFFLIBS"
  AC_DEFINE(HAVE_XML, [1], [Enable XML input modes, using Xerces C++ library])
else
  AC_MSG_ERROR([Mandatory Xerces C++ library not found])
fi
AM_CONDITIONAL(XML, [test "x$xml" = "xyes"])
CPPFLAGS=$savedCPPFLAGS
CXXFLAGS=$savedCXXFLAGS
LDFLAGS=$savedLDFLAGS
LIBS=$savedLIBS

AC_SUBST(XDIFFCPPFLAGS)
AC_SUBST(XDIFFCXXFLAGS)
AC_SUBST(XDIFFLDFLAGS)
AC_SUBST(XDIFFLIBS)

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
