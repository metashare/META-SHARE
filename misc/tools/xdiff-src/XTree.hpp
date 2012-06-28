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

#ifndef	__XTREE__
#define	__XTREE__

#include "xdiff-config.h"
#include <iostream>
#include <string>
#ifdef HAVE_EXT_HASH_MAP
#include <ext/hash_map>
#else
#include <hash_map>
#endif
#include <vector>

using namespace __gnu_cxx;

class HashString
{
public:
	bool operator()(string const &str) const
	{
		return hash<char const *>()(str.c_str());
	}
};


/**
  * XTree provides the storage for input XML documents. Basically, an XML
  * document is parsed by a SAX parser and stored in an XTree.
  */
class XTree
{
public:

	static const int	MATCH, NO_MATCH, INSERT, DELETE, CHANGE;
	static const int	NULL_NODE, NO_CONNECTION;

	XTree();
	XTree(int topcap, int botcap);
	~XTree();

	// Start  -- methods for constructing a tree.

	/**
	  * Add a new element to the tree.
	  * @param	pid		parent id
	  * @param	lsid		left-side sibling id
	  * @param	tagName		element name
	  * @return	the element id in the tree.
	  */
	int addElement(int pid, int lsid, string tagName);

	// Add a text node.
	int addText(int eid, int lsid, string text, unsigned long long value);

	/**
	  * Add an attribute.
	  * @param	eid	element id
	  * @param	lsid	the sibling id on the left
	  * @param	name	attribute name
	  * @param	value	attribute value
	  * @param	valuehash	hash value of the value
	  * @param	attrhash	hash value of the entire attribute
	  * @return	the element id of the attribute
	  */
	int addAttribute(int eid, int lsid, string name, string value,
			 unsigned long long valuehash,
			 unsigned long long attrhash);

	// Add more information (hash value) to the tree.
	void addHashValue(int eid, unsigned long long value);

	/**
	  * Add a CDATA section (either a start or an end) to the CDATA
	  * hashtable, in which each entry should have an even number of
	  * position slots. This value is interpreted as a string.
	  * @param	eid		The text node id
	  * @param	position	the section tag position
	  */
	void addCDATA(int eid, size_t position);

	/**
	  * Add matching information.
	  * @param	eid		element id
	  * @param	matchType	match type
	  * @param	matchNode	matched element id
	  */
	void addMatching(int eid, int matchType, int matchNode = -1);
	// End  -- methods for constructing a tree.

	// Start -- methods for accessing a tree.
	// Get matching information.
	void getMatching(int eid, int &matchType, int &matchNode);

	int getRoot();

	int getFirstChild(int eid);

	int getNextSibling(int eid);

	int getFirstAttribute(int eid);

	int getNextAttribute(int aid);

	string getAttributeValue(int aid);

	unsigned long long getHashValue(int eid);

	/**
	  * Get the CDATA position list for a text node.
	  * @param	eid		The text node id
	  * @return	the position vector.
	  */
	vector<size_t> getCDATA(int eid);

	int getChildrenCount(int eid);

	int getDecendentsCount(int eid);

	int getValueIndex(int eid);

	string getTag(int eid);

	// Get the value of a leaf node using the value index
	string getValue(int index);

	// Get the value of a leaf node using the node id
	string getText(int eid);

	// Check if a node is an element node.
	bool isElement(int eid);

	// Check if a node is a leaf text node.
	bool isLeaf(int eid);

	// Check if a ndoe is an attribute node
	bool isAttribute(int eid);

	// Return the number of nodes in the tree.
	int getNodeCount();

	// End  -- methods for accessing a tree.
	// For testing purpose.
	void dump();
	void dumpHash();

private:

	static const int	_TOP_LEVEL_CAPACITY, _BOT_LEVEL_CAPACITY;
	static const int	_ROOT;

	int	_topCap, _botCap, _elementIndex, _tagIndex, _valueCount;
	int	**_firstChild, **_nextSibling, **_childrenCount;
	int	**_valueIndex, **_matching;
	bool	**_isAttribute;
	unsigned long long	**_hashValue;
	string	**_value;
	hash_map<string, int, HashString>	_tagNames;
	hash_map<int, vector<size_t> >	_cdataTable;

	void _initialize();
	void _expand(int topid);
};
#endif
