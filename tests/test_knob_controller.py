import unittest
from state import StateStore, EventType, KnobUserAction
from input.knob_controller2 import KnobController


class _DummyRotor:
    def __init__(self):
        self.steps = 0


class TestKnobController(unittest.TestCase):
    def setUp(self):
        self.store = StateStore()
        self.store.bus._listeners.clear()
        self.received_actions = []
        self.store.subscribe(EventType.KNOB.value, lambda action: self.received_actions.append(action))

    def tearDown(self):
        self.store.bus._listeners.clear()

    def test_step_accumulation_single_step(self):
        """Verify that with steps_per_detent=1, every step is dispatched immediately."""
        controller = KnobController(steps_per_detent=1)
        # Mock rotor
        dummy = _DummyRotor()
        controller.rotor = dummy
        controller._last_steps = 0

        # Rotate right 1 step
        dummy.steps = 1
        controller._on_rotated()
        self.assertEqual(self.received_actions, [KnobUserAction.TURN_RIGHT])

        # Rotate right 2 steps quickly
        dummy.steps = 3
        controller._on_rotated()
        self.assertEqual(
            self.received_actions,
            [KnobUserAction.TURN_RIGHT, KnobUserAction.TURN_RIGHT, KnobUserAction.TURN_RIGHT],
        )

        # Rotate left 1 step
        dummy.steps = 2
        controller._on_rotated()
        self.assertEqual(
            self.received_actions,
            [
                KnobUserAction.TURN_RIGHT,
                KnobUserAction.TURN_RIGHT,
                KnobUserAction.TURN_RIGHT,
                KnobUserAction.TURN_LEFT,
            ],
        )

    def test_step_accumulation_multi_step_detent(self):
        """Verify that with steps_per_detent=2, 1 event is emitted per 2 quadrature transitions."""
        controller = KnobController(steps_per_detent=2)
        dummy = _DummyRotor()
        controller.rotor = dummy
        controller._last_steps = 0

        # Half-click (1 pulse) -> should NOT dispatch yet
        dummy.steps = 1
        controller._on_rotated()
        self.assertEqual(self.received_actions, [])

        # Second pulse completes the detent -> dispatches 1 TURN_RIGHT
        dummy.steps = 2
        controller._on_rotated()
        self.assertEqual(self.received_actions, [KnobUserAction.TURN_RIGHT])

    def test_inverted_rotation(self):
        """Verify inverted flag flips right and left."""
        controller = KnobController(steps_per_detent=1, inverted=True)
        dummy = _DummyRotor()
        controller.rotor = dummy
        controller._last_steps = 0

        # Increment steps (normally right, now inverted to left)
        dummy.steps = 1
        controller._on_rotated()
        self.assertEqual(self.received_actions, [KnobUserAction.TURN_LEFT])


if __name__ == "__main__":
    unittest.main()
