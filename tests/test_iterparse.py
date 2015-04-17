import unittest
from six import BytesIO
from iterparse.parser import iterparse
from lxml.etree import XMLSyntaxError


class Iterparse(unittest.TestCase):
    def assertElement(
        self, element, name, text=None, num_children=0, num_attrib=0,
    ):
        self.assertEqual(element.tag, name)
        self.assertEqual(element.text, text)
        self.assertEqual(element.tail, None)
        self.assertEqual(len(element.getchildren()), num_children)
        self.assertEqual(len(element.attrib), num_attrib)

    def test_basic(self):
        stream = BytesIO(
            b"""
            <root>
                <unwanted>
                    <unwanted-0>foo</unwanted-0>
                    <unwanted-1>foo</unwanted-1>
                    <unwanted-2>foo</unwanted-2>
                </unwanted>
                <wanted>garbage
                    <wanted-0 key="value">foo</wanted-0>
                    <wanted-1>foo</wanted-1>junk
                    <wanted-2>foo</wanted-2><!-- comment -->
                    <wanted-3>
                        <wanted-3a>sub-sub
                            <wanted-3aa>deep</wanted-3aa>
                        </wanted-3a>
                        <wanted-3b>sup</wanted-3b>
                    </wanted-3>
                    <wanted-4/>
                    bullshit
                </wanted>
            </root>
            """
        )

        elements = list(iterparse(stream, tag=['wanted']))

        self.assertEqual(len(elements), 1)

        element = elements[0]
        self.assertElement(element, 'wanted', num_children=5)
        self.assertElement(element[0], 'wanted-0', text='foo', num_attrib=1)
        self.assertElement(element[1], 'wanted-1', text='foo')
        self.assertElement(element[2], 'wanted-2', text='foo')
        self.assertElement(element[3], 'wanted-3', num_children=2)
        self.assertElement(element[3][0], 'wanted-3a', num_children=1)
        self.assertElement(element[3][0][0], 'wanted-3aa', text='deep')
        self.assertElement(element[3][1], 'wanted-3b', text='sup')
        self.assertElement(element[4], 'wanted-4')

    def test_exception_handling(self):
        stream = BytesIO(b'<a>1</a>2</a>3')

        elements = iterparse(stream, tag=['a'], debug=True)

        # We can process the first <a> without issue.
        element = next(elements)
        self.assertElement(element, 'a', text='1')

        # Processing the second <a> should fail.
        with self.assertRaises(XMLSyntaxError):
            next(elements)

    def test_error_extra_content(self):
        stream = BytesIO(b'<a><b></a></b>')

        elements = iterparse(stream, tag=['a'])

        with self.assertRaises(XMLSyntaxError):
            next(elements)

    def test_error_opening_ending_mismatch(self):
        stream = BytesIO(b'</a>')

        elements = iterparse(stream, tag=['a'])

        with self.assertRaises(XMLSyntaxError):
            next(elements)

    def test_error_document_is_empty(self):
        stream = BytesIO(b'0<a></a>')

        elements = iterparse(stream, tag=['a'])

        with self.assertRaises(XMLSyntaxError):
            next(elements)

    def test_return_order(self):
        stream = BytesIO(
            b"""
            <root>
                <wanted>
                    <wanted-0>foo</wanted-0>
                </wanted>
            </root>
            """
        )

        elements = list(iterparse(stream, tag=['wanted', 'wanted-0']))

        self.assertEqual(len(elements), 2)

        element = elements[0]
        self.assertElement(element, 'wanted-0', text='foo')

        element = elements[1]
        self.assertElement(element, 'wanted', num_children=1)
        self.assertElement(element[0], 'wanted-0', text='foo')

    def test_namespaces(self):
        text = b"""
            <root xmlns:a1="example.com/a1" xmlns:a2="example.com/a2">
                <a1:a>1</a1:a>
                <a2:a>2</a2:a>
            </root>
            """

        # Make sure we can filter with namespaces.
        elements = list(iterparse(BytesIO(text), tag=['{example.com/a1}a']))

        self.assertEquals(len(elements), 1)
        self.assertElement(elements[0], '{example.com/a1}a', text='1')

        elements = list(iterparse(BytesIO(text), tag=['{example.com/a2}a']))

        self.assertEquals(len(elements), 1)
        self.assertElement(elements[0], '{example.com/a2}a', text='2')

        # Make sure that we can filter while ignoring namespaces.
        elements = list(
            iterparse(BytesIO(text), tag=['a'], ignore_namespace=True)
        )

        self.assertEquals(len(elements), 2)
        self.assertElement(elements[0], '{example.com/a1}a', text='1')
        self.assertElement(elements[1], '{example.com/a2}a', text='2')

        # Make sure we can filter with namespaces and strip the result.
        elements = list(
            iterparse(
                BytesIO(text), tag=['{example.com/a1}a'],
                strip_namespace=True,
            )
        )

        self.assertEquals(len(elements), 1)
        self.assertElement(elements[0], 'a', text='1')

        # Combination of ignoring/striping namespaces.
        elements = list(
            iterparse(
                BytesIO(text), tag=['a'], strip_namespace=True,
                ignore_namespace=True,
            )
        )

        self.assertEquals(len(elements), 2)
        self.assertElement(elements[0], 'a', text='1')
        self.assertElement(elements[1], 'a', text='2')


if __name__ == '__main__':
    unittest.main()
