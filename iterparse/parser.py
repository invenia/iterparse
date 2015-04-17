from __future__ import print_function

import re

from lxml.etree import Element, XMLParser, tostring
from six import text_type


class Tag(object):
    """
    An XML tag
    """
    def __init__(self, raw):
        self._namespace, self._name = re.search(
            '^(:?\{([^{}]+)\})?([^{}]+)$', raw
        ).groups()[1:]

    @property
    def namespace(self):
        return self._namespace

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        if isinstance(other, text_type):
            other = Tag(other)

        if isinstance(other, Tag):
            return self.name == other.name and (
                (not self.namespace) or
                (not other.namespace) or
                self.namespace == other.namespace
            )

        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, (text_type, Tag)):
            return not (self == other)

        return NotImplemented

    def __repr__(self):
        return 'Tag({%s}%s)' % (self._namespace or '', self._name)

    def __hash__(self):
        return hash((self._namespace, self._name))


class MinimalTarget(object):
    """
    A minimal XMLParser target that only stores the data you want. It
    does not support every XML feature (by design) but (should) support
    everything you need.

    tags: The names of tags you would like to store
    """
    def __init__(self, tags, strip_namespace=False, debug=False):
        self._tags = frozenset(Tag(tag) for tag in tags)
        self._debug = debug

        self._element = None
        self._text = []

        self._strip = strip_namespace

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

        # Save elements are tags we are interested in or which are
        # decendents of interesting tags.
        save_element = self._element is not None

        if not save_element:
            save_element = self._desired_tag(tag)

        if save_element:
            parent = self._element

            if self._strip:
                tag = Tag(tag).name

            element = Element(tag, attrib)

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

        if self._element is not None:
            if self._text:
                self._element.text = ''.join(self._text)
                self._text = []  # Probably not needed

            if self._desired_tag(tag):
                self.completed_elements.append(self._element)
                self._tree = None

            self._element = self._element.getparent()

        if self._debug and self._tree is not None and self._text:
            print(tostring(self._tree, pretty_print=True))

        # Avoid saving text that occurs after the end of a tag.
        # eg. <a><b>text</b>garbage</a>
        self._keep_text = False

    def _desired_tag(self, tag):
        """
        Test whether a tag is desired
        """
        wrapped = Tag(tag)

        for desired in self._tags:
            if wrapped == desired:
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


def iterparse(
    source, events=('end',), tag=None, strip_namespace=False, **kwargs
):
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
    debug = kwargs.pop('debug', False)

    target = MinimalTarget(
        tags=tag, strip_namespace=strip_namespace, debug=debug,
    )
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
