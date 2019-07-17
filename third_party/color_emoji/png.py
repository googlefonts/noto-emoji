#!/usr/bin/env python
#
# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Author(s): Behdad Esfahbod
#

import struct
import sys
if sys.version_info >= (3,0,0): # Python3
   from io import StringIO
else:
   from StringIO import StringIO


class PNG:

	signature = bytearray ((137,80,78,71,13,10,26,10))

	def __init__ (self, f):

		if (isinstance(f, str) or isinstance(f, type(u''))):
			f = open (f, 'rb')

		self.f = f
		self.IHDR = None

	def tell (self):
		return self.f.tell ()

	def seek (self, pos):
		self.f.seek (pos)

	def stream (self):
		return self.f

	def data (self):
		self.seek (0)
		if sys.version_info >= (3,0,0): # Python3
			return bytearray (self.f.read (), 'iso-8859-1')
		else:
			return bytearray (self.f.read ())

	class BadSignature (Exception): pass
	class BadChunk (Exception): pass

	def read_signature (self):
		header = bytearray (self.f.read (8))
		if header != PNG.signature:
			raise PNG.BadSignature
		return PNG.signature

	def read_chunk (self):
		buf = self.f.read (4)
		length = struct.unpack (">I", buf)[0]
		chunk_type = self.f.read (4)
		chunk_data = self.f.read (length)
		if len (chunk_data) != length:
			raise PNG.BadChunk
		crc = self.f.read (4)
		if len (crc) != 4:
			raise PNG.BadChunk
		return (chunk_type, chunk_data, crc)

	def read_IHDR (self):
		(chunk_type, chunk_data, crc) = self.read_chunk ()
		if chunk_type not in ("IHDR", b"IHDR"):
			raise PNG.BadChunk
		#  Width:              4 bytes
		#  Height:             4 bytes
		#  Bit depth:          1 byte
		#  Color type:         1 byte
		#  Compression method: 1 byte
		#  Filter method:      1 byte
		#  Interlace method:   1 byte
		return struct.unpack (">IIBBBBB", chunk_data)

	def read_header (self):
		self.read_signature ()
		self.IHDR = self.read_IHDR ()
		return self.IHDR

	def get_size (self):
		if not self.IHDR:
			pos = self.tell ()
			self.seek (0)
			self.read_header ()
			self.seek (pos)
		return self.IHDR[0:2]

	def filter_chunks (self, chunks):
		self.seek (0);
		out = StringIO ()
		if sys.version_info >= (3,0,0): # Python3
			out.write (self.read_signature ().decode('iso-8859-1'))
		else:
			out.write (self.read_signature ())
		while True:
			chunk_type, chunk_data, crc = self.read_chunk ()
			if chunk_type in chunks:
				if sys.version_info >= (3,0,0): # Python3
					out.write (struct.pack (">I", len (chunk_data)).decode('iso-8859-1'))
					out.write (chunk_type.decode('iso-8859-1'))
					out.write (chunk_data.decode('iso-8859-1'))
					out.write (crc.decode('iso-8859-1'))
				else:
					out.write (struct.pack (">I", len (chunk_data)))
					out.write (chunk_type)
					out.write (chunk_data)
					out.write (crc)
			if chunk_type in ("IEND", b"IEND"):
				break
		return PNG (out)
