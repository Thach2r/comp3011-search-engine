import pytest
import runpy
from unittest.mock import patch, MagicMock
from src.main import run


class TestMain:

    def test_quit_command(self, capsys):
        """run() should exit cleanly on 'quit' command."""
        with patch("builtins.input", side_effect=["quit"]):
            run()
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    def test_unknown_command(self, capsys):
        """run() should handle unknown commands gracefully."""
        with patch("builtins.input", side_effect=["badcommand", "quit"]):
            run()
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_empty_input(self, capsys):
        """run() should handle empty input without crashing."""
        with patch("builtins.input", side_effect=["", "quit"]):
            run()
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    def test_print_without_index(self, capsys):
        """print command should warn if no index loaded."""
        with patch("builtins.input", side_effect=["print good", "quit"]):
            run()
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_find_without_index(self, capsys):
        """find command should warn if no index loaded."""
        with patch("builtins.input", side_effect=["find good", "quit"]):
            run()
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_print_without_argument(self, capsys):
        """print command without a word should show usage."""
        with patch("builtins.input", side_effect=["print", "quit"]):
            run()
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_find_without_argument(self, capsys):
        """find command without a word should show usage."""
        with patch("builtins.input", side_effect=["find", "quit"]):
            run()
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_load_command(self, capsys):
        """load command should call load_index."""
        mock_index = {"hello": {}}
        with patch("src.main.load_index", return_value=(mock_index, {})):
            with patch("builtins.input", side_effect=["load", "quit"]):
                run()
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    def test_build_command(self, capsys):
        """build command should call crawl, build_index, save_index."""
        with patch("src.main.crawl", return_value={"http://a.com": "<p>hello</p>"}):
            with patch("src.main.save_index"):
                with patch("builtins.input", side_effect=["build", "quit"]):
                    run()
        captured = capsys.readouterr()
        assert "Index built" in captured.out

    def test_keyboard_interrupt(self, capsys):
        """run() should handle KeyboardInterrupt gracefully."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            run()
        captured = capsys.readouterr()
        assert "Exiting" in captured.out

    def test_print_with_loaded_index(self, capsys):
        """print command should call print_word when index is loaded."""
        mock_index = {"good": {"http://page1.com": {"count": 1, "positions": [0]}}}
        with patch("src.main.load_index", return_value=(mock_index, {})):
            with patch("builtins.input", side_effect=["load", "print good", "quit"]):
                run()
        captured = capsys.readouterr()
        assert "good" in captured.out

    def test_find_with_loaded_index(self, capsys):
        """find command should call find_pages when index is loaded."""
        mock_index = {"good": {"http://page1.com": {"count": 1, "positions": [0]}}}
        with patch("src.main.load_index", return_value=(mock_index, {})):
            with patch("builtins.input", side_effect=["load", "find good", "quit"]):
                run()
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    def test_main_entrypoint_runs(self, capsys):
        """Running src.main as a script should call run()."""
        with patch("builtins.input", side_effect=["quit"]):
            runpy.run_path("src/main.py", run_name="__main__")
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out
