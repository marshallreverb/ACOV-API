# ACOV-API

Python helpers for reading and creating COVADIS plan-axis elements through
AutoCAD COM.

## Requirements

- Windows with AutoCAD and COVADIS installed.
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
