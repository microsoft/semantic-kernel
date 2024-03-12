#
# libraryBookDemo.py
#
# Simple statemachine demo, based on the state transitions given in librarybookstate.pystate
#

import statemachine
import librarybookstate


class Book(librarybookstate.BookStateMixin):
    def __init__(self):
        self.initialize_state(librarybookstate.New)


class RestrictedBook(Book):
    def __init__(self):
        super(RestrictedBook, self).__init__()
        self._authorized_users = []

    def authorize(self, name):
        self._authorized_users.append(name)

    # specialized checkout to check permission of user first
    def checkout(self, user=None):
        if user in self._authorized_users:
            super().checkout()
        else:
            raise Exception("{0} could not check out restricted book".format(user if user is not None else "anonymous"))


def run_demo():
    book = Book()
    book.shelve()
    print(book)
    book.checkout()
    print(book)
    book.checkin()
    print(book)
    book.reserve()
    print(book)
    try:
        book.checkout()
    except Exception as e: # statemachine.InvalidTransitionException:
        print(e)
        print('..cannot check out reserved book')
    book.release()
    print(book)
    book.checkout()
    print(book)
    print()

    restricted_book = RestrictedBook()
    restricted_book.authorize("BOB")
    restricted_book.restrict()
    print(restricted_book)
    for name in [None, "BILL", "BOB"]:
        try:
            restricted_book.checkout(name)
        except Exception as e:
            print('..' + str(e))
        else:
            print('checkout to', name)
    print(restricted_book)
    restricted_book.checkin()
    print(restricted_book)


if __name__ == '__main__':
    run_demo()
