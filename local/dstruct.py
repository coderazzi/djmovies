class Struct:
    def __init__(self, **entries): 
    	for k, v in entries.items():
        	self.__dict__[k]=v or ''