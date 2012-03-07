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

#include "XTree.hpp"

const int	XTree::MATCH = 0;
const int	XTree::NO_MATCH = -1;
const int	XTree::INSERT = -1;
const int	XTree::DELETE = -1;
const int	XTree::CHANGE = 1;
const int	XTree::NULL_NODE = -1;
const int	XTree::NO_CONNECTION = 1048576;

const int	XTree::_TOP_LEVEL_CAPACITY = 16384;
const int	XTree::_BOT_LEVEL_CAPACITY = 4096;
const int	XTree::_ROOT = 0;


XTree::XTree()
: _tagNames(256),
  _cdataTable(256)
{
	_topCap = _TOP_LEVEL_CAPACITY;
	_botCap = _BOT_LEVEL_CAPACITY;
	_initialize();
}

XTree::XTree(int topcap, int botcap)
: _tagNames(256),
  _cdataTable(256)
{
	_topCap = topcap;
	_botCap = botcap;
	_initialize();
}

XTree::~XTree()
{
	int	size = _elementIndex / _botCap;
	if (size >= 0)
	{
		for (int i = 0; i <= size; i++)
		{
			delete[] _valueIndex[i];
			delete[] _firstChild[i];
			delete[] _nextSibling[i];
			delete[] _childrenCount[i];
			delete[] _matching[i];
			delete[] _isAttribute[i];
			delete[] _hashValue[i];
		}
	}
	delete[] _firstChild;
	delete[] _nextSibling;
	delete[] _childrenCount;
	delete[] _valueIndex;
	delete[] _matching;
	delete[] _isAttribute;
	delete[] _hashValue;

	size = _valueCount / _botCap;
	for (int i = 0; i <= size; i++)
		delete[] _value[i];
	delete[] _value;
}

void XTree::_initialize()
{
	_firstChild	= new int*[_topCap];
	_nextSibling	= new int*[_topCap];
	_childrenCount	= new int*[_topCap];
	_valueIndex	= new int*[_topCap];
	_matching	= new int*[_topCap];
	_isAttribute	= new bool*[_topCap];
	_hashValue	= new unsigned long long*[_topCap];
	_value		= new string*[_topCap];

	_value[0]	= new string[_botCap];
	_elementIndex	= -1;
	_tagIndex	= -1;
	_valueCount	= _botCap - 1;
}

void XTree::_expand(int topid)
{
	_firstChild[topid]	= new int[_botCap];
	_nextSibling[topid]	= new int[_botCap];
	_childrenCount[topid]	= new int[_botCap];
	_valueIndex[topid]	= new int[_botCap];
	_matching[topid]	= new int[_botCap];
	_isAttribute[topid]	= new bool[_botCap];
	_hashValue[topid]	= new unsigned long long[_botCap];

	for (int i = 0; i < _botCap; i++)
	{
		_firstChild[topid][i]	= NULL_NODE;
		_nextSibling[topid][i]	= NULL_NODE;
		_childrenCount[topid][i]= 0;
		_matching[topid][i]	= MATCH;
		_valueIndex[topid][i]	= -1;
		_isAttribute[topid][i]	= false;
	}
}

int XTree::addElement(int pid, int lsid, string tagName)
{
	_elementIndex++;

	int	topid = _elementIndex / _botCap;
	int	botid = _elementIndex % _botCap;
	if (botid == 0)
		_expand(topid);

	// Check if we've got the element name
	hash_map <string, int, HashString>::const_iterator
		hit = _tagNames.find(tagName);
	if (hit != _tagNames.end())
	{
		int	id = hit->second;
		_valueIndex[topid][botid] = id;
	}
	else
	{
		_tagIndex++;
		_value[0][_tagIndex] = tagName;
		_tagNames[tagName] = _tagIndex;
		_valueIndex[topid][botid] = _tagIndex;
	}

	if (pid == NULL_NODE)
		return _elementIndex;

	int	ptopid = pid / _botCap;
	int	pbotid = pid % _botCap;
	// parent-child relation or sibling-sibling ralation
	if (lsid == NULL_NODE)
		_firstChild[ptopid][pbotid] = _elementIndex;
	else
		_nextSibling[lsid/_botCap][lsid%_botCap] = _elementIndex;

	// update children count
	_childrenCount[ptopid][pbotid]++;

	return _elementIndex;
}

