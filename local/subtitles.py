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

		def getSeconds(match):
			seconds = int(match.group(1))*60 + int(match.group(2))
			return seconds*60 + int(match.group(3))

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

		timePattern=re.compile('^\s*(\d\d?)\:(\d\d)\:(\d\d)\s*$')
		st1match = timePattern.match(st1)
		if not st1match: raise Exception('Invalid subtitle time: '+st1)
		mt1match = timePattern.match(mt1)
		if not st1match: raise Exception('Invalid movie time: '+mt1)
		
		base, newBase = getSeconds(st1match), getSeconds(mt1match)

		if st2:
			st2match = timePattern.match(st2)
			if not st2match: raise Exception('Invalid second subtitle time: '+st2)
			mt2match = timePattern.match(mt2)
			if not mt2match: raise Exception('Invalid second movie time: '+mt2)
			scale = (getSeconds(mt2match)-newBase)/(float(getSeconds(st2match) - base))
		else:
			scale=1.0

		base, newBase = base*1000, newBase*1000

		raise Exception('Invalid second movie time: '+mt2)

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
		




pattern = re.compile('^(\d+)\:(\d+)\:(\d+),(\d+) --> (\d+)\:(\d+)\:(\d+),(\d+)(.*)$')
timeFormat = '%02d:%02d:%02d,%03d'
timeLineFormat = '%s --> %s%s'


def update_time(base, newBase, scale, h, m, s, ms):
	milliseconds = int(ms) + 1000*( int(s) + 60 * ( int(m) + 60*int(h)) )
	ms=int(round((milliseconds-base) * scale + newBase))
	if ms<0:
		ms=s=m=h=0
	else:
		s = ms/1000
		m = s/60
		h = m/60
	return timeFormat % (h, m%60, s%60, ms%1000)


def shift_time(base, newBase, scale, lines):
	ret, state, lnumber = [], 1, 0
	for each in lines:
		lnumber+=1
		if state==1:
			if each.strip():
				state=2
		elif state==2:
			match = pattern.match(each)
			if not match: 
				raise Exception('Problem on time line '+str(lnumber) +" : "+ each)
			start = update_time(base, newBase, scale, match.group(1), match.group(2), match.group(3), match.group(4))
			end = update_time(base, newBase, scale, match.group(5), match.group(6), match.group(7), match.group(8))
			ret.append(timeLineFormat%(start, end, match.group(9)))
			state=3
			continue
		elif not each.strip():
			state=1
		ret.append(each)
	return ret

def argError(message):
 	print message
 	sys.exit(1)

def argTime(group):
	s=0
	for each in group.split(':'):
		s=s*60+int(each)
	return s*1000

if __name__=='__main__':
	okargs=re.compile(argTimePattern)
	if len(sys.argv) not in [3, 4]:
	 	argError(sys.argv[0]+" [shift in ms | time=new_time [time2=new_time2]")
	arg2=argTimePattern.match(sys.argv[2])
	if not arg2:
		if len(sys.argv)==3 and argShiftPattern.match(sys.argv[2]):
			base = 0
			newBase = int(sys.argv[2])*1000
			scale=1.0
		else:
	 		argError(sys.argv[1]+": must be a shift in milliseconds or a time shift as in time1=time2, where times are expressed as mm:ss or hh:mm:ss")
	else:
	 	base, newBase, scale = argTime(arg2.group(1)), argTime(arg2.group(2)), 1.0
	 	if len(sys.argv)==4:
	 		arg3=argTimePattern.match(sys.argv[3])
	 		if not arg3:
	 			argError(sys.argv[2]+": must be a time shift as in time1=time2, where times are expressed as mm:ss or hh:mm:ss")
	 		t1, t2  = argTime(arg3.group(1)), argTime(arg3.group(2))
	 		if t1==base:
	 			argError('incorrect time arguments')
			scale = (float(t2 - newBase))/(t1-base)
	filename=sys.argv[1]
	with open(filename) as f:
		content = f.read().splitlines()
	dirname, basename =os.path.dirname(filename), os.path.basename(filename)
	newname = os.path.join(dirname,'shift_'+basename)
	print "***", base, newBase, scale
	updated = '\n'.join(shift_time(base, newBase, scale, content))
	with open(newname, 'w') as f:
		f.write(updated)

