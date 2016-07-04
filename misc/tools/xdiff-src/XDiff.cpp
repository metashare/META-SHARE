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

#include "XDiff.hpp"

using namespace XERCES_CPP_NAMESPACE;

const string	XDiff::USAGE = "xdiff [-o|-g] [-p percent] input_xml1 input_xml2 diff_result\nOptions:\n  The default mode is \"-o -p 0.3\"\n  -o\tThe optimal mode, to get the minimum editing distance.\n  -g\tThe greedy mode, to find a difference quickly.\n  -p\tThe maximum change percentage allowed.\n\tDefault value: 1.0 for -o mode; 0.3 for -g mode.";

const int	XDiff::_CIRCUIT_SIZE = 2048;
const int	XDiff::_MATRIX_SIZE = 1024;
const int	XDiff::_ATTRIBUTE_SIZE = 1024;
const int	XDiff::_TEXT_SIZE = 1024;

/* You can use a different number for sampling here, as sqrt(n) is a safe
   one, though 3 works pretty well. */
const int	XDiff::_sampleCount = 3;
double		XDiff::_NO_MATCH_THRESHOLD = 0.3;
bool		XDiff::_oFlag = false;
bool		XDiff::_gFlag = false;

XDiff::XDiff() {}

int XDiff::diff(const char* input1, const char* input2, const char* output)
{
	struct timeval	*tv0 = new struct timeval;
	struct timeval	*tv1 = new struct timeval;
	struct timeval	*tv2 = new struct timeval;
	struct timeval	*tv3 = new struct timeval;
	struct timeval	*tv4 = new struct timeval;
	struct timezone	*tz = new struct timezone;

	// starting time.
	gettimeofday(tv0, tz);

	// parse the first file.
	XParser	*parser1 = new XParser();
	_xtree1 = parser1->parse(input1);
	delete parser1;
	gettimeofday(tv1, tz);

	// parse the second file.
	XParser	*parser2 = new XParser();
	_xtree2 = parser2->parse(input2);
	delete parser2;
	gettimeofday(tv2, tz);

	// check both root nodes.
	int	root1 = _xtree1->getRoot();
	int	root2 = _xtree2->getRoot();
	int 	retval = 0;
	if (_xtree1->getHashValue(root1) == _xtree2->getHashValue(root2))
	{
		cout << "No difference!" << endl;
		cout << "Execution time:\t\t" << _diffTime(tv0, tv2) << " s\n";
		cout << "Parsing " << input1 << ":\t"
			<< _diffTime(tv0, tv1) << " s\n";
		cout << "Parsing " << input2 << ":\t"
			<< _diffTime(tv1, tv2) << " s\n";
	}
	else
	{
		retval = 1;
		if (_xtree1->getTag(root1).compare(_xtree2->getValue(root2)) != 0)
		{
			cout << "The root is changed!" << endl;
			_xtree1->addMatching(root1, XTree::DELETE, root2);
			_xtree2->addMatching(root2, XTree::INSERT, root1);
		}
		else
		{
			_attrList1 = new int[_ATTRIBUTE_SIZE];
			_attrList2 = new int[_ATTRIBUTE_SIZE];
			_textList1 = new int[_TEXT_SIZE];
			_textList2 = new int[_TEXT_SIZE];
			_attrMatch = new bool[_ATTRIBUTE_SIZE];
			_textMatch1 = new bool[_TEXT_SIZE];
			_textMatch2 = new bool[_TEXT_SIZE];
			_attrHash = new unsigned long long[_ATTRIBUTE_SIZE];
			_textHash = new unsigned long long[_TEXT_SIZE];
			_attrTag = new string[_ATTRIBUTE_SIZE];
			_leastCostMatrix = new int*[_MATRIX_SIZE];
			_pathMatrix = new int*[_MATRIX_SIZE];
			_circuit = new int[_CIRCUIT_SIZE];
			for (int i = 0; i < _MATRIX_SIZE; i++)
			{
				_leastCostMatrix[i] = new int[_MATRIX_SIZE];
				_pathMatrix[i] = new int[_MATRIX_SIZE];
			}
			_xtree1->addMatching(root1, XTree::CHANGE, root2);
			_xtree2->addMatching(root2, XTree::CHANGE, root1);
			_seed = (unsigned int)(tv0->tv_usec & 0xffffffff);
			_xlut = new XLut((_xtree1->getNodeCount() > 0xffff) ||
					 (_xtree2->getNodeCount() > 0xffff));
			xdiff(root1, root2, false);
		}

		// after diffing.
		gettimeofday(tv3, tz);
		writeDiff(input1, output);
		gettimeofday(tv4, tz);

		cout << "Difference detected!" << endl;
		cout << "Execution time:\t\t" << _diffTime(tv0, tv4) << " s\n";
		cout << "Parsing " << input1 << ":\t"
			<< _diffTime(tv0, tv1) << " s\n";
		cout << "Parsing " << input2 << ":\t"
			<< _diffTime(tv1, tv2) << " s\n";
		cout << "Diffing:\t\t" << _diffTime(tv2, tv3) << " s\n";
		cout << "Writing diff:\t\t" << _diffTime(tv3, tv4) << " s\n";

		delete _xlut;
		delete[] _attrList1;
		delete[] _attrList2;
		delete[] _attrMatch;
		delete[] _attrHash;
		delete[] _attrTag;
		delete[] _circuit;
		for (int i = 0; i < _MATRIX_SIZE; i++)
		{
			delete[] _leastCostMatrix[i];
			delete[] _pathMatrix[i];
		}
		delete[] _leastCostMatrix;
		delete[] _pathMatrix;
	}

	delete tv0;
	delete tv1;
	delete tv2;
	delete tv3;
	delete tv4;
	delete tz;
	return retval;
}

XDiff::~XDiff()
{
	delete _xtree1;
	delete _xtree2;
}

