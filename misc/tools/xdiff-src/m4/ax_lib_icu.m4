# SYNOPSIS
#
#   AX_LIB_ICU([minimum-version], [action-if-found], [action-if-not-found])
#
# DESCRIPTION
#
#   Tests for the presence of the ICU library (International Component for
#   Unicode), using icu-config.
#
#   If ICU (of the specified version) is found, the following variables are
#   defined as shell and autoconf output variables:
#
#     ICU_CPPFLAGS
#     ICU_CPPFLAGS_SEARCHPATH
#     ICU_CFLAGS
#     ICU_CXXFLAGS
#     ICU_LDFLAGS
#     ICU_LDFLAGS_SEARCHPATH
#     ICU_LIBS
#
#   and the following preprocessor define is set:
#
#     HAVE_ICU
#
# LAST MODIFICATION
#
#   2008-02-25
#
# COPYLEFT
#
#   Copyright (c) 2008 Peter Adolphs
#
#   Copying and distribution of this file, with or without
#   modification, are permitted in any medium without royalty provided
#   the copyright notice and this notice are preserved.

AC_DEFUN([AX_LIB_ICU], [
  # define configure parameter
  unset ax_lib_icu_path ax_lib_icu_config
  AC_ARG_WITH([icu],
    [AC_HELP_STRING(
      [--with-icu@<:@=ARG@:>@], dnl
      [use ICU library from a standard location (ARG=yes),
       from the specified location or icu-config binary (ARG=<path>),
       or disable it (ARG=no)
       @<:@ARG=yes@:>@ ])],
    [case "${withval}" in
       yes) ax_lib_icu="yes" ;;
       no)  ax_lib_icu="no" ;;
       *)   ax_lib_icu="yes"
            if test -d $withval ; then
              ax_lib_icu_path="$withval/bin"
            elif test -x $withval ; then
              ax_lib_icu_config=$withval
              ax_lib_icu_path=$(dirname $ax_lib_icu_config)
            else
              AC_MSG_ERROR([bad value ${withval} for --with-icu ])
            fi ;;
     esac],
    [ax_lib_icu="yes"])
  if test "x$ax_lib_icu_path" = "x" ; then
    ax_lib_icu_path=$PATH
  fi
  
  # check for icu-config
  if test "x$ax_lib_icu" = "xyes" ; then
    AC_PATH_PROG([ax_lib_icu_config], [icu-config], [""], [$ax_lib_icu_path])
    if test "x$ax_lib_icu_config" = "x" ; then
      ax_lib_icu="no"
      AC_MSG_WARN([ICU library requested but icu-config not found.])
    fi
  fi
  
  # check version
  if test "x$ax_lib_icu" = "xyes" && test "x$1" != "x" ; then
    AC_MSG_CHECKING([whether ICU version >= $1])
    ax_lib_icu_version=$($ax_lib_icu_config --version)
    if test $(expr $ax_lib_icu_version \>\= $1) = 1 ; then
      AC_MSG_RESULT([yes])
    else
      AC_MSG_RESULT([no])
      ax_lib_icu="no"
    fi
  fi
  
  # get various flags and settings
  # cf. Autoconf manual:
  # LDFLAGS: options as `-s' and `-L' affecting only the behavior of the linker
  # LIBS: `-l' options to pass to the linker
  unset ICU_CPPFLAGS ICU_CPPFLAGS_SEARCHPATH
  unset ICU_CFLAGS ICU_CXXFLAGS ICU_LDFLAGS ICU_LDFLAGS_SEARCHPATH ICU_LIBS
  if test "x$ax_lib_icu" = "xyes" ; then
    ICU_CPPFLAGS=$($ax_lib_icu_config --cppflags | sed -e s/#.*//)
    ICU_CPPFLAGS_SEARCHPATH=$($ax_lib_icu_config --cppflags-searchpath | sed -e s/#.*//)
    ICU_CFLAGS=$($ax_lib_icu_config --cflags | sed -e s/#.*//)
    ICU_CXXFLAGS=$($ax_lib_icu_config --cxxflags | sed -e s/#.*//)
    ICU_LDFLAGS=$($ax_lib_icu_config --ldflags | sed -e s/#.*//)
    ICU_LDFLAGS_SEARCHPATH=$($ax_lib_icu_config --ldflags-searchpath | sed -e s/#.*//)
    ICU_LIBS=$($ax_lib_icu_config --ldflags-system | sed -e s/#.*//)
    ICU_LIBS="$ICU_LIBS $($ax_lib_icu_config --ldflags-libsonly | sed -e s/#.*//)"
  fi
  
  ax_lib_icu_saved_CPPFLAGS=$CPPFLAGS
  ax_lib_icu_saved_CXXFLAGS=$CXXFLAGS
  ax_lib_icu_saved_LDFLAGS=$LDFLAGS
  ax_lib_icu_saved_LIBS=$LIBS
  CPPFLAGS="$ICU_CPPFLAGS $CPPFLAGS"
  CXXFLAGS="$ICU_CXXFLAGS $CXXFLAGS"
  LDFLAGS="$ICU_LDFLAGS $LDFLAGS"
  LIBS="$ICU_LIBS $LIBS"
  
  # checking header presence
  AC_CHECK_HEADERS([unicode/unistr.h], [], [ax_lib_icu="no"])
  
  # checking library functionality
  if test "x$ax_lib_icu" = "xyes" ; then
    AC_REQUIRE([AC_PROG_CXX])
    AC_LANG_PUSH([C++])
    AC_MSG_CHECKING([ICU library usability])
    AC_LINK_IFELSE(
      [AC_LANG_PROGRAM(
        [[@%:@include <unicode/unistr.h>]],
        [[ UnicodeString s=UNICODE_STRING("foo", 32); ]])],
      [AC_MSG_RESULT([yes])],
      [AC_MSG_RESULT([no]) ; ax_lib_icu="no"])
    AC_LANG_POP([C++])
  fi
  
  CPPFLAGS=$ax_lib_icu_saved_CPPFLAGS
  CXXFLAGS=$ax_lib_icu_saved_CXXFLAGS
  LDFLAGS=$ax_lib_icu_saved_LDFLAGS
  LIBS=$ax_lib_icu_saved_LIBS
  
  # final actions
  AC_SUBST([ICU_CPPFLAGS])
  AC_SUBST([ICU_CPPFLAGS_SEARCHPATH])
  AC_SUBST([ICU_CFLAGS])
  AC_SUBST([ICU_CXXFLAGS])
  AC_SUBST([ICU_LDFLAGS])
  AC_SUBST([ICU_LDFLAGS_SEARCHPATH])
  AC_SUBST([ICU_LIBS])
  if test "x$ax_lib_icu" = "xyes"; then
    # execute action-if-found (if any)
    AC_DEFINE(HAVE_ICU, [1], [define to 1 if ICU library is available])
    ifelse([$2], [], :, [$2])
  else
    # execute action-if-not-found (if any)
    ifelse([$3], [], :, [$3])
  fi
])

