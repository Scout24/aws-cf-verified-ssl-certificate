from HTMLParser import HTMLParser

class InputFieldParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            print "Found input tag with attributes:", attrs
            self.inputs.append(dict(attrs))

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass
