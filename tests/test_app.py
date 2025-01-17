import unittest
from unittest.mock import MagicMock, patch
import logging
from main import App  # Adjust the import based on your actual module structure

class TestApp(unittest.TestCase):
    @patch('ConnectionManager.ConnectionManager')
    def test_command_execution(self, MockConnectionManager):
        # Set up the mock
        mock_connection = MagicMock()
        MockConnectionManager.return_value = mock_connection

        # Create an instance of the app
        app = App()

        # Mock the method to avoid actual network operations
        app.connect_to_device = MagicMock()
        app.start_acquisition = MagicMock()

        # Mock the input boxes to return numerical parameters
        #app.inputboxes_frame.get = MagicMock(return_value={"192.168.1.20": "123 456"})

        # Manually add a mock connection
        app.connections.append(mock_connection)

        # Define the expected command
        base_command = "cd /root/RedPitaya/G && ./send_acquire"
        params = app.inputboxes_frame.get()
        param_str = ' '.join([str(params[ip]) for ip in params])
        expected_command = f"{base_command} {param_str}"

        # Define a proper start_acquisition method that will use execute_command
        def mock_start_acquisition(command):
            logging.debug(f"Command to execute: {command}")
            print(f"Command to execute: {command}")  # Debug log
            for connection in app.connections:
                connection.execute_command(command)

        app.start_acquisition = mock_start_acquisition

        # Start acquisition (this should send the command to all connections)
        app.start_acquisition(expected_command)

        # Assert the command was sent correctly
        for connection in app.connections:
            connection.execute_command.assert_any_call(expected_command)

        # Print out the actual calls made to verify
        for connection in app.connections:
            print(f"Calls made to connection: {connection.execute_command.call_args_list}")

        # Cleanup
        app.destroy()

if __name__ == '__main__':
    unittest.main()