void XDiff::xdiff(int pid1, int pid2, bool matchFlag)
{
	// diff attributes.
	int	attrCount1 = 0, attrCount2 = 0;
	int	attr1 = _xtree1->getFirstAttribute(pid1);
	while (attr1 != XTree::NULL_NODE)
	{
		_attrList1[attrCount1++] = attr1;
		attr1 = _xtree1->getNextAttribute(attr1);
	}
	int	attr2 = _xtree2->getFirstAttribute(pid2);
	while (attr2 != XTree::NULL_NODE)
	{
		_attrList2[attrCount2++] =  attr2;
		attr2 = _xtree2->getNextAttribute(attr2);
	}
	if (attrCount1 > 0)
	{
		if (attrCount2 > 0)
			diffAttributes(attrCount1, attrCount2);
		else
		{
			for (int i = 0; i < attrCount1; i++)
				_xtree1->addMatching(_attrList1[i],
						     XTree::NO_MATCH);
		}
	}
	else if (attrCount2 > 0) // attrCount1 == 0
	{
		for (int i = 0; i < attrCount2; i++)
			_xtree2->addMatching(_attrList2[i], XTree::NO_MATCH);
	}

	// Match element nodes.
	int	count1 = _xtree1->getChildrenCount(pid1) - attrCount1;
	int	count2 = _xtree2->getChildrenCount(pid2) - attrCount2;

	if ((count1 == 0) && (count2 == 0))
	{
	}
	else if (count1 == 0)
	{
		int	node2 = _xtree2->getFirstChild(pid2);
		_xtree2->addMatching(node2, XTree::NO_MATCH);
		for (int i = 1; i < count2; i++)
		{
			node2 = _xtree2->getNextSibling(node2);
			_xtree2->addMatching(attr2, XTree::NO_MATCH);
		}
	}
	else if (count2 == 0)
	{
		int	node1 = _xtree1->getFirstChild(pid1);
		_xtree1->addMatching(node1, XTree::NO_MATCH);
		for (int i = 0; i < count1; i++)
		{
			node1 = _xtree1->getNextSibling(node1);
			_xtree1->addMatching(node1, XTree::NO_MATCH);
		}
	}
	else if ((count1 == 1) && (count2 == 1))
	{
		int	node1 = _xtree1->getFirstChild(pid1);
		int	node2 = _xtree2->getFirstChild(pid2);

		if (_xtree1->getHashValue(node1) == _xtree2->getHashValue(node2))
			return;

		bool	isE1 = _xtree1->isElement(node1);
		bool	isE2 = _xtree2->isElement(node2);

		if (isE1 && isE2)
		{
			if (_xtree1->getTag(node1).compare(_xtree2->getTag(node2)) == 0)
			{
				_xtree1->addMatching(node1, XTree::CHANGE, node2);
				_xtree2->addMatching(node2, XTree::CHANGE, node1);
				xdiff(node1, node2, matchFlag);
			}
			else
			{
				_xtree1->addMatching(node1, XTree::NO_MATCH);
				_xtree2->addMatching(node2, XTree::NO_MATCH);
			}
		}
		else if (!isE1 && !isE2)
		{
			_xtree1->addMatching(node1, XTree::CHANGE, node2);
			_xtree2->addMatching(node2, XTree::CHANGE, node1);
		}
		else
		{
			_xtree1->addMatching(node1, XTree::NO_MATCH);
			_xtree2->addMatching(node2, XTree::NO_MATCH);
		}
	}
	else
	{
		int	*elements1 = new int[count1];
		int	*elements2 = new int[count2];
		int	elementCount1 = 0, textCount1 = 0;
		int	elementCount2 = 0, textCount2 = 0;

		int	child1 = _xtree1->getFirstChild(pid1);
		if (_xtree1->isElement(child1))
			elements1[elementCount1++] = child1;
		else
			_textList1[textCount1++] = child1;
		for (int i = 1; i < count1; i++)
		{
			child1 = _xtree1->getNextSibling(child1);
			if (_xtree1->isElement(child1))
				elements1[elementCount1++] = child1;
			else
				_textList1[textCount1++] = child1;
		}

		int	child2 = _xtree2->getFirstChild(pid2);
		if (_xtree2->isElement(child2))
			elements2[elementCount2++] = child2;
		else
			_textList2[textCount2++] = child2;
		for (int i = 1; i < count2; i++)
		{
			child2 = _xtree2->getNextSibling(child2);
			if (_xtree2->isElement(child2))
				elements2[elementCount2++] = child2;
			else
				_textList2[textCount2++] = child2;
		}

		// Match text nodes.
		if (textCount1 > 0)
		{
			if (textCount2 > 0)
				diffText(textCount1, textCount2);
			else
			{
				for (int i = 0; i < textCount1; i++)
					_xtree1->addMatching(_textList1[i],
							     XTree::NO_MATCH);
			}
		}
		else if (textCount2 > 0)	// textCount1 == 0
		{
			for (int i = 0; i < textCount2; i++)
				_xtree2->addMatching(_textList2[i],
						     XTree::NO_MATCH);
		}

		bool	*matched1 = new bool[elementCount1];
		bool	*matched2 = new bool[elementCount2];
		int	mcount = _matchFilter(elements1, elements2,
					      matched1, matched2,
					      elementCount1, elementCount2);

		if ((elementCount1 == mcount) &&
		    (elementCount2 == mcount))
		{
		}
		else if (elementCount1 == mcount)
		{
			for (int i = 0; i < elementCount2; i++)
			{
				if (!matched2[i])
					_xtree2->addMatching(elements2[i],
							     XTree::NO_MATCH);
			}
		}
		else if (elementCount2 == mcount)
		{
			for (int i = 0; i < elementCount1; i++)
			{
				if (!matched1[i])
					_xtree1->addMatching(elements1[i],
							     XTree::NO_MATCH);
			}
		}
		else
		{
			// Write the list of unmatched nodes.
			int	ucount1 = elementCount1 - mcount;
			int	ucount2 = elementCount2 - mcount;
			int	*unmatched1 = new int[ucount1];
			int	*unmatched2 = new int[ucount2];
			int	muc1 = 0, muc2 = 0;
			int	start = 0;

			while ((muc1 < ucount1) && (muc2 < ucount2))
			{
				for (; (start < elementCount1) && matched1[start]; start++);
				string	startTag = _xtree1->getTag(elements1[start]);
				int	uele1 = 0, uele2 = 0;
				muc1++;
				unmatched1[uele1++] = elements1[start];
				matched1[start++] = true;

				for (int i = start; (i < elementCount1) && (muc1 < ucount1); i++)
				{
					if (!matched1[i] && (startTag.compare(_xtree1->getTag(elements1[i])) == 0))
					{
						matched1[i] = true;
						muc1++;
						unmatched1[uele1++] = elements1[i];
					}
				}

				for (int i = 0; (i < elementCount2) && (muc2 < ucount2); i++)
				{
					if (!matched2[i] && (startTag.compare(_xtree2->getTag(elements2[i])) == 0))
					{
						matched2[i] = true;
						muc2++;
						unmatched2[uele2++] = elements2[i];
					}
				}

				if (uele2 == 0)
				{
					for (int i = 0; i < uele1; i++)
						_xtree1->addMatching(unmatched1[i], XTree::NO_MATCH);
				}
				else
				{
					if ((uele1 == 1) && (uele2 == 1))
					{
						_xtree1->addMatching(unmatched1[0], XTree::CHANGE, unmatched2[0]);
						_xtree2->addMatching(unmatched2[0], XTree::CHANGE, unmatched1[0]);
						xdiff(unmatched1[0],
					      unmatched2[0], matchFlag);
					}
					// To find minimal-cost matching between those unmatched elements (with the same tag name.
					else if (uele1 >= uele2)
					{
						if ((uele2 <= _sampleCount) ||
						    !_gFlag)
							matchListO(unmatched1, unmatched2, uele1, uele2, true, matchFlag);
						else
							matchList(unmatched1, unmatched2, uele1, uele2, true, matchFlag);
					}
					else
					{
						if ((uele1 <= _sampleCount) ||
						    !_gFlag)
							matchListO(unmatched2, unmatched1, uele2, uele1, false, matchFlag);
						else
							matchList(unmatched2, unmatched1, uele2, uele1, false, matchFlag);
					}
				}
			}

			if (muc1 < ucount1)
			{
				for (int i = start; i < elementCount1; i++)
				{
					if (!matched1[i])
						_xtree1->addMatching(elements1[i], XTree::NO_MATCH);
				}
			}
			else if (muc2 < ucount2)
			{
				for (int i = 0; i < elementCount2; i++)
				{
					if (!matched2[i])
						_xtree2->addMatching(elements2[i], XTree::NO_MATCH);
				}
			}

			delete[] unmatched1;
			delete[] unmatched2;
		}

		delete[] elements1;
		delete[] elements2;
		delete[] matched1;
		delete[] matched2;
	}
}

void XDiff::diffAttributes(int attrCount1, int attrCount2)
{
	if ((attrCount1 == 1) && (attrCount2 == 1))
	{
		int	a1 = _attrList1[0];
		int	a2 = _attrList2[0];
		if (_xtree1->getHashValue(a1) == _xtree2->getHashValue(a2))
			return;

		if (_xtree1->getTag(a1).compare(_xtree2->getTag(a2)) == 0)
		{
			_xtree1->addMatching(a1, XTree::CHANGE, a2);
			_xtree2->addMatching(a2, XTree::CHANGE, a1);
			_xtree1->addMatching(_xtree1->getFirstChild(a1),
					     XTree::CHANGE,
					     _xtree2->getFirstChild(a2));
			_xtree2->addMatching(_xtree2->getFirstChild(a2),
					     XTree::CHANGE,
					     _xtree1->getFirstChild(a1));
		}
		else
		{
			_xtree1->addMatching(a1, XTree::NO_MATCH);
			_xtree2->addMatching(a2, XTree::NO_MATCH);
		}
		return;
	}

	for (int i = 0; i < attrCount2; i++)
	{
		_attrHash[i] = _xtree2->getHashValue(_attrList2[i]);
		_attrTag[i] = _xtree2->getTag(_attrList2[i]);
		_attrMatch[i] = false;
	}

	int	matchCount = 0;
	for (int i = 0; i < attrCount1; i++)
	{
		int	attr1 = _attrList1[i];
		unsigned long long	ah1 = _xtree1->getHashValue(attr1);
		string	tag1 = _xtree1->getTag(attr1);

		bool	found = false;
		for (int j = 0; j < attrCount2; j++)
		{
			int	attr2 = _attrList2[j];
			if (_attrMatch[j])
				continue;
			else if (ah1 == _attrHash[j])
			{
				_attrMatch[j] = true;
				matchCount++;
				found = true;
				break;
			}
			else if (tag1.compare(_attrTag[j]) == 0)
			{
				_attrMatch[j] = true;
				matchCount++;

				_xtree1->addMatching(attr1, XTree::CHANGE, attr2);
				_xtree2->addMatching(attr2, XTree::CHANGE, attr1);
				_xtree1->addMatching(_xtree1->getFirstChild(attr1), XTree::CHANGE, _xtree2->getFirstChild(attr2));
				_xtree2->addMatching(_xtree2->getFirstChild(attr2), XTree::CHANGE, _xtree1->getFirstChild(attr1));

				found = true;
				break;
			}
		}

		if (!found)
			_xtree1->addMatching(attr1, XTree::NO_MATCH);
	}

	if (matchCount != attrCount2)
	{
		for (int i = 0; i < attrCount2; i++)
		{
			if (!_attrMatch[i])
				_xtree2->addMatching(_attrList2[i], XTree::NO_MATCH);
		}
	}
}

