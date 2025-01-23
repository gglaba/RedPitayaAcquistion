import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import shutil
import pandas as pd
from ConnectionManager import ConnectionManager
from unittest.mock import patch, MagicMock

class TestConnectionManager:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = MagicMock()
        self.conn_manager = ConnectionManager(self.app, '192.168.1.1', 'user', 'password')

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('shutil.copy')
    @patch('pandas.read_csv')
    @patch('pandas.concat')
    @patch('shutil.move')
    @patch('os.makedirs')
    @patch('pandas.DataFrame.to_csv')
    def test_merge_csv_files_local(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
        mock_exists.side_effect = lambda path: True
        mock_listdir.side_effect = lambda path: ['file1.csv', 'file2.csv']
        mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]}), pd.DataFrame({'col2': [3, 4]})]
        mock_concat.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

        output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

        mock_copy.assert_any_call('path\\to\\driveA\\file1.csv', 'test_directory')
        mock_copy.assert_any_call('path\\to\\driveA\\file2.csv', 'test_directory')
        mock_read_csv.assert_any_call('test_directory/file1.csv')
        mock_read_csv.assert_any_call('test_directory/file2.csv')
        mock_concat.assert_called_once()
        mock_to_csv.assert_called_once_with('test_directory/file1_file2_merged.csv', index=False)
        mock_makedirs.assert_called_once_with('archive_path')
        mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
        mock_move.assert_any_call('test_directory/file2.csv', 'archive_path/file2.csv')
        assert output_file == 'test_directory/file1_file2_merged.csv'

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('shutil.copy')
    @patch('pandas.read_csv')
    @patch('pandas.concat')
    @patch('shutil.move')
    @patch('os.makedirs')
    @patch('pandas.DataFrame.to_csv')
    def test_merge_csv_files_remote(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
        class TestConnectionManager:

            @pytest.fixture(autouse=True)
            def setup(self):
                self.app = MagicMock()
                self.conn_manager = ConnectionManager(self.app, '192.168.1.1', 'user', 'password')

            @patch('os.path.exists')
            @patch('os.listdir')
            @patch('shutil.copy')
            @patch('pandas.read_csv')
            @patch('pandas.concat')
            @patch('shutil.move')
            @patch('os.makedirs')
            @patch('pandas.DataFrame.to_csv')
            def test_merge_csv_files_local(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                mock_exists.side_effect = lambda path: True
                mock_listdir.side_effect = lambda path: ['file1.csv', 'file2.csv']
                mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]}), pd.DataFrame({'col2': [3, 4]})]
                mock_concat.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

                output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                mock_copy.assert_any_call('path\\to\\driveA\\file1.csv', 'test_directory')
                mock_copy.assert_any_call('path\\to\\driveA\\file2.csv', 'test_directory')
                mock_read_csv.assert_any_call('test_directory/file1.csv')
                mock_read_csv.assert_any_call('test_directory/file2.csv')
                mock_concat.assert_called_once()
                mock_to_csv.assert_called_once_with('test_directory/file1_file2_merged.csv', index=False)
                mock_makedirs.assert_called_once_with('archive_path')
                mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
                mock_move.assert_any_call('test_directory/file2.csv', 'archive_path/file2.csv')
                assert output_file == 'test_directory/file1_file2_merged.csv'

            @patch('os.path.exists')
            @patch('os.listdir')
            @patch('shutil.copy')
            @patch('pandas.read_csv')
            @patch('pandas.concat')
            @patch('shutil.move')
            @patch('os.makedirs')
            @patch('pandas.DataFrame.to_csv')
            def test_merge_csv_files_remote(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                mock_exists.side_effect = lambda path: True
                class TestConnectionManager:

                    @pytest.fixture(autouse=True)
                    def setup(self):
                        self.app = MagicMock()
                        self.conn_manager = ConnectionManager(self.app, '192.168.1.1', 'user', 'password')

                    @patch('os.path.exists')
                    @patch('os.listdir')
                    @patch('shutil.copy')
                    @patch('pandas.read_csv')
                    @patch('pandas.concat')
                    @patch('shutil.move')
                    @patch('os.makedirs')
                    @patch('pandas.DataFrame.to_csv')
                    def test_merge_csv_files_local(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                        mock_exists.side_effect = lambda path: True
                        mock_listdir.side_effect = lambda path: ['file1.csv', 'file2.csv']
                        mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]}), pd.DataFrame({'col2': [3, 4]})]
                        mock_concat.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

                        output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                        mock_copy.assert_any_call('path\\to\\driveA\\file1.csv', 'test_directory')
                        mock_copy.assert_any_call('path\\to\\driveA\\file2.csv', 'test_directory')
                        mock_read_csv.assert_any_call('test_directory/file1.csv')
                        mock_read_csv.assert_any_call('test_directory/file2.csv')
                        mock_concat.assert_called_once()
                        mock_to_csv.assert_called_once_with('test_directory/file1_file2_merged.csv', index=False)
                        mock_makedirs.assert_called_once_with('archive_path')
                        mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
                        mock_move.assert_any_call('test_directory/file2.csv', 'archive_path/file2.csv')
                        assert output_file == 'test_directory/file1_file2_merged.csv'

                    @patch('os.path.exists')
                    @patch('os.listdir')
                    @patch('shutil.copy')
                    @patch('pandas.read_csv')
                    @patch('pandas.concat')
                    @patch('shutil.move')
                    @patch('os.makedirs')
                    @patch('pandas.DataFrame.to_csv')
                    def test_merge_csv_files_remote(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                        mock_exists.side_effect = lambda path: True
                        mock_listdir.side_effect = lambda path: ['file1.csv', 'file2.csv']
                        mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]}), pd.DataFrame({'col2': [3, 4]})]
                        mock_concat.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

                        with patch.object(self.conn_manager, 'transfer_all_csv_files') as mock_transfer:
                            output_file = self.conn_manager.merge_csv_files(False, 'test_directory', 'archive_path')

                            mock_transfer.assert_called_once()
                            mock_read_csv.assert_any_call('test_directory/file1.csv')
                            mock_read_csv.assert_any_call('test_directory/file2.csv')
                            mock_concat.assert_called_once()
                            mock_to_csv.assert_called_once_with('test_directory/file1_file2_merged.csv', index=False)
                            mock_makedirs.assert_called_once_with('archive_path')
                            mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
                            mock_move.assert_any_call('test_directory/file2.csv', 'archive_path/file2.csv')
                            assert output_file == 'test_directory/file1_file2_merged.csv'

                    @patch('os.path.exists')
                    @patch('os.listdir')
                    @patch('shutil.copy')
                    @patch('pandas.read_csv')
                    @patch('pandas.concat')
                    @patch('shutil.move')
                    @patch('os.makedirs')
                    @patch('pandas.DataFrame.to_csv')
                    def test_merge_csv_files_no_files(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                        mock_exists.side_effect = lambda path: True
                        mock_listdir.side_effect = lambda path: []

                        output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                        mock_copy.assert_not_called()
                        mock_read_csv.assert_not_called()
                        mock_concat.assert_not_called()
                        mock_to_csv.assert_not_called()
                        mock_makedirs.assert_called_once_with('archive_path')
                        mock_move.assert_not_called()
                        assert output_file is None

                    @patch('os.path.exists')
                    @patch('os.listdir')
                    @patch('shutil.copy')
                    @patch('pandas.read_csv')
                    @patch('pandas.concat')
                    @patch('shutil.move')
                    @patch('os.makedirs')
                    @patch('pandas.DataFrame.to_csv')
                    def test_merge_csv_files_single_file(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                        mock_exists.side_effect = lambda path: True
                        mock_listdir.side_effect = lambda path: ['file1.csv']
                        mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]})]
                        mock_concat.return_value = pd.DataFrame({'col1': [1, 2]})

                        output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                        mock_copy.assert_any_call('path\\to\\driveA\\file1.csv', 'test_directory')
                        mock_read_csv.assert_any_call('test_directory/file1.csv')
                        mock_concat.assert_called_once()
                        mock_to_csv.assert_called_once_with('test_directory/file1_merged.csv', index=False)
                        mock_makedirs.assert_called_once_with('archive_path')
                        mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
                        assert output_file == 'test_directory/file1_merged.csv'

                    @patch('os.path.exists')
                    @patch('os.listdir')
                    @patch('shutil.copy')
                    @patch('pandas.read_csv')
                    @patch('pandas.concat')
                    @patch('shutil.move')
                    @patch('os.makedirs')
                    @patch('pandas.DataFrame.to_csv')
                    def test_merge_csv_files_with_non_csv_files(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                        mock_exists.side_effect = lambda path: True
                        mock_listdir.side_effect = lambda path: ['file1.csv', 'file2.csv', 'file3.txt']
                        mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]}), pd.DataFrame({'col2': [3, 4]})]
                        mock_concat.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

                        output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                        mock_copy.assert_any_call('path\\to\\driveA\\file1.csv', 'test_directory')
                        mock_copy.assert_any_call('path\\to\\driveA\\file2.csv', 'test_directory')
                        mock_read_csv.assert_any_call('test_directory/file1.csv')
                        mock_read_csv.assert_any_call('test_directory/file2.csv')
                        mock_concat.assert_called_once()
                        mock_to_csv.assert_called_once_with('test_directory/file1_file2_merged.csv', index=False)
                        mock_makedirs.assert_called_once_with('archive_path')
                        mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
                        mock_move.assert_any_call('test_directory/file2.csv', 'archive_path/file2.csv')
                        assert output_file == 'test_directory/file1_file2_merged.csv'

                if __name__ == '__main__':
                    pytest.main()
            def test_merge_csv_files_no_files(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                mock_exists.side_effect = lambda path: True
                mock_listdir.side_effect = lambda path: []

                output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                mock_copy.assert_not_called()
                mock_read_csv.assert_not_called()
                mock_concat.assert_not_called()
                mock_to_csv.assert_not_called()
                mock_makedirs.assert_called_once_with('archive_path')
                mock_move.assert_not_called()
                assert output_file is None

            @patch('os.path.exists')
            @patch('os.listdir')
            @patch('shutil.copy')
            @patch('pandas.read_csv')
            @patch('pandas.concat')
            @patch('shutil.move')
            @patch('os.makedirs')
            @patch('pandas.DataFrame.to_csv')
            def test_merge_csv_files_single_file(self, mock_to_csv, mock_makedirs, mock_move, mock_concat, mock_read_csv, mock_copy, mock_listdir, mock_exists):
                mock_exists.side_effect = lambda path: True
                mock_listdir.side_effect = lambda path: ['file1.csv']
                mock_read_csv.side_effect = [pd.DataFrame({'col1': [1, 2]})]
                mock_concat.return_value = pd.DataFrame({'col1': [1, 2]})

                output_file = self.conn_manager.merge_csv_files(True, 'test_directory', 'archive_path')

                mock_copy.assert_any_call('path\\to\\driveA\\file1.csv', 'test_directory')
                mock_read_csv.assert_any_call('test_directory/file1.csv')
                mock_concat.assert_called_once()
                mock_to_csv.assert_called_once_with('test_directory/file1_merged.csv', index=False)
                mock_makedirs.assert_called_once_with('archive_path')
                mock_move.assert_any_call('test_directory/file1.csv', 'archive_path/file1.csv')
                assert output_file == 'test_directory/file1_merged.csv'

        if __name__ == '__main__':
            pytest.main()