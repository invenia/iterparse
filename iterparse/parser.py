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
        self.completed_elements = []

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
            self.completed_elements.append(self.element)
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
        # Note: Avoid clearing completed_elements here as it will
        # cause graceful exception handling to fail.
        pass


def iterparse(stream, tag, size=1024, **kwargs):
    """
    Iterativel parse an xml file
    """
    target = LowMemoryTarget(tag, **kwargs)
    parser = XMLParser(target=target)

    raw = stream.read(size)

    while raw:
        try:
            parser.feed(raw)
        finally:
            elements = target.completed_elements
            while elements:
                yield elements.pop(0)

        raw = stream.read(size)