void XDiff::diffText(int textCount1, int textCount2)
{
	for (int i = 0; i < textCount1; i++)
		_textMatch1[i] = false;
	for (int i = 0; i < textCount2; i++)
	{
		_textMatch2[i] = false;
		_textHash[i] = _xtree2->getHashValue(_textList2[i]);
	}

	int	mcount = 0;
	for (int i = 0; i < textCount1; i++)
	{
		unsigned long long	hash1 = _xtree1->getHashValue(_textList1[i]);
		for (int j = 0; j < textCount2; j++)
		{
			if (!_textMatch2[j] && (hash1 == _textHash[j]))
			{
				_textMatch1[i] = true;
				_textMatch2[j] = true;
				mcount++;
				break;
			}
		}

		if (mcount == textCount2)
			break;
	}

	if ((mcount < textCount1) && (textCount1 <= textCount2))
	{
		for (int i = 0, j = 0;
		     (i < textCount1) && (mcount < textCount1); i++)
		{
			if (_textMatch1[i])
				continue;
			for (; _textMatch2[j]; j++);
			_xtree1->addMatching(_textList1[i], XTree::CHANGE,
					     _textList2[j]);
			_textMatch1[i] = true;
			_xtree2->addMatching(_textList2[j], XTree::CHANGE,
					     _textList1[i]);
			_textMatch2[j] = true;
			mcount++;
		}
	}
	else if ((mcount < textCount2) && (textCount2 < textCount1))
	{
		for (int i = 0, j = 0;
		     (i < textCount2) && (mcount < textCount2); i++)
		{
			if (_textMatch2[i])
				continue;
			for (; _textMatch1[j]; j++);
			_xtree2->addMatching(_textList2[i], XTree::CHANGE,
					     _textList1[j]);
			_textMatch2[i] = true;
			_xtree1->addMatching(_textList1[j], XTree::CHANGE,
					     _textList2[i]);
			_textMatch1[j] = true;
			mcount++;
		}
	}

	if (mcount < textCount1)
	{
		for (int i = 0; i < textCount1; i++)
		{
			if (!_textMatch1[i])
				_xtree1->addMatching(_textList1[i],
						     XTree::NO_MATCH);
		}
	}
	else if (mcount < textCount2)
	{
		for (int i = 0; i < textCount2; i++)
		{
			if (!_textMatch2[i])
				_xtree2->addMatching(_textList2[i],
						     XTree::NO_MATCH);
		}
	}
}

int XDiff::_matchFilter(int *elements1, int *elements2, bool *matched1,
			bool *matched2, int count1, int count2)
{
	unsigned long long *value1 = new unsigned long long[count1];
	unsigned long long *value2 = new unsigned long long[count2];

	for (int i = 0; i < count1; i++)
	{
		value1[i] = _xtree1->getHashValue(elements1[i]);
		matched1[i] = false;
	}
	for (int i = 0; i < count2; i++)
	{
		value2[i] = _xtree2->getHashValue(elements2[i]);
		matched2[i] = false;
	}

	int	mcount = 0;
	for (int i = 0; i < count2; i++)
		for (int j = 0; j < count1; j++)
		{
			if (!matched1[j] && !matched2[i] &&
			    (value1[j] == value2[i]))
			{
				matched1[j] = true;
				matched2[i] = true;
			    	mcount++;
				break;
			}
		}

	delete[]	value1;
	delete[]	value2;

	return mcount;
}

void XDiff::matchListO(int *nodes1, int *nodes2, int count1, int count2,
		       bool treeOrder, bool matchFlag)
{
	int	**distanceMatrix = new int*[count1+1];
	int	*matching1 = new int[count1];
	int	*matching2 = new int[count2];

	// insert cost.
	distanceMatrix[count1] = new int[count2+1];
	for (int i = 0; i < count2; i++)
		distanceMatrix[count1][i] = (treeOrder ? _xtree2->getDecendentsCount(nodes2[i]) : _xtree1->getDecendentsCount(nodes2[i])) + 1;

	for (int i = 0; i < count1; i++)
	{
		distanceMatrix[i] = new int[count2+1];
		int	deleteCost = (treeOrder ? _xtree1->getDecendentsCount(nodes1[i]) : _xtree2->getDecendentsCount(nodes1[i])) + 1;
		for (int j = 0; j < count2; j++)
		{
			int	dist;
			if (matchFlag)
				dist = treeOrder ? _xlut->get(nodes1[i], nodes2[j]) : _xlut->get(nodes2[j], nodes1[i]);
			else
			{
				dist = treeOrder ? distance(nodes1[i], nodes2[j], true, XTree::NO_CONNECTION) : distance(nodes2[j], nodes1[i], true, XTree::NO_CONNECTION);

				// the default mode.
				if (!_oFlag && (dist > 1) && (dist >= _NO_MATCH_THRESHOLD * (deleteCost + distanceMatrix[count1][j])))
					dist = XTree::NO_CONNECTION;
				if (dist < XTree::NO_CONNECTION)
				{
					if (treeOrder)
						_xlut->add(nodes1[i],
							   nodes2[j],
							   dist);
					else
						_xlut->add(nodes2[j],
							   nodes1[i],
							   dist);
				}
			}
			distanceMatrix[i][j] = dist;
		}
		// delete cost.
		distanceMatrix[i][count2] = deleteCost;
	}

	// compute the minimal cost matching.
	findMatching(count1, count2, distanceMatrix, matching1, matching2);

	for (int i = 0; i < count1; i++)
	{
		if (matching1[i] == XTree::NO_MATCH)
		{
			if (treeOrder)
				_xtree1->addMatching(nodes1[i], XTree::NO_MATCH);
			else
				_xtree2->addMatching(nodes1[i], XTree::NO_MATCH);
		}
		else
		{
			if (treeOrder)
				_xtree1->addMatching(nodes1[i], XTree::CHANGE,
						     nodes2[matching1[i]]);
			else
				_xtree2->addMatching(nodes1[i], XTree::CHANGE,
						     nodes2[matching1[i]]);
		}
	}

	for (int i = 0; i < count2; i++)
	{
		if (matching2[i] == XTree::NO_MATCH)
		{
			if (treeOrder)
				_xtree2->addMatching(nodes2[i], XTree::NO_MATCH);
			else
				_xtree1->addMatching(nodes2[i], XTree::NO_MATCH);
		}
		else
		{
			if (treeOrder)
				_xtree2->addMatching(nodes2[i], XTree::CHANGE,
						     nodes1[matching2[i]]);
			else
				_xtree1->addMatching(nodes2[i], XTree::CHANGE,
						     nodes1[matching2[i]]);
		}
	}

	for (int i = 0; i < count1; i++)
	{
		if (matching1[i] != XTree::NO_MATCH)
		{
			int	todo1 = nodes1[i];
			int	todo2 = nodes2[matching1[i]];
			if (treeOrder)
			{
				if (_xtree1->isElement(todo1) &&
				    _xtree2->isElement(todo2))
					xdiff(todo1, todo2, true);
			}
			else
			{
				if (_xtree1->isElement(todo2) &&
				    _xtree2->isElement(todo1))
					xdiff(todo2, todo1, true);
			}
		}
	}

	delete[]	matching1;
	delete[]	matching2;
	for (int i = 0; i <= count1; i++)
		delete[]	distanceMatrix[i];
	delete[]	distanceMatrix;
}

