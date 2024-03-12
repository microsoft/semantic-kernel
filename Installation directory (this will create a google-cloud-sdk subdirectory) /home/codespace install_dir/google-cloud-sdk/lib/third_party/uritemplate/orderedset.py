# From: https://github.com/ActiveState/code/blob/master/recipes/Python/576696_OrderedSet_with_Weakrefs/  # noqa

from weakref import proxy

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc


class Link(object):
    __slots__ = 'prev', 'next', 'key', '__weakref__'


class OrderedSet(collections_abc.MutableSet):
    'Set the remembers the order elements were added'
    # Big-O running times for all methods are the same as for regular sets.
    # The internal self.__map dictionary maps keys to links in a doubly linked
    # list. The circular doubly linked list starts and ends with a sentinel
    # element. The sentinel element never gets deleted (this simplifies the
    # algorithm). The prev/next links are weakref proxies (to prevent circular
    # references). Individual links are kept alive by the hard reference in
    # self.__map. Those hard references disappear when a key is deleted from
    # an OrderedSet.

    def __init__(self, iterable=None):
        self.__root = root = Link()  # sentinel node for doubly linked list
        root.prev = root.next = root
        self.__map = {}  # key --> link
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.__map)

    def __contains__(self, key):
        return key in self.__map

    def add(self, key):
        # Store new key in a new link at the end of the linked list
        if key not in self.__map:
            self.__map[key] = link = Link()
            root = self.__root
            last = root.prev
            link.prev, link.next, link.key = last, root, key
            last.next = root.prev = proxy(link)

    def discard(self, key):
        # Remove an existing item using self.__map to find the link which is
        # then removed by updating the links in the predecessor and successors.
        if key in self.__map:
            link = self.__map.pop(key)
            link.prev.next = link.next
            link.next.prev = link.prev

    def __iter__(self):
        # Traverse the linked list in order.
        root = self.__root
        curr = root.next
        while curr is not root:
            yield curr.key
            curr = curr.next

    def __reversed__(self):
        # Traverse the linked list in reverse order.
        root = self.__root
        curr = root.prev
        while curr is not root:
            yield curr.key
            curr = curr.prev

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return not self.isdisjoint(other)
