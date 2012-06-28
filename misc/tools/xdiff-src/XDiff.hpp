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

#ifndef	__XDIFF__
#define	__XDIFF__

#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>
#include <unistd.h>
#include <fstream>
#include <math.h>
#include <algorithm>

#include "XTree.hpp"
#include "XParser.hpp"
#include "XLut.hpp"

using namespace std;

/**
  * XDiff computes the difference between two input XML documents.
  */
class XDiff
{
public:
	static const string	USAGE;
	static bool		_oFlag, _gFlag;
        static double		_NO_MATCH_THRESHOLD;

	XDiff();
	~XDiff();

	/**
	  * @param	input1	input file #1
	  * @param	input2	input file #2
	  * @param	output	output file
	  */
	int diff(const char* input1, const char* input2, const char* output);

private:
	static const int	_CIRCUIT_SIZE, _MATRIX_SIZE, _ATTRIBUTE_SIZE;
	static const int	_TEXT_SIZE, _sampleCount;

	int			*_attrList1, *_attrList2, *_textList1;
	int			*_textList2, *_circuit, _seed;
	int			**_leastCostMatrix, **_pathMatrix;
	bool			*_attrMatch, *_textMatch1, *_textMatch2;
	bool			_needNewLine;
	unsigned long long	*_attrHash, *_textHash;
	string			*_attrTag;
	XTree			*_xtree1, *_xtree2;
	XLut			*_xlut;

	void xdiff(int pid1, int pid2, bool matchFlag);
	void diffAttributes(int attrCount1, int attrCount2);
	void diffText(int textCount1, int textCount2);
	int _matchFilter(int *elements1, int *elements2, bool *matched1,
			 bool *matched2, int count1, int count2);
	void matchListO(int *nodes1, int *nodes2, int count1, int count2,
			bool treeOrder, bool matchFlag);
	void matchList(int *nodes1, int *nodes2, int count1, int count2,
		       bool treeOrder, bool matchFlag);
	int distance(int eid1, int eid2, bool toRecord, int threshold);
	int _xdiff(int pid1, int pid2, int threshold = XTree::NO_CONNECTION);
	int _diffAttributes(int attrCount1, int attrCount2);
	int _diffText(int textCount1, int textCount2);
	int _matchListO(int *nodes1, int *nodes2, int count1, int count2,
			bool treeOrder);
	int _matchList(int *nodes1, int *nodes2, int count1, int count2,
		       bool treeOrder, int threshold);
	int findMatching(int count1, int count2, int** dist,
			 int* matching1, int* matching2);
	int optimalMatching(int count1, int count2, int** dist,
			    int* matching1, int* matching2);
	void constructLCM(int** costMatrix, int* matching,
			  int nodeCount1, int nodeCount2);
	int searchNCC(int nodeCount);
	double _diffTime(const struct timeval *time1,
			 const struct timeval *time2);

	void writeDiff(const char* input, const char* output);
	void writeDeleteNode(ofstream &out, int node);
	void writeInsertNode(ofstream &out, int node);
	void writeMatchNode(ofstream &out, XTree *xtree, int node);
	void writeDiffNode(ofstream &out, int node1, int node2);
	string constructText(XTree *xtree, int eid);
};
#endif
