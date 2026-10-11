import math
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


Point3D = tuple[float, float, float]


@dataclass(frozen=True)
class AxisElement:
    kind: str
    points: tuple[Point3D, ...]
    radius: float | None = None


def _format_point(point: Sequence[float]) -> str:
    if len(point) not in (2, 3):
        raise ValueError("Un point doit contenir deux ou trois coordonnées.")

    coordinates = tuple(float(value) for value in point)
    if not all(math.isfinite(value) for value in coordinates):
        raise ValueError("Les coordonnées doivent être des nombres finis.")
    if len(coordinates) == 2:
        coordinates += (0.0,)
    return ",".join(format(value, ".15g") for value in coordinates)


def create_covadis_axis_line_2pts(
    document: object,
    start_point: Sequence[float],
    end_point: Sequence[float],
) -> None:
    start = _format_point(start_point)
    end = _format_point(end_point)
    document.SendCommand(f"_CovaAxePlanLigne2Pts\n{start}\n{end}\n")


def _lisp_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _parse_axis_export(contents: str) -> list[AxisElement]:
    elements: list[AxisElement] = []
    for line in contents.splitlines():
        if line == "END":
            return elements
        fields = line.split("|")
        if fields[0] == "ERROR":
            raise RuntimeError("|".join(fields[1:]))

        kind = fields[0]
        expected_point_count = {"LIGNE": 2, "ARC": 3}.get(kind)
        if expected_point_count is None:
            raise ValueError(f"Type d'élément COVADIS inconnu : {kind}")
        expected_field_count = expected_point_count + (2 if kind == "ARC" else 1)
        if len(fields) != expected_field_count:
            raise ValueError(f"Enregistrement COVADIS incomplet : {line}")

        points: list[Point3D] = []
        for field in fields[1 : expected_point_count + 1]:
            coordinates = tuple(float(value) for value in field.split(","))
            if len(coordinates) != 3:
                raise ValueError(f"Coordonnée 3D invalide : {field}")
            points.append((coordinates[0], coordinates[1], coordinates[2]))

        radius = float(fields[-1]) if kind == "ARC" else None
        elements.append(AxisElement(kind, tuple(points), radius))

    raise ValueError("L'export COVADIS ne contient pas de marqueur de fin.")


def read_selected_covadis_axis(
    document: object, timeout: float = 15.0
) -> list[AxisElement]:
    entity, _ = document.Utility.GetEntity(
        None, "\nSélectionnez l'axe en plan COVADIS à lire : "
    )
    output_path = Path(tempfile.gettempdir()) / f"covadis-axis-{uuid.uuid4().hex}.txt"
    handle = str(entity.Handle)
    quoted_path = _lisp_string(str(output_path))
    quoted_handle = _lisp_string(handle)
    lisp = f"""
(defun cv:take-10 (l n / out)
  (while (and l (< (length out) n))
    (if (= (caar l) 10) (setq out (append out (list (cdar l))))
      )
    (setq l (cdr l)))
  out)
(defun cv:axe-elements (en / l res pts rad)
  (setq l (entget en '("*")))
  (while l
    (cond
      ((equal (car l) '(1 . "CAxePlanLigne"))
       (setq pts (cv:take-10 (cdr l) 2))
       (setq res (cons (list 'LIGNE (car pts) (cadr pts)) res)))
      ((equal (car l) '(1 . "CAxePlanArc"))
       (setq pts (cv:take-10 (cdr l) 4)
             rad (cdr (assoc 40 (cdr l))))
       (setq res (cons (list 'ARC (car pts) (caddr pts) (cadddr pts) rad) res))))
    (setq l (cdr l)))
  (reverse res))
(defun cv:point-text (p)
  (strcat (rtos (car p) 2 8) "," (rtos (cadr p) 2 8) ","
          (rtos (if (caddr p) (caddr p) 0.0) 2 8)))
(defun cv:export-axis (path handle / file en item items)
  (setq file (open path "w"))
  (if file
    (progn
      (setq en (handent handle))
      (if en
        (progn
          (setq items (cv:axe-elements en))
          (if items
            (foreach item items
              (cond
                ((eq (car item) 'LIGNE)
                 (write-line
                   (strcat "LIGNE|" (cv:point-text (cadr item)) "|"
                           (cv:point-text (caddr item))) file))
                ((eq (car item) 'ARC)
                 (write-line
                   (strcat "ARC|" (cv:point-text (cadr item)) "|"
                           (cv:point-text (caddr item)) "|"
                           (cv:point-text (cadddr item)) "|"
                           (rtos (nth 4 item) 2 8)) file))))
            (write-line "ERROR|No COVADIS axis elements found." file)))
        (write-line "ERROR|Entity handle not found." file))
      (write-line "END" file)
      (close file))))
(cv:export-axis {quoted_path} {quoted_handle})
"""
    try:
        document.SendCommand(lisp + "\n")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if output_path.is_file():
                contents = output_path.read_text(encoding="utf-8")
                if "END" in contents.splitlines():
                    return _parse_axis_export(contents)
            time.sleep(0.1)
        raise TimeoutError(
            "AutoCAD n'a pas terminé l'export de l'axe COVADIS "
            f"dans le délai de {timeout:g} s."
        )
    finally:
        output_path.unlink(missing_ok=True)
