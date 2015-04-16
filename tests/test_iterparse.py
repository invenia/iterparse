import unittest
from six import StringIO
from iterparse.parser import iterparse


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
        stream = StringIO("""
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
        """)

        elements = list(iterparse(stream, ['wanted']))

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


if __name__ == '__main__':
    unittest.main()
