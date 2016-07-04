# Tell aclocal where to find local and third-party M4 macros (aclocal >= 1.6)
ACLOCAL_AMFLAGS = -I m4

CPPFLAGS += @XDIFFCPPFLAGS@
CXXFLAGS += @XDIFFCXXFLAGS@
LDFLAGS += @XDIFFLDFLAGS@
LIBS += @XDIFFLIBS@

# Give me all warnings
AM_CXXFLAGS = -Wall

bin_PROGRAMS = xdiff

xdiff_SOURCES = XDiff.cpp XDiff.hpp XHash.cpp XHash.hpp XLut.cpp XLut.hpp \
		XParser.cpp XParser.hpp XTree.cpp XTree.hpp

