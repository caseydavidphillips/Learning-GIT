#!/usr/bin/env python3
"""Generate a simple HTML dashboard from JUnit XML test reports."""

from __future__ import annotations

import argparse
import html
import pathlib
import xml.etree.ElementTree as ET


def parse_junit_file(path: pathlib.Path) -> dict:
    root = ET.parse(path).getroot()

    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    if not suites:
        suites = [root]

    total = failures = errors = skipped = 0
    suite_rows = []
    case_rows = []

    for suite in suites:
        suite_name = suite.get("name", path.stem)
        suite_tests = int(suite.get("tests", "0"))
        suite_failures = int(suite.get("failures", "0"))
        suite_errors = int(suite.get("errors", "0"))
        suite_skipped = int(suite.get("skipped", "0"))

        total += suite_tests
        failures += suite_failures
        errors += suite_errors
        skipped += suite_skipped

        suite_rows.append(
            {
                "file": str(path),
                "name": suite_name,
                "tests": suite_tests,
                "failures": suite_failures,
                "errors": suite_errors,
                "skipped": suite_skipped,
            }
        )

        for case in suite.findall("testcase"):
            status = "passed"
            message = ""

            node = case.find("failure")
            if node is not None:
                status = "failure"
                message = node.get("message", "") or (node.text or "")
            else:
                node = case.find("error")
                if node is not None:
                    status = "error"
                    message = node.get("message", "") or (node.text or "")
                else:
                    node = case.find("skipped")
                    if node is not None:
                        status = "skipped"
                        message = node.get("message", "") or (node.text or "")

            case_rows.append(
                {
                    "suite": suite_name,
                    "name": case.get("name", "unnamed"),
                    "classname": case.get("classname", ""),
                    "time": case.get("time", "0"),
                    "status": status,
                    "message": (message or "").strip(),
                }
            )

    return {
        "total": total,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": max(total - failures - errors - skipped, 0),
        "suites": suite_rows,
        "cases": case_rows,
    }


def render_html(report_data: list[dict]) -> str:
    total = sum(d["total"] for d in report_data)
    failures = sum(d["failures"] for d in report_data)
    errors = sum(d["errors"] for d in report_data)
    skipped = sum(d["skipped"] for d in report_data)
    passed = sum(d["passed"] for d in report_data)

    suite_rows = []
    case_rows = []

    for data in report_data:
        for suite in data["suites"]:
            suite_rows.append(
                "<tr>"
                f"<td>{html.escape(suite['file'])}</td>"
                f"<td>{html.escape(suite['name'])}</td>"
                f"<td>{suite['tests']}</td>"
                f"<td>{suite['failures']}</td>"
                f"<td>{suite['errors']}</td>"
                f"<td>{suite['skipped']}</td>"
                "</tr>"
            )

        for case in data["cases"]:
            css = "ok" if case["status"] == "passed" else "bad"
            case_rows.append(
                "<tr>"
                f"<td>{html.escape(case['suite'])}</td>"
                f"<td>{html.escape(case['name'])}</td>"
                f"<td>{html.escape(case['classname'])}</td>"
                f"<td class='{css}'>{html.escape(case['status'])}</td>"
                f"<td>{html.escape(case['time'])}</td>"
                f"<td><pre>{html.escape(case['message'])}</pre></td>"
                "</tr>"
            )

    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>Test Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f0f0; }}
    .ok {{ color: #157f1f; font-weight: bold; }}
    .bad {{ color: #b00020; font-weight: bold; }}
    pre {{ margin: 0; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Unit Test Report</h1>
  <p><strong>Total:</strong> {total} | <strong>Passed:</strong> {passed} | <strong>Failures:</strong> {failures} | <strong>Errors:</strong> {errors} | <strong>Skipped:</strong> {skipped}</p>

  <h2>Suites</h2>
  <table>
    <thead>
      <tr><th>File</th><th>Suite</th><th>Tests</th><th>Failures</th><th>Errors</th><th>Skipped</th></tr>
    </thead>
    <tbody>
      {''.join(suite_rows)}
    </tbody>
  </table>

  <h2>Test Cases</h2>
  <table>
    <thead>
      <tr><th>Suite</th><th>Name</th><th>Classname</th><th>Status</th><th>Time (s)</th><th>Message</th></tr>
    </thead>
    <tbody>
      {''.join(case_rows)}
    </tbody>
  </table>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HTML report from JUnit XML files.")
    parser.add_argument("xml", nargs="+", help="One or more JUnit XML files")
    parser.add_argument("--output", default="report.html", help="Output HTML file path")
    args = parser.parse_args()

    xml_paths = [pathlib.Path(p) for p in args.xml]
    missing = [str(p) for p in xml_paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing XML files: {', '.join(missing)}")

    report_data = [parse_junit_file(path) for path in xml_paths]
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(report_data), encoding="utf-8")
    print(f"Wrote HTML report to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
