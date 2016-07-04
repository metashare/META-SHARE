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

#include "XLut.hpp"

XLut::XLut(bool con)
: _xTable(4096)
{
	_possibleConflict = con;
	_conflict = false;
}

void XLut::add(int eid1, int eid2, int dist)
{
	unsigned int	key = ((unsigned int)eid1 << 16) | (eid2 & 0xffff);
	unsigned long long	value = ((unsigned long long)eid1 << 40) | ((unsigned long long)(eid2 & 0xffffff) << 16) | dist;
	if (_possibleConflict)
	{
		hash_map<unsigned int, unsigned long long>::const_iterator hit = _xTable.find(key);
		if (hit == _xTable.end())
			_xTable[key] = value;
		else
		{
			do
			{
				key++;
				hit = _xTable.find(key);
			}
			while (hit != _xTable.end());
			_xTable[key] = value;
			_conflict = true;
		}
	}
	else
		_xTable[key] = value;
}

int XLut::get(int eid1, int eid2)
{
	unsigned int	key = ((unsigned int)eid1 << 16) | (eid2 & 0xffff);
	hash_map<unsigned int, unsigned long long>::const_iterator hit = _xTable.find(key);
	if (hit == _xTable.end())
		return XTree::NO_CONNECTION;

	if (!_conflict)
		return (int)(hit->second & 0xffff);
	else
	{
		unsigned long long	partialValue = ((unsigned long long)eid1 << 40) | ((unsigned long long)(eid2 & 0xffffff) << 16);
		unsigned long long	bucket = hit->second;
		if (((partialValue ^ bucket) >> 16) == 0)
			return (int)(bucket & 0xffff);
		else
		{
			do
			{
				key++;
				hit = _xTable.find(key);
				if (hit == _xTable.end())
					return XTree::NO_CONNECTION;
				bucket = hit->second;
			}
			while (((partialValue ^ bucket) >> 16) != 0);
			return (int)(bucket & 0xffff);
		}
	}
}