int XTree::addText(int eid, int lsid, string text, unsigned long long value)
{
	_elementIndex++;

	int	topid = _elementIndex / _botCap;
	int	botid = _elementIndex % _botCap;
	if (botid == 0)
		_expand(topid);

	int	etopid = eid / _botCap;
	int	ebotid = eid % _botCap;
	if (lsid == NULL_NODE)
		_firstChild[etopid][ebotid] = _elementIndex;
	else
		_nextSibling[lsid/_botCap][lsid%_botCap] = _elementIndex;

	_childrenCount[etopid][ebotid]++;
	_hashValue[topid][botid] = value;

	_valueCount++;
	int	vtopid = _valueCount / _botCap;
	int	vbotid = _valueCount % _botCap;
	if (vbotid == 0)
		_value[vtopid] = new string[_botCap];

	_value[vtopid][vbotid] = text;
	_valueIndex[topid][botid] = _valueCount;

	return _elementIndex;
}

int XTree::addAttribute(int eid, int lsid, string name, string value,
			unsigned long long valuehash,
			unsigned long long attrhash)
{
	// attribute name first.
	int	aid = addElement(eid, lsid, name);

	// attribute value second.
	addText(aid, NULL_NODE, value, valuehash);

	// hash value third
	int	atopid = aid / _botCap;
	int	abotid = aid % _botCap;
	_isAttribute[atopid][abotid] = true;
	_hashValue[atopid][abotid] = attrhash;

	return aid;
}

void XTree::addHashValue(int eid, unsigned long long value)
{
	_hashValue[eid/_botCap][eid%_botCap] = value;
}

void XTree::addCDATA(int eid, size_t position)
{
	hash_map<int, vector<size_t> >::const_iterator
		hit = _cdataTable.find(eid);
	if (hit != _cdataTable.end())
	{
		vector<size_t>	poslist = hit->second;
		poslist.push_back(position);
		_cdataTable[eid] = poslist;
	}
	else
	{
		vector<size_t>	poslist;
		poslist.push_back(position);
		_cdataTable[eid] = poslist;
	}
}

void XTree::addMatching(int eid, int matchType, int matchNode)
{
	if (matchType == NO_MATCH)
		_matching[eid/_botCap][eid%_botCap] = NO_MATCH;
	else if (matchType == MATCH)
		_matching[eid/_botCap][eid%_botCap] = MATCH;
	else
		_matching[eid/_botCap][eid%_botCap] = matchNode + 1;
}

void XTree::getMatching(int eid, int &matchType, int &matchNode)
{
	int	mid = _matching[eid/_botCap][eid%_botCap];
	if (mid == NO_MATCH)
		matchType = NO_MATCH;
	else if (mid == MATCH)
		matchType = MATCH;
	else
	{
		matchType = CHANGE;
		matchNode = mid - 1;
	}
}

int XTree::getRoot()
{
	return _ROOT;
}

int XTree::getFirstChild(int eid)
{
	int	cid = _firstChild[eid/_botCap][eid%_botCap];
	while (cid > _ROOT)
	{
		int	ctopid = cid / _botCap;
		int	cbotid = cid % _botCap;
		if (_isAttribute[ctopid][cbotid])
			cid = _nextSibling[ctopid][cbotid];
		else
			return cid;
	}

	return NULL_NODE;
}

int XTree::getNextSibling(int eid)
{
	return _nextSibling[eid/_botCap][eid%_botCap];
}

int XTree::getFirstAttribute(int eid)
{
	int	aid = _firstChild[eid/_botCap][eid%_botCap];
	if ((aid > _ROOT) && (_isAttribute[aid/_botCap][aid%_botCap]))
		return aid;
	else
		return NULL_NODE;
}

