import unittest
from six import StringIO
from iterparse.parser import iterparse

import lxml.etree


class Iterparse(unittest.TestCase):
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

        elements = iterparse(stream, ['wanted'])

        for element in elements:
            lxml.etree.tostring(element, pretty_print=True)


if __name__ == '__main__':
    unittest.main()
