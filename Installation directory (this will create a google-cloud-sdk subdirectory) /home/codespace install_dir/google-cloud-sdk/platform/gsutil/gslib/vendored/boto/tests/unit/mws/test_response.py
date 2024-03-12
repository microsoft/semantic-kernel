#!/usr/bin/env python
from boto.mws.connection import MWSConnection
from boto.mws.response import (ResponseFactory, ResponseElement, Element,
                               MemberList, ElementList, SimpleList)


from tests.unit import AWSMockServiceTestCase
from boto.compat import filter, map
from tests.compat import unittest


class TestMWSResponse(AWSMockServiceTestCase):
    connection_class = MWSConnection
    mws = True

    def test_parsing_nested_elements(self):
        class Test9one(ResponseElement):
            Nest = Element()
            Zoom = Element()

        class Test9Result(ResponseElement):
            Item = Element(Test9one)

        text = b"""<Test9Response><Test9Result>
                  <Item>
                        <Foo>Bar</Foo>
                        <Nest>
                            <Zip>Zap</Zip>
                            <Zam>Zoo</Zam>
                        </Nest>
                        <Bif>Bam</Bif>
                  </Item>
                  </Test9Result></Test9Response>"""
        obj = self.check_issue(Test9Result, text)
        Item = obj._result.Item
        useful = lambda x: not x[0].startswith('_')
        nest = dict(filter(useful, Item.Nest.__dict__.items()))
        self.assertEqual(nest, dict(Zip='Zap', Zam='Zoo'))
        useful = lambda x: not x[0].startswith('_') and not x[0] == 'Nest'
        item = dict(filter(useful, Item.__dict__.items()))
        self.assertEqual(item, dict(Foo='Bar', Bif='Bam', Zoom=None))

    def test_parsing_member_list_specification(self):
        class Test8extra(ResponseElement):
            Foo = SimpleList()

        class Test8Result(ResponseElement):
            Item = MemberList(SimpleList)
            Extra = MemberList(Test8extra)

        text = b"""<Test8Response><Test8Result>
                  <Item>
                        <member>0</member>
                        <member>1</member>
                        <member>2</member>
                        <member>3</member>
                  </Item>
                  <Extra>
                        <member><Foo>4</Foo><Foo>5</Foo></member>
                        <member></member>
                        <member><Foo>6</Foo><Foo>7</Foo></member>
                  </Extra>
                  </Test8Result></Test8Response>"""
        obj = self.check_issue(Test8Result, text)
        self.assertSequenceEqual(
            list(map(int, obj._result.Item)),
            list(range(4)),
        )
        self.assertSequenceEqual(
            list(map(lambda x: list(map(int, x.Foo)), obj._result.Extra)),
            [[4, 5], [], [6, 7]],
        )

    def test_parsing_nested_lists(self):
        class Test7Result(ResponseElement):
            Item = MemberList(Nest=MemberList(),
                              List=ElementList(Simple=SimpleList()))

        text = b"""<Test7Response><Test7Result>
                  <Item>
                        <member>
                            <Value>One</Value>
                            <Nest>
                                <member><Data>2</Data></member>
                                <member><Data>4</Data></member>
                                <member><Data>6</Data></member>
                            </Nest>
                        </member>
                        <member>
                            <Value>Two</Value>
                            <Nest>
                                <member><Data>1</Data></member>
                                <member><Data>3</Data></member>
                                <member><Data>5</Data></member>
                            </Nest>
                            <List>
                                <Simple>4</Simple>
                                <Simple>5</Simple>
                                <Simple>6</Simple>
                            </List>
                            <List>
                                <Simple>7</Simple>
                                <Simple>8</Simple>
                                <Simple>9</Simple>
                            </List>
                        </member>
                        <member>
                            <Value>Six</Value>
                            <List>
                                <Complex>Foo</Complex>
                                <Simple>1</Simple>
                                <Simple>2</Simple>
                                <Simple>3</Simple>
                            </List>
                            <List>
                                <Complex>Bar</Complex>
                            </List>
                        </member>
                  </Item>
                  </Test7Result></Test7Response>"""
        obj = self.check_issue(Test7Result, text)
        item = obj._result.Item
        self.assertEqual(len(item), 3)
        nests = [z.Nest for z in filter(lambda x: x.Nest, item)]
        self.assertSequenceEqual(
            [[y.Data for y in nest] for nest in nests],
            [[u'2', u'4', u'6'], [u'1', u'3', u'5']],
        )
        self.assertSequenceEqual(
            [element.Simple for element in item[1].List],
            [[u'4', u'5', u'6'], [u'7', u'8', u'9']],
        )
        self.assertSequenceEqual(
            item[-1].List[0].Simple,
            ['1', '2', '3'],
        )
        self.assertEqual(item[-1].List[1].Simple, [])
        self.assertSequenceEqual(
            [e.Value for e in obj._result.Item],
            ['One', 'Two', 'Six'],
        )

    def test_parsing_member_list(self):
        class Test6Result(ResponseElement):
            Item = MemberList()

        text = b"""<Test6Response><Test6Result>
                  <Item>
                        <member><Value>One</Value></member>
                        <member><Value>Two</Value>
                                <Error>Four</Error>
                        </member>
                        <member><Value>Six</Value></member>
                  </Item>
                  </Test6Result></Test6Response>"""
        obj = self.check_issue(Test6Result, text)
        self.assertSequenceEqual(
            [e.Value for e in obj._result.Item],
            ['One', 'Two', 'Six'],
        )
        self.assertTrue(obj._result.Item[1].Error == 'Four')
        with self.assertRaises(AttributeError) as e:
            obj._result.Item[2].Error

    def test_parsing_empty_member_list(self):
        class Test5Result(ResponseElement):
            Item = MemberList(Nest=MemberList())

        text = b"""<Test5Response><Test5Result>
                  <Item/>
                  </Test5Result></Test5Response>"""
        obj = self.check_issue(Test5Result, text)
        self.assertSequenceEqual(obj._result.Item, [])

    def test_parsing_missing_member_list(self):
        class Test4Result(ResponseElement):
            Item = MemberList(NestedItem=MemberList())

        text = b"""<Test4Response><Test4Result>
                  </Test4Result></Test4Response>"""
        obj = self.check_issue(Test4Result, text)
        self.assertSequenceEqual(obj._result.Item, [])

    def test_parsing_element_lists(self):
        class Test1Result(ResponseElement):
            Item = ElementList()

        text = b"""<Test1Response><Test1Result>
            <Item><Foo>Bar</Foo></Item>
            <Item><Zip>Bif</Zip></Item>
            <Item><Foo>Baz</Foo>
                      <Zam>Zoo</Zam></Item>
        </Test1Result></Test1Response>"""
        obj = self.check_issue(Test1Result, text)
        self.assertTrue(len(obj._result.Item) == 3)
        elements = lambda x: getattr(x, 'Foo', getattr(x, 'Zip', '?'))
        elements = list(map(elements, obj._result.Item))
        self.assertSequenceEqual(elements, ['Bar', 'Bif', 'Baz'])

    def test_parsing_missing_lists(self):
        class Test2Result(ResponseElement):
            Item = ElementList()

        text = b"""<Test2Response><Test2Result>
        </Test2Result></Test2Response>"""
        obj = self.check_issue(Test2Result, text)
        self.assertEqual(obj._result.Item, [])

    def test_parsing_simple_lists(self):
        class Test3Result(ResponseElement):
            Item = SimpleList()

        text = b"""<Test3Response><Test3Result>
            <Item>Bar</Item>
            <Item>Bif</Item>
            <Item>Baz</Item>
        </Test3Result></Test3Response>"""
        obj = self.check_issue(Test3Result, text)
        self.assertSequenceEqual(obj._result.Item, ['Bar', 'Bif', 'Baz'])

    def check_issue(self, klass, text):
        action = klass.__name__[:-len('Result')]
        factory = ResponseFactory(scopes=[{klass.__name__: klass}])
        parser = factory(action, connection=self.service_connection)
        return self.service_connection._parse_response(parser, 'text/xml', text)


if __name__ == "__main__":
    unittest.main()
