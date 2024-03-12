#
# video_demo.py
#
# Simple statemachine demo, based on the state transitions given in videostate.pystate
#

import statemachine
import videostate


class Video(videostate.VideoStateMixin):
    def __init__(self, title):
        self.initialize_state(videostate.Stopped)
        self.title = title


# ==== main loop - a REPL ====

v = Video("Die Hard.mp4")

while True:
    print(v.state)
    cmd = input("Command ({})> ".format('/'.join(videostate.VideoState.transition_names))).lower().strip()
    if not cmd:
        continue

    if cmd in ('?', 'h', 'help'):
        print('enter a transition {!r}'.format(videostate.VideoState.transition_names))
        print(' q - quit')
        print(' ?, h, help - this message')
        continue

    # quitting out
    if cmd.startswith('q'):
        break

    # get transition function for given command
    state_transition_fn = getattr(v, cmd, None)

    if state_transition_fn is None:
        print('???')
        continue

    # invoke the input transition, handle invalid commands
    try:
        state_transition_fn()
    except videostate.VideoState.InvalidTransitionException as e:
        print(e)
