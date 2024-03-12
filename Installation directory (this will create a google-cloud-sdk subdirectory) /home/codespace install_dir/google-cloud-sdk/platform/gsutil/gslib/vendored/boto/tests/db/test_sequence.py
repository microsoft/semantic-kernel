# Copyright (c) 2010 Chris Moyer http://coredumped.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
 

class TestDBHandler(object):
    """Test the DBHandler"""

    def setup_class(cls):
        """Setup this class"""
        cls.sequences = []

    def teardown_class(cls):
        """Remove our sequences"""
        for s in cls.sequences:
            try:
                s.delete()
            except:
                pass

    def test_sequence_generator_no_rollover(self):
        """Test the sequence generator without rollover"""
        from boto.sdb.db.sequence import SequenceGenerator
        gen = SequenceGenerator("ABC")
        assert(gen("") == "A")
        assert(gen("A") == "B")
        assert(gen("B") == "C")
        assert(gen("C") == "AA")
        assert(gen("AC") == "BA")

    def test_sequence_generator_with_rollover(self):
        """Test the sequence generator with rollover"""
        from boto.sdb.db.sequence import SequenceGenerator
        gen = SequenceGenerator("ABC", rollover=True)
        assert(gen("") == "A")
        assert(gen("A") == "B")
        assert(gen("B") == "C")
        assert(gen("C") == "A")

    def test_sequence_simple_int(self):
        """Test a simple counter sequence"""
        from boto.sdb.db.sequence import Sequence
        s = Sequence()
        self.sequences.append(s)
        assert(s.val == 0)
        assert(s.next() == 1)
        assert(s.next() == 2)
        s2 = Sequence(s.id)
        assert(s2.val == 2)
        assert(s.next() == 3)
        assert(s.val == 3)
        assert(s2.val == 3)

    def test_sequence_simple_string(self):
        from boto.sdb.db.sequence import Sequence, increment_string
        s = Sequence(fnc=increment_string)
        self.sequences.append(s)
        assert(s.val == "A")
        assert(s.next() == "B")

    def test_fib(self):
        """Test the fibonacci sequence generator"""
        from boto.sdb.db.sequence import fib
        # Just check the first few numbers in the sequence
        lv = 0
        for v in [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]:
            assert(fib(v, lv) == lv+v)
            lv = fib(v, lv)

    def test_sequence_fib(self):
        """Test the fibonacci sequence"""
        from boto.sdb.db.sequence import Sequence, fib
        s = Sequence(fnc=fib)
        s2 = Sequence(s.id)
        self.sequences.append(s)
        assert(s.val == 1)
        # Just check the first few numbers in the sequence
        for v in [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]:
            assert(s.next() == v)
            assert(s.val == v)
            assert(s2.val == v) # it shouldn't matter which reference we use since it's garunteed to be consistent

    def test_sequence_string(self):
        """Test the String incrementation sequence"""
        from boto.sdb.db.sequence import Sequence, increment_string
        s = Sequence(fnc=increment_string)
        self.sequences.append(s)
        assert(s.val == "A")
        assert(s.next() == "B")
        s.val = "Z"
        assert(s.val == "Z")
        assert(s.next() == "AA")
