#
# documentSignoffDemo.py
#
# Example of a state machine modeling the state of a document in a document
# control system, using named state transitions
#
import statemachine
import documentsignoffstate

print('\n'.join(t.__name__ for t in documentsignoffstate.DocumentRevisionState.transitions()))

class Document(documentsignoffstate.DocumentRevisionStateMixin):
    def __init__(self):
        self.initialize_state(documentsignoffstate.New)


def run_demo():
    import random

    doc = Document()
    print(doc)

    # begin editing document
    doc.create()
    print(doc)
    print(doc.state.description)

    while not isinstance(doc._state, documentsignoffstate.Approved):

        print('...submit')
        doc.submit()
        print(doc)
        print(doc.state.description)

        if random.randint(1,10) > 3:
            print('...reject')
            doc.reject()
        else:
            print('...approve')
            doc.approve()

        print(doc)
        print(doc.state.description)

    doc.activate()
    print(doc)
    print(doc.state.description)

if __name__ == '__main__':
    run_demo()