void XDiff::matchList(int *nodes1, int *nodes2, int count1, int count2,
		      bool treeOrder, bool matchFlag)
{
	int	*matching1 = new int[count1];
	int	*matching2 = new int[count2];
	for (int i = 0; i < count1; i++)
		matching1[i] = XTree::NO_MATCH;
	for (int i = 0; i < count2; i++)
		matching2[i] = XTree::NO_MATCH;

	if (matchFlag)
	{
		for (int i = 0; i < count1; i++)
		{
			for (int j = 0; j < count2; j++)
			{
				int	d = treeOrder ? _xlut->get(nodes1[i], nodes2[j]) : _xlut->get(nodes2[j], nodes1[i]);
				if (d != XTree::NO_CONNECTION)
				{
					matching1[i] = j;
					matching2[j] = i;
					break;
				}
			}
		}
	}
	else
	{
		int	scount1 = 0;
		int	scount2 = 0;
		int	matchingThreshold = 0;
		for (int i = 0; ((i < _sampleCount) && (scount2 < count2)); scount2++)
		{
			srand(_seed);
			_seed = rand();
			int	snode = (int)((long long)_seed * (count2 - scount2) / (RAND_MAX + 1)) + scount2;
			int	dist = XTree::NO_CONNECTION;
			int	bestmatch = XTree::NULL_NODE;
			for (int j = scount1; j < count1; j++)
			{
				int	d = treeOrder ? distance(nodes1[j], nodes2[snode], false, dist) : distance(nodes2[snode], nodes1[j], false, dist);
				if (d < dist)
				{
					dist = d;
					bestmatch = j;
					if (d == 1)
						break;
				}
			}

			int	deleteCost = (treeOrder ? _xtree2->getDecendentsCount(nodes2[snode]) : _xtree1->getDecendentsCount(nodes2[snode])) + 1;
			if ((dist > 1) &&
			    (dist > _NO_MATCH_THRESHOLD * deleteCost))
			{
				int	tmp = nodes2[snode];
				nodes2[snode] = nodes2[scount2];
				nodes2[scount2] = tmp;
			}
			else
			{
				int	tmp = nodes1[bestmatch];
				nodes1[bestmatch] = nodes1[scount1];
				nodes1[scount1] = tmp;
				tmp = nodes2[snode];
				nodes2[snode] = nodes2[scount2];
				nodes2[scount2] = tmp;

				if (treeOrder)
					_xlut->add(nodes1[scount1], nodes2[scount2], dist);
				else
					_xlut->add(nodes2[scount2], nodes1[scount1], dist);
				matching1[scount1] = scount2;
				matching2[scount2] = scount1;

				i++;
				scount1++;
				if (matchingThreshold < dist)
					matchingThreshold = dist;
			}
		}

		for (;scount2 < count2; scount2++)
		{
			int	dist = XTree::NO_CONNECTION;
			int	bestmatch = XTree::NO_MATCH;
			for (int i = scount1; i < count1; i++)
			{
				int	d = treeOrder ? distance(nodes1[i], nodes2[scount2], false, dist) : distance(nodes2[scount2], nodes1[i], false, dist);
				if (d <= matchingThreshold)
				{
					dist = d;
					bestmatch = i;
					break;
				}
				else if (d < dist)
				{
					dist = d;
					bestmatch = i;
				}
			}

			if (bestmatch != XTree::NO_MATCH)
			{
				int	tmp = nodes1[bestmatch];
				nodes1[bestmatch] = nodes1[scount1];
				nodes1[scount1] = tmp;

				if (treeOrder)
					_xlut->add(nodes1[scount1], nodes2[scount2], dist);
				else
					_xlut->add(nodes2[scount2], nodes1[scount1], dist);
				matching1[scount1] = scount2;
				matching2[scount2] = scount1;
				scount1++;
			}
		}
	}

	// Record matching
	for (int i = 0; i < count1; i++)
	{
		if (matching1[i] == XTree::NO_MATCH)
		{
			if (treeOrder)
				_xtree1->addMatching(nodes1[i], XTree::NO_MATCH);
			else
				_xtree2->addMatching(nodes1[i], XTree::NO_MATCH);
		}
		else
		{
			if (treeOrder)
				_xtree1->addMatching(nodes1[i], XTree::CHANGE,
						     nodes2[matching1[i]]);
			else
				_xtree2->addMatching(nodes1[i], XTree::CHANGE,
						     nodes2[matching1[i]]);
		}
	}

	for (int i = 0; i < count2; i++)
	{
		if (matching2[i] == XTree::NO_MATCH)
		{
			if (treeOrder)
				_xtree2->addMatching(nodes2[i], XTree::NO_MATCH);
			else
				_xtree1->addMatching(nodes2[i], XTree::NO_MATCH);
		}
		else
		{
			if (treeOrder)
				_xtree2->addMatching(nodes2[i], XTree::CHANGE,
						     nodes1[matching2[i]]);
			else
				_xtree1->addMatching(nodes2[i], XTree::CHANGE,
						     nodes1[matching2[i]]);
		}
	}

	for (int i = 0; i < count1; i++)
	{
		if (matching1[i] != XTree::NO_MATCH)
		{
			int	todo1 = nodes1[i];
			int	todo2 = nodes2[matching1[i]];
			if (treeOrder)
			{
				if (_xtree1->isElement(todo1) &&
				    _xtree2->isElement(todo2))
					xdiff(todo1, todo2, true);
			}
			else
			{
				if (_xtree1->isElement(todo2) &&
				    _xtree2->isElement(todo1))
					xdiff(todo2, todo1, true);
			}
		}
	}

	delete[]	matching1;
	delete[]	matching2;
}

int XDiff::distance(int eid1, int eid2, bool toRecord, int threshold)
{
	bool	isE1 = _xtree1->isElement(eid1);
	bool	isE2 = _xtree2->isElement(eid2);
	if (isE1 && isE2)
	{
		if (_xtree1->getTag(eid1).compare(_xtree2->getTag(eid2)) != 0)
			return XTree::NO_CONNECTION;
		else
		{
			int	dist = _xdiff(eid1, eid2, threshold);
			if (toRecord && (dist < XTree::NO_CONNECTION))
				_xlut->add(eid1, eid2, dist);
			return dist;
		}
	}
	else if (!isE1 && !isE2)
		return 1;
	else
		return XTree::NO_CONNECTION;
}

