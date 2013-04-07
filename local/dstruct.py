class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

    @staticmethod
    def nonulls(**entries):
        s=Struct()
        for k, v in entries.items():
            s.__dict__[k]=v or ''
        return s

    @staticmethod
    def fromjs(**entries):
        s=Struct()
        for k, v in entries.items():
            s.__dict__[k]=v or None
        return s
