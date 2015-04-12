import mechanize

class Browser(mechanize.Browser):

    def __init__(self, *largs, **kargs):
        mechanize.Browser.__init__(self, *largs, **kargs)
        self.addheaders = [
            ('User-agent', 
                'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
            ('Accept-Language',
                'en-US,en;q=0.8')]
        self.set_handle_robots(False)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()