int XDiff::_xdiff(int pid1, int pid2, int threshold)
{
	int	dist = 0;

	// diff attributes.
	int	attrCount1 = 0, attrCount2 = 0;
	int	attr1 = _xtree1->getFirstAttribute(pid1);
	while (attr1 != XTree::NULL_NODE)
	{
		_attrList1[attrCount1++] = attr1;
		attr1 = _xtree1->getNextAttribute(attr1);
	}
	int	attr2 = _xtree2->getFirstAttribute(pid2);
	while (attr2 != XTree::NULL_NODE)
	{
		_attrList2[attrCount2++] =  attr2;
		attr2 = _xtree2->getNextAttribute(attr2);
	}

	if (attrCount1 == 0)
		dist = attrCount2 * 2;
	else if (attrCount2 == 0)
		dist = attrCount1 * 2;
	else
		dist = _diffAttributes(attrCount1, attrCount2);
	if (!_gFlag && (dist >= threshold))
		return XTree::NO_CONNECTION;

	// Match element nodes.
	int	count1 = _xtree1->getChildrenCount(pid1) - attrCount1;
	int	count2 = _xtree2->getChildrenCount(pid2) - attrCount2;

	if (count1 == 0)
	{
		int	node2 = _xtree2->getFirstChild(pid2);
		while (node2 != XTree::NULL_NODE)
		{
			dist += _xtree2->getDecendentsCount(node2) + 1;
			if (!_gFlag && (dist >= threshold))
				return XTree::NO_CONNECTION;
			node2 = _xtree2->getNextSibling(node2);
		}
	}
	else if (count2 == 0)
	{
		int	node1 = _xtree1->getFirstChild(pid1);
		while (node1 != XTree::NULL_NODE)
		{
			dist += _xtree1->getDecendentsCount(node1) + 1;
			if (!_gFlag && (dist >= threshold))
				return XTree::NO_CONNECTION;
			node1 = _xtree1->getNextSibling(node1);
		}
	}
	else if ((count1 == 1) && (count2 == 1))
	{
		int	node1 = _xtree1->getFirstChild(pid1);
		int	node2 = _xtree2->getFirstChild(pid2);

		if (_xtree1->getHashValue(node1) == _xtree2->getHashValue(node2))
			return dist;

		bool	isE1 = _xtree1->isElement(node1);
		bool	isE2 = _xtree2->isElement(node2);

		if (isE1 && isE2)
		{
			if (_xtree1->getTag(node1).compare(_xtree2->getTag(node2)) == 0)
				dist += _xdiff(node1, node2, threshold - dist);
			else
				dist += _xtree1->getDecendentsCount(node1) +
					_xtree2->getDecendentsCount(node2) + 2;
		}
		else if (!isE1 && !isE2)
			dist++;
		else
			dist += _xtree1->getDecendentsCount(node1) +
				_xtree2->getDecendentsCount(node2) + 2;
	}
	else
	{
		int	*elements1 = new int[count1];
		int	*elements2 = new int[count2];
		int	elementCount1 = 0, textCount1 = 0;
		int	elementCount2 = 0, textCount2 = 0;

		int     child1 = _xtree1->getFirstChild(pid1);
		if (_xtree1->isElement(child1))
			elements1[elementCount1++] = child1;
		else
			_textList1[textCount1++] = child1;
		for (int i = 1; i < count1; i++)
		{
			child1 = _xtree1->getNextSibling(child1);
			if (_xtree1->isElement(child1))
				elements1[elementCount1++] = child1;
			else
				_textList1[textCount1++] = child1;
		}

		int     child2 = _xtree2->getFirstChild(pid2);
		if (_xtree2->isElement(child2))
			elements2[elementCount2++] = child2;
		else
			_textList2[textCount2++] = child2;
		for (int i = 1; i < count2; i++)
		{
			child2 = _xtree2->getNextSibling(child2);
			if (_xtree2->isElement(child2))
				elements2[elementCount2++] = child2;
			else
				_textList2[textCount2++] = child2;
		}

		// Match text nodes.
		if (textCount1 == 0)
		{
			dist += textCount2;
		}
		else if (textCount2 == 0)
		{
			dist += textCount1;
		}
		else
			dist += _diffText(textCount1, textCount2);

		if (_gFlag && (dist >= threshold))
			return XTree::NO_CONNECTION;

		bool	*matched1 = new bool[elementCount1];
		bool	*matched2 = new bool[elementCount2];
		int	mcount = _matchFilter(elements1, elements2,
					      matched1, matched2,
					      elementCount1, elementCount2);

		if ((elementCount1 == mcount) &&
		    (elementCount2 == mcount))
		{
		}
		else if (elementCount1 == mcount)
		{
			for (int i = 0; i < elementCount2; i++)
			{
				if (!matched2[i])
				{
					dist += _xtree2->getDecendentsCount(elements2[i]) + 1;
					if (_gFlag && (dist >= threshold))
					{
						dist = XTree::NO_CONNECTION;
						break;
					}
				}
			}
		}
		else if (elementCount2 == mcount)
		{
			for (int i = 0; i < elementCount1; i++)
			{
				if (!matched1[i])
				{
					dist += _xtree1->getDecendentsCount(elements1[i]) + 1;
					if (_gFlag && (dist >= threshold))
					{
						dist = XTree::NO_CONNECTION;
						break;
					}
				}
			}
		}
		else //if ((count1 > mcount) && (count2 > mcount))
		{
			// Write the list of unmatched nodes.
			int	ucount1 = elementCount1 - mcount;
			int	ucount2 = elementCount2 - mcount;
			int	*unmatched1 = new int[ucount1];
			int	*unmatched2 = new int[ucount2];
			int	muc1 = 0, muc2 = 0, start = 0;

			while ((muc1 < ucount1) && (muc2 < ucount2))
			{
				for (; (start < elementCount1) && matched1[start]; start++);
				string	startTag = _xtree1->getTag(elements1[start]);
				int	uele1 = 0, uele2 = 0;
				muc1++;
				unmatched1[uele1++] = elements1[start];
				matched1[start++] = true;

				for (int i = start; (i < elementCount1) && (muc1 < ucount1); i++)
				{
					if (!matched1[i] && (startTag.compare(_xtree1->getTag(elements1[i])) == 0))
					{
						matched1[i] = true;
						muc1++;
						unmatched1[uele1++] = elements1[i];
					}
				}

				for (int i = 0; (i < elementCount2) && (muc2 < ucount2); i++)
				{
					if (!matched2[i] && (startTag.compare(_xtree2->getTag(elements2[i])) == 0))
					{
						matched2[i] = true;
						muc2++;
						unmatched2[uele2++] = elements2[i];
					}
				}

				if (uele2 == 0)
				{
					for (int i = 0; i < uele1; i++)
						dist += _xtree1->getDecendentsCount(unmatched1[i]);
				}
				else
				{
/*
					if ((uele1 == 1) && (uele2 == 1))
					{
						dist += _xdiff(unmatched1[0],
							       unmatched2[0],
							       threshold-dist);
					}
					// To find minimal-cost matching between those unmatched elements (with the same tag name.
					else if (uele1 >= uele2)
					*/
					if (uele1 >= uele2)
					{
						if ((uele2 <= _sampleCount) ||
						    !_gFlag)
							dist += _matchListO(unmatched1, unmatched2, uele1, uele2, true);
						else
							dist += _matchList(unmatched1, unmatched2, uele1, uele2, true, threshold - dist);
					}
					else
					{
						if ((uele1 <= _sampleCount) ||
						    !_gFlag)
							dist += _matchListO(unmatched2, unmatched1, uele2, uele1, false);
						else
							dist += _matchList(unmatched2, unmatched1, uele2, uele1, false, threshold - dist);
					}
				}

				if (_gFlag && (dist >= threshold))
				{
					dist = XTree::NO_CONNECTION;
					break;
				}
			}

			if (dist < XTree::NO_CONNECTION)
			{
				if (muc1 < ucount1)
				{
					for (int i = start; i < elementCount1; i++)
					{
						if (!matched1[i])
						{
							dist =+ _xtree1->getDecendentsCount(elements1[i]);
							if (_gFlag && (dist >= threshold))
							{
								dist = XTree::NO_CONNECTION;
								break;
							}
						}
					}
				}
				else if (muc2 < ucount2)
				{
					for (int i = 0; i < elementCount2; i++)
					{
						if (!matched2[i])
						{
							dist += _xtree2->getDecendentsCount(elements2[i]);
							if (_gFlag && (dist >= threshold))
							{
								dist = XTree::NO_CONNECTION;
								break;
							}
						}
					}
				}
			}

			delete[] unmatched1;
			delete[] unmatched2;
		}

		delete[] elements1;
		delete[] elements2;
		delete[] matched1;
		delete[] matched2;
	}

	if (!_gFlag || (dist < threshold))
		return dist;
	else
		return XTree::NO_CONNECTION;
}

int XDiff::_diffAttributes(int attrCount1, int attrCount2)
{
	if ((attrCount1 == 1) && (attrCount2 == 1))
	{
		int	a1 = _attrList1[0];
		int	a2 = _attrList2[0];
		if (_xtree1->getHashValue(a1) == _xtree2->getHashValue(a2))
			return 0;

		if (_xtree1->getTag(a1).compare(_xtree2->getTag(a2)) == 0)
			return 1;
		else
			return 2;
	}

	int	dist = 0;
	for (int i = 0; i < attrCount2; i++)
	{
		_attrHash[i] = _xtree2->getHashValue(_attrList2[i]);
		_attrTag[i] = _xtree2->getTag(_attrList2[i]);
		_attrMatch[i] = false;
	}

	int	matchCount = 0;
	for (int i = 0; i < attrCount1; i++)
	{
		int	attr1 = _attrList1[i];
		unsigned long long	ah1 = _xtree1->getHashValue(attr1);
		string	tag1 = _xtree1->getTag(attr1);

		bool	found = false;
		for (int j = 0; j < attrCount2; j++)
		{
			if (_attrMatch[j])
				continue;
			else if (ah1 == _attrHash[j])
			{
				_attrMatch[j] = true;
				matchCount++;
				found = true;
				break;
			}
			else if (tag1.compare(_attrTag[j]) == 0)
			{
				_attrMatch[j] = true;
				matchCount++;
				dist++;
				found = true;
				break;
			}
		}

		if (!found)
			dist += 2;
	}

	dist += (attrCount2 - matchCount) * 2;
	return dist;
}

int XDiff::_diffText(int textCount1, int textCount2)
{
	for (int i = 0; i < textCount2; i++)
	{
		_textMatch2[i] = false;
		_textHash[i] = _xtree2->getHashValue(_textList2[i]);
	}

	int	mcount = 0;
	for (int i = 0; i < textCount1; i++)
	{
		unsigned long long	hash1 = _xtree1->getHashValue(_textList1[i]);
		for (int j = 0; j < textCount2; j++)
		{
			if (!_textMatch2[j] && (hash1 == _textHash[j]))
			{
				_textMatch2[j] = true;
				mcount++;
				break;
			}
		}

		if (mcount == textCount2)
			break;
	}

	if (textCount1 >= textCount2)
		return textCount1 - mcount;
	else
		return textCount2 - mcount;
}

