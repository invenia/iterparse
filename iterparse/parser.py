from lxml.etree import Element, XMLParser, tostring


class LowMemoryTarget(object):
    """
    An XMLParser target that only stores the data you want,
    when you want it.
    """
    def __init__(self, tags, debug=False):
        self._tags = frozenset(tags)
        self._debug = debug

        self.element = None
        self.parent = None

        self.tree = None  # Debug only.
        self.complete = []

        self.text = []

        self.last_tag_event = None

    def start(self, tag, attrib):
        """
        The starting tag.

        TODO: how do self-closing tags work?
        TODO: Handling of namespaces?
        """
        if self.element is None and tag not in self._tags:
            return

        # Throw away any text that occurred within an element containing
        # a child. eg. <a>garbage<b>text</b></a>
        self.text = []

        # Add last element as an ancestor when two start.
        if self.last_tag_event == 'start':
            self.parent = self.element

        self.element = Element(tag, attrib)

        if self.parent is not None:
            self.parent.append(self.element)

        if self._debug:
            print 'START', tag

            if not self.tree:
                self.tree = self.element

            print tostring(self.tree, pretty_print=True)

        # Avoid saving text after an end tag.
        self.last_tag_event = 'start'

    def end(self, tag):
        """
        The closing tag.
        """

        if self.element is None:
            return

        # Assign text to an element.
        if self.text:
            self.element.text = ''.join(self.text)
            self.text = []  # Probably not needed

        if self._debug:
            print 'END', tag
            print tostring(self.tree, pretty_print=True)

        if self.last_tag_event == 'end':
            self.element = self.element.getparent()
            self.parent = self.element.getparent()

        if self.parent is None:
            self.complete.append(self.element)
            self.element = None
            self.tree = None

            if self._debug:
                print "********"

        self.last_tag_event = 'end'

    def data(self, text):
        """
        Text for a tag
        """

        if self.element is None:
            return

        # Avoid record text that after the end of a tag.
        # eg. <a><b>text</b>garbage</a>
        if self.last_tag_event == 'start':
            self.text.append(text)

    # Avoid defining comment method if we aren't using it.
    # def comment(self, text):
    #     pass

    def close(self):
        """
        Close the parser
        """
        # self._complete = []
        # self._tree = []
        pass

    def actions(self):
        """
        Get all the completed elements
        """
        while self.complete:
            yield self.complete.pop(0)


def iterparse(stream, tag, size=1024):
    """
    Iterativel parse an xml file
    """
    target = LowMemoryTarget(tag)
    parser = XMLParser(target=target)

    raw = stream.read(size)

    while raw:
        parser.feed(raw)

        for action in target.actions():
            yield action

        raw = stream.read(size)