int XTree::getNextAttribute(int aid)
{
	int	aid1 = _nextSibling[aid/_botCap][aid%_botCap];
	if ((aid1 > _ROOT) && (_isAttribute[aid1/_botCap][aid1%_botCap]))
		return aid1;
	else
		return NULL_NODE;
}

string XTree::getAttributeValue(int aid)
{
	int	cid = _firstChild[aid/_botCap][aid%_botCap];
	int	index = _valueIndex[cid/_botCap][cid%_botCap];
	if (index > _ROOT)
		return _value[index/_botCap][index%_botCap];
	else
		return NULL;
}

unsigned long long XTree::getHashValue(int eid)
{
	return _hashValue[eid/_botCap][eid%_botCap];
}

vector<size_t> XTree::getCDATA(int eid)
{
	hash_map<int, vector<size_t> >::const_iterator
		hit = _cdataTable.find(eid);
	if (hit != _cdataTable.end())
		return hit->second;
	else
	{
		vector<size_t>	a;
		return a;
	}
}

int XTree::getChildrenCount(int eid)
{
	return _childrenCount[eid/_botCap][eid%_botCap];
}

int XTree::getDecendentsCount(int eid)
{
	int	topid = eid / _botCap;
	int	botid = eid % _botCap;
	int	count = _childrenCount[topid][botid];
	if (count == 0)
		return 0;

	int	cid = _firstChild[topid][botid];
	while (cid > _ROOT)
	{
		count += getDecendentsCount(cid);
		cid = _nextSibling[cid/_botCap][cid%_botCap];
	}

	return count;
}

int XTree::getValueIndex(int eid)
{
	return _valueIndex[eid/_botCap][eid%_botCap];
}

string XTree::getValue(int index)
{
	return _value[index/_botCap][index%_botCap];
}

string XTree::getTag(int eid)
{
	int	index = _valueIndex[eid/_botCap][eid%_botCap];
	return	_value[0][index];
}

string XTree::getText(int eid)
{
	int	index = _valueIndex[eid/_botCap][eid%_botCap];
	return _value[index/_botCap][index%_botCap];
}

bool XTree::isElement(int eid)
{
	int	index = _valueIndex[eid/_botCap][eid%_botCap];
	if (index < _botCap)
		return true;
	else
		return false;
}

bool XTree::isLeaf(int eid)
{
	int	index = _valueIndex[eid/_botCap][eid%_botCap];
	if (index < _botCap)
		return false;
	else
		return true;
}

bool XTree::isAttribute(int eid)
{
	return _isAttribute[eid/_botCap][eid%_botCap];
}

int XTree::getNodeCount()
{
	return _elementIndex;
}

void XTree::dump()
{
	cout << "eid\tfirstC\tnextS\tattr?\tcCount\thash\tmatch\tvalue\n";
	for (int i = _ROOT; i <= _elementIndex; i++)
	{
		int	topid = i / _botCap;
		int	botid = i % _botCap;
		int	vid = _valueIndex[topid][botid];
		int	vtopid = vid / _botCap;
		int	vbotid = vid % _botCap;
		cout << i << "\t" << _firstChild[topid][botid] << "\t"
			<< _nextSibling[topid][botid] << "\t"
			<< _isAttribute[topid][botid] << "\t"
			<< _childrenCount[topid][botid] << "\t"
			<< _hashValue[topid][botid] << "\t"
			<< _matching[topid][botid] << "\t"
			<< _value[vtopid][vbotid] << endl;
	}
}

void XTree::dumpHash()
{
	cout << "hash table:" << _tagNames.size() << endl;
	hash_map<string, int, HashString>::const_iterator
		hit;// = _tagNames.begin();
	for(hit=_tagNames.begin(); hit != _tagNames.end(); hit++)
	{
		cout << hit->first << "\t" << hit->second << endl;
		//hit++;
	}
}