int XDiff::_matchListO(int *nodes1, int *nodes2, int count1, int count2,
		       bool treeOrder)
{
	int	**distanceMatrix = new int*[count1+1];
	int	*matching1 = new int[count1];
	int	*matching2 = new int[count2];

	// insert cost.
	distanceMatrix[count1] = new int[count2+1];
	for (int i = 0; i < count2; i++)
		distanceMatrix[count1][i] = (treeOrder ? _xtree2->getDecendentsCount(nodes2[i]) : _xtree1->getDecendentsCount(nodes2[i])) + 1;

	for (int i = 0; i < count1; i++)
	{
		distanceMatrix[i] = new int[count2+1];
		int	deleteCost = (treeOrder ? _xtree1->getDecendentsCount(nodes1[i]) : _xtree2->getDecendentsCount(nodes1[i])) + 1;
		for (int j = 0; j < count2; j++)
		{
			int	dist = treeOrder ? distance(nodes1[i], nodes2[j], true, XTree::NO_CONNECTION) : distance(nodes2[j], nodes1[i], true, XTree::NO_CONNECTION);

			// the default mode.
			if (!_oFlag && (dist > 1) &&
			    (dist < XTree::NO_CONNECTION) &&
			    (dist >= _NO_MATCH_THRESHOLD *
			     (deleteCost + distanceMatrix[count1][j])))
				dist = XTree::NO_CONNECTION;

			if (dist < XTree::NO_CONNECTION)
			{
				if (treeOrder)
					_xlut->add(nodes1[i], nodes2[j], dist);
				else
					_xlut->add(nodes2[j], nodes1[i], dist);
			}
			distanceMatrix[i][j] = dist;
		}
		// delete cost.
		distanceMatrix[i][count2] = deleteCost;
	}

	// compute the minimal cost matching.
	int	dist_value = findMatching(count1, count2, distanceMatrix,
					  matching1, matching2);

	delete[]	matching1;
	delete[]	matching2;
	for (int i = 0; i <= count1; i++)
		delete[]	distanceMatrix[i];
	delete[]	distanceMatrix;

	return dist_value;
}

int XDiff::_matchList(int *nodes1, int *nodes2, int count1, int count2,
		      bool treeOrder, int threshold)
{
	int	*matching1 = new int[count1];
	int	*matching2 = new int[count2];
	for (int i = 0; i < count1; i++)
		matching1[i] = XTree::NULL_NODE;
	for (int i = 0; i < count2; i++)
		matching2[i] = XTree::NULL_NODE;

	int	Distance = 0;
	int	scount1 = 0;
	int	scount2 = 0;
	int	matchingThreshold = 0;

	for (int i = 0; ((i < _sampleCount) && (scount2 < count2)); scount2++)
	{
		int	snode = rand() % (count2 - scount2) + scount2;
		int	dist = XTree::NO_CONNECTION;
		int	bestmatch = XTree::NULL_NODE;
		for (int j = scount1; j < count1; j++)
		{
			int	d = treeOrder ? distance(nodes1[j], nodes2[snode], false, threshold - Distance) : distance(nodes2[snode], nodes1[j], false, threshold - Distance);
			if (d < dist)
			{
				dist = d;
				bestmatch = j;
				if (d == 1)
					break;
			}
		}

		int	deleteCost = (treeOrder ? _xtree2->getDecendentsCount(nodes2[snode]) : _xtree1->getDecendentsCount(nodes2[snode])) + 1;

		if ((dist > 1) && (dist > _NO_MATCH_THRESHOLD * deleteCost))
		{
			int	tmp = nodes2[snode];
			nodes2[snode] = nodes2[scount2];
			nodes2[scount2] = tmp;
			Distance += deleteCost;
		}
		else
		{
			int	tmp = nodes1[bestmatch];
			nodes1[bestmatch] = nodes1[scount1];
			nodes1[scount1] = tmp;
			tmp = nodes2[snode];
			nodes2[snode] = nodes2[scount2];
			nodes2[scount2] = tmp;

			if (treeOrder)
				_xlut->add(nodes1[scount1], nodes2[scount2], dist);
			else
				_xlut->add(nodes2[scount2], nodes1[scount1], dist);
			matching1[scount1] = scount2;
			matching2[scount2] = scount1;

			i++;
			scount1++;
			if (matchingThreshold < dist)
				matchingThreshold = dist;
			Distance += dist;
		}

		if (Distance >= threshold)
		{
			delete[]	matching1;
			delete[]	matching2;
			return XTree::NO_CONNECTION;
		}
	}

	for (;scount2 < count2; scount2++)
	{
		int	deleteCost = (treeOrder ? _xtree2->getDecendentsCount(nodes2[scount2]) : _xtree1->getDecendentsCount(nodes2[scount2])) + 1;
		int	dist = XTree::NO_CONNECTION;
		int	bestmatch = XTree::NULL_NODE;
		for (int i = scount1; i < count1; i++)
		{
			int	d = treeOrder ? distance(nodes1[i], nodes2[scount2], false, threshold - Distance) : distance(nodes2[scount2], nodes1[i], false, threshold - Distance);
			if (d <= matchingThreshold)
			{
				dist = d;
				bestmatch = i;
				break;
			}
			else if ((d == 1) || (d < _NO_MATCH_THRESHOLD * dist))
			{
				dist = d;
				bestmatch = i;
			}
		}

		if (bestmatch == XTree::NO_MATCH)
		{
			Distance += deleteCost;
		}
		else
		{
			int	tmp = nodes1[bestmatch];
			nodes1[bestmatch] = nodes1[scount1];
			nodes1[scount1] = tmp;

			if (treeOrder)
				_xlut->add(nodes1[scount1], nodes2[scount2], dist);
			else
				_xlut->add(nodes2[scount2], nodes1[scount1], dist);

			matching1[scount1] = scount2;
			matching2[scount2] = scount1;
			scount1++;
			Distance += dist;
		}

		if (Distance >= threshold)
		{
			delete[]	matching1;
			delete[]	matching2;
			return XTree::NO_CONNECTION;
		}
	}

	for (int i = 0; i < count1; i++)
	{
		if (matching1[i] == XTree::NO_MATCH)
		{
			Distance += (treeOrder ? _xtree1->getDecendentsCount(nodes1[i]) : _xtree2->getDecendentsCount(nodes1[i])) + 1;
			if (Distance >= threshold)
			{
				delete[]	matching1;
				delete[]	matching2;
				return XTree::NO_CONNECTION;
			}
		}
	}

	delete[]	matching1;
	delete[]	matching2;
	return Distance;
}

int XDiff::findMatching(int count1, int count2, int** dist,
			int* matching1, int* matching2)
{
	if (count1 == 1)
	{
		// count2 == 1
		if (dist[0][0] < XTree::NO_CONNECTION)
		{
			matching1[0] = 0;
			matching2[0] = 0;
		}
		else
		{
			matching1[0] = XTree::DELETE;
			matching2[0] = XTree::DELETE;
		}

		return dist[0][0];
	}
	else if (count2 == 1)
	{
		int	distance = 0;
		int	mate = 0;
		int	mindist = XTree::NO_CONNECTION;
		matching2[0] = XTree::DELETE;

		for (int i = 0; i < count1; i++)
		{
			matching1[i] = XTree::DELETE;
			if (mindist > dist[i][0])
			{
				mindist = dist[i][0];
				mate = i;
			}

			// Suppose we delete every node on list1.
			distance += dist[i][1];
		}

		if (mindist < XTree::NO_CONNECTION)
		{
			matching1[mate] = 0;
			matching2[0] = mate;
			distance += mindist - dist[mate][1];
		}
		else
		{
			// Add the delete cost of the single node on list2.
			distance += dist[count1][0];
		}

		return distance;
	}
	else if ((count1 == 2) && (count2 == 2))
	{
		int	distance1 = dist[0][0] + dist[1][1];
		int	distance2 = dist[0][1] + dist[1][0];
		if (distance1 < distance2)
		{
			if (dist[0][0] < XTree::NO_CONNECTION)
			{
				matching1[0] = 0;
				matching2[0] = 0;
				distance1 = dist[0][0];
			}
			else
			{
				matching1[0] = XTree::DELETE;
				matching2[0] = XTree::DELETE;
				distance1 = dist[0][2] + dist[2][0];
			}

			if (dist[1][1] < XTree::NO_CONNECTION)
			{
				matching1[1] = 1;
				matching2[1] = 1;
				distance1 += dist[1][1];
			}
			else
			{
				matching1[1] = XTree::DELETE;
				matching2[1] = XTree::DELETE;
				distance1 += dist[1][2] + dist[2][1];
			}

			return distance1;
		}
		else
		{
			if (dist[0][1] < XTree::NO_CONNECTION)
			{
				matching1[0] = 1;
				matching2[1] = 0;
				distance2 = dist[0][1];
			}
			else
			{
				matching1[0] = XTree::DELETE;
				matching2[1] = XTree::DELETE;
				distance2 = dist[0][2] + dist[2][1];
			}

			if (dist[1][0] < XTree::NO_CONNECTION)
			{
				matching1[1] = 0;
				matching2[0] = 1;
				distance2 += dist[1][0];
			}
			else
			{
				matching1[1] = XTree::DELETE;
				matching2[0] = XTree::DELETE;
				distance2 += dist[1][2] + dist[2][0];
			}

			return distance2;
		}
	}
	else
	{
		return optimalMatching(count1, count2, dist,
				       matching1, matching2);
	}
}

int XDiff::optimalMatching(int count1, int count2, int** dist,
			   int* matching1, int* matching2)
{
	// Initialize matching.
	// Initial guess will be pair-matching between two lists.
	// Others will be insertion or deletion
	for (int i = 0; i < count2; i++)
		matching1[i] = i;
	for (int i = count2; i < count1; i++)
		matching1[i] = XTree::DELETE;

	// Three artificial nodes: "start", "end" and "delete".
	int count = count1 + count2 + 3;

	// Initialize least cost matrix and path matrix.
	// Both have been initialized at the very beginning.

	// Start algorithm.
	while (true)
	{
		// Construct least cost matrix.
		constructLCM(dist, matching1, count1, count2);

		// Initialize path matrix.
		for (int i = 0; i < count; i++)
			for (int j = 0; j < count; j++)
				_pathMatrix[i][j] = i;

		// Search negative cost circuit.
		int	clen = searchNCC(count);
		if (clen > 0)
		{
			// Modify matching.
			for (int i = 0, next = 0; i < clen - 1; i++)
			{
				int	n1 = _circuit[next];
				next = _circuit[next+1];
				// Node in node list 1.
				if ((n1 > 0) && (n1 <= count1))
				{
					int	nid1 = n1 - 1;
					int	nid2 = _circuit[next] - count1 - 1;
					if (nid2 == count2)
						nid2 = XTree::DELETE;

					matching1[nid1] = nid2;
				}
			}
		}
		else // Stop.
			break;
	}

	int	distance = 0;
	// Suppose all insertion on list2
	for (int i = 0; i < count2; i++)
	{
		matching2[i] = XTree::INSERT;
		distance += dist[count1][i];
	}

	// update distance by looking at matching pairs.
	for (int i = 0; i < count1; i++)
	{
		int	mmm = matching1[i];
		if (mmm == XTree::DELETE)
			distance += dist[i][count2];
		else
		{
			matching2[mmm] = i;
			distance += dist[i][mmm] -
				    dist[count1][mmm];
		}
	}

	return distance;
}

void XDiff::constructLCM(int** costMatrix, int* matching,
			 int nodeCount1, int nodeCount2)
{
	// Three artificial nodes: "start", "end" and "delete".
	int nodeCount = nodeCount1 + nodeCount2 + 3;

	// Initialize.
	for (int i = 0; i < nodeCount; i++)
	{
		for (int j = 0; j < nodeCount; j++)
		_leastCostMatrix[i][j] = XTree::NO_CONNECTION;

		// self.
		_leastCostMatrix[i][i] = 0;
	}

	// Between start node and nodes in list 1.
	// Start -> node1 = Infinity; node1 -> Start = -0.
	for (int i = 0; i < nodeCount1; i++)
		_leastCostMatrix[i+1][0] = 0;

	// Between nodes in list2 and the end node.
	// Unless matched (later), node2 -> end = 0;
	// end -> node2 = Infinity.
	for (int i = 0; i < nodeCount2; i++)
		_leastCostMatrix[i+nodeCount1+1][nodeCount-1] = 0;

	int deleteCount = 0;

	// Between nodes in list1 and nodes in list2.
	// For matched, node1 -> node2 = Infinity;
	// node2 -> node1 = -1 * distance
	// For unmatched, node1 -> node2 = distance;
	// node2 -> node1 = Infinity
	for (int i = 0; i < nodeCount1; i++)
	{
		int node1 = i + 1;
		int node2;

		// According to cost matrix.
		for (int j = 0; j < nodeCount2; j++)
		{
			node2 = j + nodeCount1 + 1;
			_leastCostMatrix[node1][node2] = costMatrix[i][j];
		}

		// According to matching.
		if (matching[i] == XTree::DELETE)
		{
			deleteCount++;

			// node1 -> Delete = Infinity;
			// Delete -> node1 = -1 * DELETE_COST
			_leastCostMatrix[nodeCount-2][node1] = -1 * costMatrix[i][nodeCount2];
		}
		else
		{
			node2 = matching[i] + nodeCount1 + 1;

			// Between node1 and node2.
			_leastCostMatrix[node1][node2] = XTree::NO_CONNECTION;
			_leastCostMatrix[node2][node1] = costMatrix[i][matching[i]] * -1;

			// Between node1 and delete.
			_leastCostMatrix[node1][nodeCount-2] = costMatrix[i][nodeCount2];

			// Between node2 and end.
			_leastCostMatrix[node2][nodeCount-1] = XTree::NO_CONNECTION;
			_leastCostMatrix[nodeCount-1][node2] = costMatrix[nodeCount1][matching[i]];
		}
	}

	// Between the "Delete" and the "End".
	// If delete all, delete -> end = Infinity; end -> delete = 0.
	if (deleteCount == nodeCount1)
		_leastCostMatrix[nodeCount-1][nodeCount-2] = 0;
	// if no delete, delete -> end = 0; end -> delete = Infinity.
	else if (deleteCount == 0)
		_leastCostMatrix[nodeCount-2][nodeCount-1] = 0;
	// else, both 0;
	else
	{
		_leastCostMatrix[nodeCount-2][nodeCount-1] = 0;
		_leastCostMatrix[nodeCount-1][nodeCount-2] = 0;
	}
}

int XDiff::searchNCC(int nodeCount)
{
	for (int k = 0; k < nodeCount; k++)
	{
	    for (int i = 0; i < nodeCount; i++)
	    {
		if ((i != k) &&
		    (_leastCostMatrix[i][k] != XTree::NO_CONNECTION))
		{
		    for (int j = 0; j < nodeCount; j++)
		    {
			if ((j != k) &&
			    (_leastCostMatrix[k][j] != XTree::NO_CONNECTION))
			{
			    int	less = _leastCostMatrix[i][k] +
				       _leastCostMatrix[k][j];
			    if (less < _leastCostMatrix[i][j])
			    {
				_leastCostMatrix[i][j] = less;
				_pathMatrix[i][j] = k;

				// Found!
			       	if ((i == j) && (less < 0))
				{
				    int	clen = 0; // the length of the circuit.

				    // Locate the circuit.
				    //circuit.addElement(new Integer(i));
				    _circuit[0] = i;
				    _circuit[1] = 2;

				    //circuit.addElement(new Integer(pathMatrix[i][i]));
				    _circuit[2] = _pathMatrix[i][i];
				    _circuit[3] = 4;

				    //circuit.addElement(new Integer(i));
				    _circuit[4] = i;
				    _circuit[5] = -1;

				    clen = 3;

				    bool	finish;

				    do
				    {
					finish = true;
					for (int cit = 0, n = 0; cit < clen - 1; cit++)
					{
					    int	left = _circuit[n];
					    int	next = _circuit[n+1];
					    int	right = (next == -1)? -1 : _circuit[next];

					    //int middle = pathMatrix[circuit[n-1]][circuit[n]];
					    int	middle = _pathMatrix[left][right];

					    if (middle != left)
					    {
						//circuit.insert( cit, middle );
						_circuit[clen*2] = middle;
						_circuit[clen*2+1] = next;
						_circuit[n+1] = clen*2;
						clen++;

						finish = false;
						break;
					    }
					    n = next;
					}
				    } while (!finish);

				    return clen;
				}
			    }
			}
		    }
		}
	    }
	}
	return 0;
}

void XDiff::writeDiff(const char* input, const char* output)
{
	ifstream	in(input);
	ofstream	out(output, ios::out|ios::trunc);

	int	root1 = _xtree1->getRoot();
	int	root2 = _xtree2->getRoot();
	// the header
	// XXX <root > is valid and should be treated as <root>;
	// < root> is NOT valid, so use <root as the comparison key.
	string	rootTag = "<" + _xtree1->getTag(root1);
	string	line;
	while (getline(in, line))
	{
		if (line.find(rootTag) != string::npos)
			break;
		out << line << endl;
	}
	in.close();

	int	matchType, matchNode;
	_xtree1->getMatching(root1, matchType, matchNode);
	if (matchType == XTree::DELETE)
	{
		writeDeleteNode(out, root1);
		writeInsertNode(out, root2);
	}
	else
		writeDiffNode(out, root1, root2);

	out.close();
}

