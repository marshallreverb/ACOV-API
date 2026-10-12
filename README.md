# ACOV-API

Python helpers for reading and creating Autocad elements through
AutoCAD COM.

## Requirements

- Windows with AutoCAD  installed.
- Python with `pywin32` installed.

## Usage

```python
from covadis_parser import (
    create_covadis_axis_line_2pts,
    read_selected_covadis_axis,
)

# `document` is an open AutoCAD COM document.
axis_elements = read_selected_covadis_axis(document)
create_covadis_axis_line_2pts(document, (0, 0), (100, 50))
```

`read_selected_covadis_axis` prompts for an existing COVADIS axis and returns
`AxisElement` values for its lines and arcs. The line-creation helper sends
`_CovaAxePlanLigne2Pts` and the two supplied points to AutoCAD.

To run an AutoCAD command and capture the new text in AutoCAD's command log:

```python
from cmd_reader import read_autocad_command_output

output = read_autocad_command_output(document, "_.-LAYER\n?\n*\n")
print(output)
```

The reader temporarily enables AutoCAD command logging when it is disabled,
waits for the command to finish, returns only the newly logged text, and
restores the previous logging mode. It requires a command that completes
without waiting for interactive input.

For the project workflow covering AutoCAD/COVADIS drawing, command-output
reading, topographic point validation, and axis helpers, see
[the AutoCAD drafting skill](.github/skills/autocad-drafting/SKILL.md).
