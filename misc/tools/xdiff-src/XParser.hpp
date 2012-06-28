/**
  * Copyright (c) 2001 - 2005
  * 	Yuan Wang. All rights reserved.
  *
  * Redistribution and use in source and binary forms, with or without
  * modification, are permitted provided that the following conditions
  * are met:
  * 1. Redistributions of source code must retain the above copyright
  * notice, this list of conditions and the following disclaimer.
  * 2. Redistributions in binary form must reproduce the above copyright
  * notice, this list of conditions and the following disclaimer in the
  * documentation and/or other materials provided with the distribution.
  * 3. Redistributions in any form must be accompanied by information on
  * how to obtain complete source code for the X-Diff software and any
  * accompanying software that uses the X-Diff software.  The source code
  * must either be included in the distribution or be available for no
  * more than the cost of distribution plus a nominal fee, and must be
  * freely redistributable under reasonable conditions.  For an executable
  * file, complete source code means the source code for all modules it
  * contains.  It does not include source code for modules or files that
  * typically accompany the major components of the operating system on
  * which the executable file runs.
  *
  * THIS SOFTWARE IS PROVIDED BY YUAN WANG "AS IS" AND ANY EXPRESS OR IMPLIED
  * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
  * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT,
  * ARE DISCLAIMED.  IN NO EVENT SHALL YUAN WANG BE LIABLE FOR ANY DIRECT,
  * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
  * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
  * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
  * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
  * IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
  * POSSIBILITY OF SUCH DAMAGE.
  *
  */

#ifndef	__XPARSER__
#define __XPARSER__

#include <string>

#include <xercesc/sax2/Attributes.hpp>
#include <xercesc/sax2/DefaultHandler.hpp>
#include <xercesc/sax2/SAX2XMLReader.hpp>
#include <xercesc/sax2/XMLReaderFactory.hpp>
#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/util/XMLString.hpp>

#include "XTree.hpp"
#include "XHash.hpp"

#define _STACK_SIZE 64

using namespace XERCES_CPP_NAMESPACE;

#if (XERCES_VERSION_MAJOR == 1)
typedef unsigned int XMLSize_t
#endif

/**
  * XParser parses an input XML document and constructs an XTree.
  * Note: this parser may generate incorrect result on characters whose
  * ASCII value is beyond 127.
  */
class XParser : public DefaultHandler
{
public:

	XParser();
	~XParser();

	/**
	  * Parse an XML document
	  * @param	uri	input XML document
	  * @return	the created XTree
	  */
	XTree* parse(const char* uri);

	// Document handler methods

	void startElement(const XMLCh* const uri, const XMLCh* const local,
			  const XMLCh* const raw, const Attributes& attrs);

	void characters(const XMLCh* const ch, const XMLSize_t length);

	void endElement(const XMLCh* const uri, const XMLCh* const local,
			const XMLCh* const raw);

	void startCDATA();

	void endCDATA();

private:

	static const char*	_feature_Validation;
	static const char*	_feature_NameSpaces;
	static const char*	_feature_SchemaSupport;
	static const char*	_feature_SchemaFullSupport;
	static const char*	_feature_NameSpacePrefixes;
	static bool		_setValidation, _setNameSpaces;
	static bool		_setSchemaSupport, _setSchemaFullSupport;
	static bool		_setNameSpacePrefixes;
	static const char*	_trimReject;

	SAX2XMLReader	*_parser;
	XTree		*_xtree;
	int		_idStack[_STACK_SIZE];
        int		_lsidStack[_STACK_SIZE]; // id and left sibling
	unsigned long long	_valueStack[_STACK_SIZE];
	int		_stackTop, _currentNodeID;
	bool		_readElement;
	string		_elementBuffer;

	/**
	  * Trim a string.
	  * @param	input	input string
	  * @return	a trimmed string
	  */
	string _trim(const char* input);
	string _trim(string input);
};

#endif
