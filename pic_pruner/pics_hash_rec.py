class Pics_Hash_Rec(object):

    __slots__ = ['dups_list','mo', 'copied', 'yr' ]

    def __init__(self):
        self.dups_list = []
        self.mo = None
        self.yr = None