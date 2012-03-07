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

using namespace std;

#include "XParser.hpp"

bool		XParser::_setValidation = false;
bool		XParser::_setNameSpaces = true;
bool		XParser::_setSchemaSupport = true;
bool		XParser::_setSchemaFullSupport = false;
bool		XParser::_setNameSpacePrefixes = true;

const char*	XParser::_trimReject = " \t\n";

XParser::XParser()
{
	_parser = XMLReaderFactory::createXMLReader();
	_parser->setFeature(XMLUni::fgSAX2CoreValidation, _setValidation);
	_parser->setFeature(XMLUni::fgSAX2CoreNameSpaces, _setNameSpaces);
/*
	_parser->setFeature(XMLUni::fgXercesSchema, _setSchemaSupport);
	_parser->setFeature(XMLUni::fgXercesSchemaFullChecking, _setSchemaFullSupport);
*/
	_parser->setFeature(XMLUni::fgSAX2CoreNameSpacePrefixes, _setNameSpacePrefixes);

	_parser->setContentHandler(this);
	_parser->setErrorHandler(this);
	_parser->setLexicalHandler(this);

	for(int i = 0; i < _STACK_SIZE; i++)
	{
		_idStack[i] = 0;
		_lsidStack[i] = 0;
		_valueStack[i] = 0;
	}
	_stackTop = 0;
	_currentNodeID = XTree::NULL_NODE;
	_xtree = new XTree();
	_elementBuffer = string("");
}

XParser::~XParser()
{
	delete _parser;
}

XTree* XParser::parse(const char* uri)
{
	_idStack[_stackTop] = XTree::NULL_NODE;
	_readElement = false;

	try
	{
		_parser->parse(uri);
	}
	catch (const XMLException& e)
	{
		cerr << "File not found:\t" << uri << "\nException message:\n"
			<< e.getMessage() << endl;
		return NULL;
	}

	return _xtree;
}

void XParser::startElement(const XMLCh* const uri, const XMLCh* const local,
		  	   const XMLCh* const raw, const Attributes& attrs)
{
	// if text is mixed with elements.
	if (_elementBuffer.length() > 0)
	{
		string	text = _trim(_elementBuffer);
		if (text.length() > 0)
		{
			unsigned long long	value = XHash::hash(text);
			int	tid = _xtree->addText(_idStack[_stackTop],
						      _lsidStack[_stackTop],
						      text, value);
			_lsidStack[_stackTop] = tid;
			_currentNodeID = tid;
			_valueStack[_stackTop] += value;
		}
	}

	string local_s(XMLString::transcode(local));

//cout << "Add element " << _idStack[_stackTop] << "\t" << _lsidStack[_stackTop] << "\t" << local_s << endl;
	int	eid = _xtree->addElement(_idStack[_stackTop],
					 _lsidStack[_stackTop], local_s);
	// Update last sibling info.
	_lsidStack[_stackTop] = eid;

	// Push
	_stackTop++;
	_idStack[_stackTop] = eid;
	_currentNodeID = eid;
	_lsidStack[_stackTop] = XTree::NULL_NODE;
	_valueStack[_stackTop] = XHash::hash(local_s);

	// Take care of attributes
	if (attrs.getLength() > 0)
	{
		for (unsigned int i = 0; i < attrs.getLength(); i++)
		{
			string	name(XMLString::transcode(attrs.getQName(i)));
			unsigned long long	namehash = XHash::hash(name);

			unsigned long long	attrhash = namehash * namehash;
			string	value = "";
			char	*valueP = XMLString::transcode(attrs.getValue(i));
			if (valueP != NULL)
			{
				value = string(valueP);
				unsigned long long valuehash = XHash::hash(value);
				attrhash += valuehash * valuehash;
			}
			int	aid = _xtree->addAttribute(eid, _lsidStack[_stackTop], name, value, namehash, attrhash);

			_lsidStack[_stackTop] = aid;
			_currentNodeID = aid + 1;
			_valueStack[_stackTop] += attrhash * attrhash;
		}
	}

	_readElement = true;
	_elementBuffer = string("");

}

void XParser::characters(const XMLCh* const ch, const XMLSize_t length)
{
	char*	str = XMLString::transcode(ch);
	_elementBuffer.append(str);
	XMLString::release(&str);
}

void XParser::endElement(const XMLCh* const uri, const XMLCh* const local,
			 const XMLCh* const raw)
{
	if (_readElement)
	{
		if (_elementBuffer.length() > 0)
		{
			unsigned long long	value = XHash::hash(_elementBuffer);

			_currentNodeID = _xtree->addText(_idStack[_stackTop],
							 _lsidStack[_stackTop],
							 _elementBuffer, value);

			_valueStack[_stackTop] += value;
		}
		else	// an empty element
		{
			_currentNodeID = _xtree->addText(_idStack[_stackTop],
							 _lsidStack[_stackTop],
							 "", 0);
		}

		_readElement = false;
	}
	else	// mixed contents
	{
		if (_elementBuffer.length() > 0)
		{
			string	text = _trim(_elementBuffer);
			if (text.length() > 0)
			{
				unsigned long long	value = XHash::hash(text);
				_currentNodeID =
					_xtree->addText(_idStack[_stackTop],
							_lsidStack[_stackTop],
							text, value);
				_valueStack[_stackTop] += value;
			}
		}
	}

	_elementBuffer = string("");
	_xtree->addHashValue(_idStack[_stackTop], _valueStack[_stackTop]);
	_valueStack[_stackTop-1] += _valueStack[_stackTop] *
				    _valueStack[_stackTop];
	_lsidStack[_stackTop-1] = _idStack[_stackTop];

	// Pop
	_stackTop--;
}

// The lexical handler methods.
void XParser::startCDATA()
{
	int	textid = _currentNodeID + 1;
	string	text = _elementBuffer;
	_xtree->addCDATA(textid, text.length());
}

void XParser::endCDATA()
{
	int	textid = _currentNodeID + 1;
	string	text = _elementBuffer;
	_xtree->addCDATA(textid, text.length());
}

string XParser::_trim(const char* input)
{
	string	base(input);
	if (base.length() == 0)
		return string("");

	int	start = base.find_first_not_of(_trimReject);
	if (start < 0)
		return string("");

	int	end = base.find_last_not_of(_trimReject);
	return base.substr(start, end - start + 1);
}

string XParser::_trim(string input)
{
	if (input.length() == 0)
		return string("");

	int	start = input.find_first_not_of(_trimReject);
	if (start < 0)
		return string("");

	int	end = input.find_last_not_of(_trimReject);
	return input.substr(start, end - start + 1);
}

// For testing purpose.
/*
int main(int argc, char* args[])
{
	try
	{
		XMLPlatformUtils::Initialize();
	}
	catch (const XMLException& e)
	{
		cerr << "Error during initialization! :\n"
			<< e.getMessage() << endl;
		exit(1);
	}

	XParser	*parser = new XParser();
	XTree	*xtree = parser->parse(args[1]);

	xtree->dump();

	delete parser;
	delete xtree;
}
*/