void XDiff::writeDeleteNode(ofstream &out, int node)
{
	if (_xtree1->isElement(node))
	{
		string	tag = _xtree1->getTag(node);
		out << "<" << tag;

		// Attributes.
		int	attr = _xtree1->getFirstAttribute(node);
		while (attr > 0)
		{
			string	atag = _xtree1->getTag(attr);
			string	value = _xtree1->getAttributeValue(attr);
			out << " " << atag << "=\"" << value << "\"";
			attr = _xtree1->getNextAttribute(attr);
		}

		// Child nodes.
		int	child = _xtree1->getFirstChild(node);

		if (child < 0)
		{
			out << "/><?DELETE " << tag << "?>" << endl;
			_needNewLine = false;
			return;
		}

		out << "><?DELETE " << tag << "?>" << endl;
		_needNewLine = false;

		while (child > 0)
		{
			writeMatchNode(out, _xtree1, child);
			child = _xtree1->getNextSibling(child);
		}

		if (_needNewLine)
		{
			out << endl;
			_needNewLine = false;
		}

		out << "</" << tag << ">" << endl;
	}
	else
	{
		out << "<?DELETE \"" << constructText(_xtree1, node)
			<< "\"?>" << endl;
		_needNewLine = false;
	}
}

void XDiff::writeInsertNode(ofstream &out, int node)
{
	if (_xtree2->isElement(node))
	{
		string	tag = _xtree2->getTag(node);
		out << "<" << tag;

		// Attributes.
		int	attr = _xtree2->getFirstAttribute(node);
		while (attr > 0)
		{
			string	atag = _xtree2->getTag(attr);
			string	value = _xtree2->getAttributeValue(attr);
			out << " " << atag << "=\"" << value << "\"";
			attr = _xtree2->getNextAttribute(attr);
		}

		// Child nodes.
		int	child = _xtree2->getFirstChild(node);
		if (child < 0)
		{
			out << "/><?INSERT " << tag << "?>" << endl;
			_needNewLine = false;
			return;
		}

		out << "><?INSERT " << tag << "?>" << endl;
		_needNewLine = false;

		while (child > 0)
		{
			writeMatchNode(out, _xtree2, child);
			child = _xtree2->getNextSibling(child);
		}

		if (_needNewLine)
		{
			out << endl;
			_needNewLine = false;
		}

		out << "</" << tag << ">" << endl;
	}
	else
	{
		out << constructText(_xtree2, node) << "<?INSERT?>" << endl;
		_needNewLine = false;
	}
}

void XDiff::writeMatchNode(ofstream &out, XTree *xtree, int node)
{
	if (xtree->isElement(node))
	{
		string	tag = xtree->getTag(node);
		if (_needNewLine)
			out << endl;

		out << "<" << tag;

		// Attributes.
		int	attr = xtree->getFirstAttribute(node);
		while (attr > 0)
		{
			string	atag = xtree->getTag(attr);
			string	value = xtree->getAttributeValue(attr);
			out << " " << atag << "=\"" << value << "\"";
			attr = xtree->getNextAttribute(attr);
		}

		// Child nodes.
		int	child = xtree->getFirstChild(node);
		if (child < 0)
		{
			out << "/>" << endl;
			_needNewLine = false;
			return;
		}

		out << ">";
		_needNewLine = true;

		while (child > 0)
		{
			writeMatchNode(out, xtree, child);
			child = xtree->getNextSibling(child);
		}

		if (_needNewLine)
		{
			out << endl;
			_needNewLine = false;
		}

		out << "</" << tag << ">" << endl;
	}
	else
	{
		out << constructText(xtree, node);
		_needNewLine = false;
	}
}

void XDiff::writeDiffNode(ofstream &out, int node1, int node2)
{
	if (_xtree1->isElement(node1))
	{
		string	tag = _xtree1->getTag(node1);
		if (_needNewLine)
			out << endl;
		out << "<" << tag;

		// Attributes.
		int	attr1 = _xtree1->getFirstAttribute(node1);
		string	diffff = "";
		while (attr1 > 0)
		{
			string	atag = _xtree1->getTag(attr1);
			string	value = _xtree1->getAttributeValue(attr1);
			int	matchType, matchNode;
			_xtree1->getMatching(attr1, matchType, matchNode);
			if (matchType == XTree::MATCH)
				out << " " << atag << "=\"" << value << "\"";
			else if (matchType == XTree::DELETE)
			{
				out << " " << atag << "=\"" << value << "\"";
				diffff += "<?DELETE " + atag + "?>";
			}
			else
			{
				string	value2 = _xtree2->getAttributeValue(matchNode);
				out << " " << atag << "=\"" << value2 << "\"";
				diffff += "<?UPDATE " + atag +
					  " FROM \"" + value + "\"?>";
			}

			attr1 = _xtree1->getNextAttribute(attr1);
		}

		int	attr2 = _xtree2->getFirstAttribute(node2);
		while (attr2 > 0)
		{
			int	matchType, matchNode;
			_xtree2->getMatching(attr2, matchType, matchNode);
			if (matchType == XTree::INSERT)
			{
				string	atag = _xtree2->getTag(attr2);
				string	value = _xtree2->getAttributeValue(attr2);
				out << " " << atag << "=\"" << value << "\"";
				diffff += "<?INSERT " + atag + "?>";
			}

			attr2 = _xtree2->getNextAttribute(attr2);
		}

		// Child nodes.
		int	child1 = _xtree1->getFirstChild(node1);
		if (child1 < 0)
		{
			out << "/>" << diffff << endl;
			_needNewLine = false;
			return;
		}

		out << ">" << diffff;
		_needNewLine = true;

		while (child1 > 0)
		{
			int	matchType, matchNode;
			_xtree1->getMatching(child1, matchType, matchNode);
			if (matchType == XTree::MATCH)
				writeMatchNode(out, _xtree1, child1);
			else if (matchType == XTree::DELETE)
				writeDeleteNode(out, child1);
			else
				writeDiffNode(out, child1, matchNode);

			child1 = _xtree1->getNextSibling(child1);
		}

		int	child2 = _xtree2->getFirstChild(node2);
		while (child2 > 0)
		{
			int 	matchType, matchNode;
			_xtree2->getMatching(child2, matchType, matchNode);
			if (matchType == XTree::INSERT)
				writeInsertNode(out, child2);

			child2 = _xtree2->getNextSibling(child2);
		}

		if (_needNewLine)
		{
			out << endl;
			_needNewLine = false;
		}

		out << "</" << tag << ">" << endl;
	}
	else
	{
		out << constructText(_xtree2, node2) << "<?UPDATE FROM \""
			<< constructText(_xtree1, node1) << "\"?>";
		_needNewLine = false;
	}
}

string XDiff::constructText(XTree *xtree, int eid)
{
	string		text = xtree->getText(eid);
	vector<size_t>	cdatalist = xtree->getCDATA(eid);
	if (cdatalist.empty())
		return text;

	string	buf = "";
	int	count = cdatalist.size();
	size_t	lastEnd = 0;
	for (int i = 0; i < count; i += 2)
	{
		size_t	cdataStart = cdatalist[i];
		size_t	cdataEnd = cdatalist[i+1];

		if (cdataStart > lastEnd)
			buf += text.substr(lastEnd, cdataStart - lastEnd);
		buf += "<![CDATA[" +
		       text.substr(cdataStart, cdataEnd - cdataStart) +
		       "]]>";
		lastEnd = cdataEnd;
	}

	if (lastEnd < text.length())
		buf += text.substr(lastEnd);

	return buf;
}

double XDiff::_diffTime(const struct timeval *time1,
			const struct timeval *time2)
{
	long	sec = time2->tv_sec - time1->tv_sec;
	long	usec = time2->tv_usec - time1->tv_usec;
	if (usec < 0)
	{
		sec--;
		usec += 1000000;
	}

	return 0.000001 * usec + sec;
}

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

	int	opid = 1;
	if (argc < 4)
	{
		cout << XDiff::USAGE << endl;
		exit(1);
	}
	else if (strcmp(args[1], "-o") == 0)
	{
		XDiff::_oFlag = true;
		opid++;
	}
	else if (strcmp(args[1], "-g") == 0)
	{
		XDiff::_gFlag = true;
		opid++;
	}

	if (strcmp(args[opid], "-p") == 0)
	{
		opid++;
		double	p = strtod(args[opid], NULL);
		if ((p <= 0) || (p > 1))
		{
			cout << XDiff::USAGE << endl;
			exit(1);
		}
		XDiff::_NO_MATCH_THRESHOLD = p;
		opid++;
	}

	if ((argc - opid) != 3)
	{
		cout << XDiff::USAGE << endl;
		exit(1);
	}

	try {
	  XDiff xdiff;
	  return xdiff.diff(args[opid], args[opid+1], args[opid+2]);
	}
	catch (const SAXParseException& e) {
	  char *message = XMLString::transcode(e.getMessage());
	  char *where = XMLString::transcode(e.getSystemId());
	  cerr << "Error: " << where
	       << ":" << e.getLineNumber() << ":" << e.getColumnNumber() << ": "
	       << message << endl;
	  XMLString::release(&where);
	  XMLString::release(&message);
	  return 2;
	}

}
