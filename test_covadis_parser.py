import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from covadis_parser import (
    AxisElement,
    _format_point,
    _parse_axis_export,
    create_covadis_axis_line_2pts,
    read_selected_covadis_axis,
)


class ParseAxisExportTests(unittest.TestCase):
    def test_parses_line_and_arc_elements(self) -> None:
        result = _parse_axis_export(
            "LIGNE|1,2,0|3,4,0\n"
            "ARC|4,5,0|6,7,0|8,9,0|12.5\n"
            "END\n"
        )

        self.assertEqual(
            result,
            [
                AxisElement("LIGNE", ((1.0, 2.0, 0.0), (3.0, 4.0, 0.0))),
                AxisElement(
                    "ARC",
                    (
                        (4.0, 5.0, 0.0),
                        (6.0, 7.0, 0.0),
                        (8.0, 9.0, 0.0),
                    ),
                    12.5,
                ),
            ],
        )

    def test_parses_empty_axis(self) -> None:
        self.assertEqual(_parse_axis_export("END\n"), [])

    def test_reports_export_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Entity handle not found"):
            _parse_axis_export("ERROR|Entity handle not found.\nEND\n")

    def test_rejects_unknown_element_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Type d'élément"):
            _parse_axis_export("SPLINE|1,2,0\nEND\n")

    def test_rejects_incomplete_line_record(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplet"):
            _parse_axis_export("LIGNE|1,2,0\nEND\n")

    def test_rejects_point_without_three_coordinates(self) -> None:
        with self.assertRaisesRegex(ValueError, "Coordonnée 3D"):
            _parse_axis_export("LIGNE|1,2|3,4,0\nEND\n")

    def test_requires_end_marker(self) -> None:
        with self.assertRaisesRegex(ValueError, "marqueur de fin"):
            _parse_axis_export("LIGNE|1,2,0|3,4,0\n")


class PointAndCommandTests(unittest.TestCase):
    def test_formats_two_and_three_dimensional_points(self) -> None:
        self.assertEqual(_format_point((1, 2)), "1,2,0")
        self.assertEqual(_format_point((1.25, -2, 3)), "1.25,-2,3")

    def test_rejects_wrong_point_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "deux ou trois"):
            _format_point((1,))

    def test_rejects_non_finite_coordinates(self) -> None:
        with self.assertRaisesRegex(ValueError, "nombres finis"):
            _format_point((float("nan"), 2))

    def test_sends_covadis_line_command_and_points(self) -> None:
        document = SimpleNamespace(sent_command=None)
        document.SendCommand = lambda command: setattr(
            document, "sent_command", command
        )

        create_covadis_axis_line_2pts(document, (0, 0), (10, 5))

        self.assertEqual(
            document.sent_command,
            "_CovaAxePlanLigne2Pts\n0,0,0\n10,5,0\n",
        )


class ReadSelectedAxisTests(unittest.TestCase):
    def test_selects_axis_parses_export_and_removes_temporary_file(self) -> None:
        class Document:
            def __init__(self) -> None:
                self.Utility = Mock()
                self.Utility.GetEntity.return_value = (
                    SimpleNamespace(Handle="AB12"),
                    (0.0, 0.0, 0.0),
                )

            def SendCommand(self, command: str) -> None:
                self.command = command
                self.output_path.write_text(
                    "LIGNE|1,2,0|3,4,0\nEND\n", encoding="utf-8"
                )

        with tempfile.TemporaryDirectory() as directory:
            document = Document()
            document.output_path = Path(directory) / "covadis-axis-test.txt"
            with patch("covadis_parser.tempfile.gettempdir", return_value=directory):
                with patch(
                    "covadis_parser.uuid.uuid4",
                    return_value=SimpleNamespace(hex="test"),
                ):
                    result = read_selected_covadis_axis(document)

        self.assertEqual(
            result,
            [AxisElement("LIGNE", ((1.0, 2.0, 0.0), (3.0, 4.0, 0.0)))],
        )
        self.assertIn("(handent handle)", document.command)
        self.assertFalse(document.output_path.exists())


if __name__ == "__main__":
    unittest.main()
