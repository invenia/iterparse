from __future__ import print_function
from lxml.etree import Element, QName, XMLParser, tostring


class MinimalTarget(object):
    """
    A minimal XMLParser target that only stores the data you want. It
    does not support every XML feature (by design) but (should) support
    everything you need.

    tags: The names of tags you would like to store
    """
    def __init__(
        self, tags=None, strip_namespace=False, ignore_namespace=False,
        debug=False,
    ):
        if tags is None:
            self._tags = tags
        else:
            self._tags = frozenset(QName(tag) for tag in tags)

        self._strip_namespace = strip_namespace
        self._ignore_namespace = ignore_namespace
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
            print('START', tag)

        # Throw away any text that occurred within an element containing
        # a child. eg. <a>garbage<b>text</b></a>
        self._text = []

        if self._ignore_namespace or self._strip_namespace:
            tag = QName(tag)

        # Save elements are tags we are interested in or which are
        # decendents of interesting tags.
        if self._element is not None or self._is_desired_tag(tag):
            parent = self._element

            name = tag.localname if self._strip_namespace else str(tag)
            element = Element(name, attrib)

            if parent is not None:
                parent.append(element)

            self._element = element
            self._keep_text = True

        if self._debug:
            if self._tree is None:
                self._tree = self._element

            if self._tree is not None:
                print(tostring(self._tree, pretty_print=True))

    def end(self, tag):
        """
        Close a tag
        """
        if self._debug:
            print('END', tag)

        if self._ignore_namespace:
            tag = QName(tag)

        if self._element is not None:
            if self._text:
                self._element.text = ''.join(self._text)
                self._text = []  # Probably not needed

            if self._is_desired_tag(tag):
                self.completed_elements.append(self._element)
                self._tree = None

            self._element = self._element.getparent()

        if self._debug and self._tree is not None and self._text:
            print(tostring(self._tree, pretty_print=True))

        # Avoid saving text that occurs after the end of a tag.
        # eg. <a><b>text</b>garbage</a>
        self._keep_text = False

    def _is_desired_tag(self, tag):
        """
        Test whether a tag is desired
        """
        if self._tags is None:
            return True

        if self._ignore_namespace:
            for desired_tag in self._tags:
                if tag.localname == desired_tag.localname:
                    return True
        else:
            for desired_tag in self._tags:
                if tag == desired_tag:
                    return True

        return False

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


def iterparse(source, events=('end',), tag=None, **kwargs):
    """
    Iteratively parse an xml file, firing end events for any requested
    tags

    stream: The XML stream to parse.
    tag: The iterable of tags to fire events on.
    size: (optional, 1024) The number of bytes to read at a time.
    """
    # Note: We need to remove all kwargs not supported by XMLParser
    # which but are supported by iterparse: source, events, tag, html,
    # recover, huge_tree.
    #
    # http://lxml.de/api/lxml.etree.XMLParser-class.html
    # http://lxml.de/api/lxml.etree.iterparse-class.html
    size = kwargs.pop('size', 1024)

    target_kwargs = dict(
        strip_namespace=kwargs.pop('strip_namespace', False),
        ignore_namespace=kwargs.pop('ignore_namespace', False),
        debug=kwargs.pop('debug', False),
    )

    target = MinimalTarget(tags=tag, **target_kwargs)
    parser = XMLParser(target=target, **kwargs)

    raw = source.read(size)

    while raw:
        try:
            parser.feed(raw)
        finally:
            # Note: When exceptions are raised within the parser the
            # target's close method will be called.
            elements = target.completed_elements
            while elements:
                yield elements.pop(0)

        raw = source.read(size)
