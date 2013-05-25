import os
import re
import sys


class SubtitleFileHandler:

	timePattern = re.compile('^(\d+)\:(\d+)\:(\d+),(\d+) --> (\d+)\:(\d+)\:(\d+),(\d+)(.*)$')

	def __init__(self, fullpath):
		self.fullpath = fullpath
		self.errors=[]
		self.content=[]

		linePattern = re.compile('^\d+$')

		state, lnumber, counter, period, content = 1, 0, None, None, []
		with open(fullpath) as f:
			for each in f.read().splitlines():
				lnumber+=1
				if state==1: #waiting for the counter
					each = each.strip()
					if not each: continue #do nothing if empty
					if linePattern.match(each):
						counter=each
						state=2
						continue
					state=4
				elif state==2: #time specification
					match = SubtitleFileHandler.timePattern.match(each)
					if match: 
						period=each
						state=3
						continue
					state=4
				elif state==3: #subtitles
					if not each.strip(): #until one or more blank lines
						state=1
						content=[]
					else:
						if not content:
							self.content.append([counter, period, content])
						content.append(each)
					continue
				self.errors.append((lnumber, each))

	def filename(self):
		return os.path.basename(self.fullpath)

	def getSubtitleLines(self):
		return [(each[1], each[2]) for each in self.content]

	def getErrors(self):
		return self.errors

	def hasErrors(self):
		return self.errors

	def shift(self, st1, mt1, st2, mt2):

		def getMilliSeconds(match):
			seconds = int(match.group(1))*60 + int(match.group(2))
			return int(1000*(seconds*60 + float(match.group(3))))

		def update_time(base, newBase, scale, h, m, s, ms):
			milliseconds = int(ms) + 1000*( int(s) + 60 * ( int(m) + 60*int(h)) )
			ms=int(round((milliseconds-base) * scale + newBase))
			if ms<0:
				ms=s=m=h=0
			else:
				s = ms/1000
				m = s/60
				h = m/60
			return '%02d:%02d:%02d,%03d' % (h, m%60, s%60, ms%1000)

		timePattern=re.compile('^\s*(\d\d?)\:(\d\d)\:(\d\d(?:\.\d+)?)\s*$')
		st1match = timePattern.match(st1)
		if not st1match: raise Exception('Invalid subtitle time: '+st1)
		mt1match = timePattern.match(mt1)
		if not st1match: raise Exception('Invalid movie time: '+mt1)
		
		base, newBase = getMilliSeconds(st1match), getMilliSeconds(mt1match)

		if st2:
			st2match = timePattern.match(st2)
			if not st2match: raise Exception('Invalid second subtitle time: '+st2)
			mt2match = timePattern.match(mt2)
			if not mt2match: raise Exception('Invalid second movie time: '+mt2)
			scale = (getMilliSeconds(mt2match)-newBase)/(float(getMilliSeconds(st2match) - base))
		else:
			scale=1.0

		for definition in self.content:
			period = SubtitleFileHandler.timePattern.match(definition[1])
			start = update_time(base, newBase, scale, period.group(1), period.group(2), period.group(3), period.group(4))
			end = update_time(base, newBase, scale, period.group(5), period.group(6), period.group(7), period.group(8))
			definition[1]='%s --> %s%s'%(start, end, period.group(9))

		filename = self.filename()
		if not filename.startswith('_onshift_'):
			self.fullpath = os.path.join(os.path.dirname(self.fullpath), '_onshift_'+filename)

		with open(self.fullpath, 'w') as f:
			for counter, period, content in self.content:
				print >>f, counter
				print >>f, period
				for line in content:
					print >>f, line
				print >>f

