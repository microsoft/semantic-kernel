#
# trafficLightDemo.py
#
# Example of a simple state machine modeling the state of a traffic light
#

import statemachine
import trafficlightstate


class TrafficLight(trafficlightstate.TrafficLightStateMixin):
    def __init__(self):
        self.initialize_state(trafficlightstate.Red)

    def change(self):
        self._state = self._state.next_state()


light = TrafficLight()
for i in range(10):
    print("{0} {1}".format(light, ("STOP", "GO")[light.cars_can_go]))
    light.crossing_signal()
    light.delay()
    print()

    light.change()
