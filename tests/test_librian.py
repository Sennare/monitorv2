import unittest
from unittest.mock import MagicMock
import time
from state import StateStore, SetTemAndHumi, TempAndHumi
from database.librian import Librian

class TestLibrian(unittest.TestCase):
    def test_immediate_save_on_startup(self):
        librian = Librian()
        # Mock database.save
        mock_save = MagicMock(return_value=True)
        librian.databse.save = mock_save

        # Dispatch first valid temperature event
        state_store = StateStore()
        state_store.dispatch(SetTemAndHumi(TempAndHumi(22.5, 55.0)))

        # Wait briefly for thread to persist
        for _ in range(50):
            if mock_save.called:
                break
            time.sleep(0.05)

        self.assertTrue(mock_save.called)
        mock_save.assert_called_with(22.5, 55.0)

        # Close cleanly
        librian.close()

if __name__ == "__main__":
    unittest.main()
