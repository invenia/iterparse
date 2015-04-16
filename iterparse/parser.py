from lxml.etree import Element, XMLParser, tostring


class MinimalTarget(object):
    """
    A minimal XMLParser target that only stores the data you want. It
    does not support every XML feature (by design) but (should) support
    everything you need.

    tags: The names of tags you would like to store
    """
    def __init__(self, tags, debug=False):
        self._tags = frozenset(tags)
        self._debug = debug

        self._element = None
        self._text = []

        self._tree = None  # Debug only.
        self.completed_elements = []

        self._keep_text = False

    def start(self, tag, attrib):
        """
        Tag starting event.

        tag: The name of the tag being started.
        attrib: The attribute dictionary for the tag.

        tag: The name of the tag being started.
        attrib: The attribute dictionary for the tag.

        TODO: how do self-closing tags work?
        TODO: Handling of namespaces?
        """
        if self._debug:
            print 'START', tag

        # Throw away any text that occurred within an element containing
        # a child. eg. <a>garbage<b>text</b></a>
        self._text = []

        # Save elements are tags we are interested in or which are
        # decendents of interesting tags.
        if self._element is not None or tag in self._tags:
            parent = self._element
            element = Element(tag, attrib)

            if parent is not None:
                parent.append(element)

            self._element = element
            self._keep_text = True

        if self._debug:
            if self._tree is None:
                self._tree = self._element

            if self._tree is not None:
                print tostring(self._tree, pretty_print=True)

    def end(self, tag):
        """
        Close a tag
        """
        if self._debug:
            print 'END', tag

        if self._element is not None:
            if self._text:
                self._element.text = ''.join(self._text)
                self._text = []  # Probably not needed

            if tag in self._tags:
                self.completed_elements.append(self._element)
                self._tree = None

            self._element = self._element.getparent()

        if self._debug and self._tree is not None and self._text:
            print tostring(self._tree, pretty_print=True)

        # Avoid saving text that occurs after the end of a tag.
        # eg. <a><b>text</b>garbage</a>
        self._keep_text = False

    def data(self, text):
        """
        Text in a tag
        """
        if self._keep_text:
            self._text.append(text)

    def close(self):
        """
        Close the parser
        """
        # Note: Avoid clearing completed_elements here as it will
        # cause graceful exception handling to fail.
        pass


def iterparse(stream, tag, size=1024, **kwargs):
    """
    Iteratively parse an xml file, firing end events for any requested
    tags

    stream: The XML stream to parse.
    tag: The iterable of tags to fire events on.
    size: (optional, 1024) The number of bytes to read at a time.
    """
    target = MinimalTarget(tags=tag, **kwargs)
    parser = XMLParser(target=target)

    raw = stream.read(size)

    while raw:
        try:
            parser.feed(raw)
        finally:
            # Note: When exceptions are raised within the parser the
            # target's close method will be called.
            elements = target.completed_elements
            while elements:
                yield elements.pop(0)

        raw = stream.read(size)
