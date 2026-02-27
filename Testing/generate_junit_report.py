#!/usr/bin/env python3
"""
generate_junit_report.py

Usage:
  python generate_junit_report.py frontend.xml backend.xml --css index.css --template report_template.html.j2 --js report.js --tag v1.0.0 --sha 97ffe28bb2a4c -o report.html

Generate a single-file HTML JUnit test report from one or more JUnit XML artifacts, suitable for CI/CD pipelines and static hosting.

This tool parses JUnit XML files, aggregates results, and renders a styled HTML report using a Jinja2 template and inlined CSS.

 -- Supports multiple JUnit XML inputs
 -- Handles <testsuite> and <testsuites> formats
 -- Graceful recovery for malformed or unexpected XML roots
 -- Aggregates pass / fail / skip / error counts
 -- Generates a stacked progress bar
  -- Interactive filtering and search for failures
 -- CI-friendly exit codes
 -- Produces a single self-contained HTML file
 
| Option             | Required | Description                                 |
| ------------------ | -------- | ------------------------------------------- |
| `xml_files`        | Yes        | One or more JUnit XML files                 |
| `--css`            | Yes        | Path to `index.css` (inlined into output)   |
| `--js`             | Yes        | Path to `report.js` (inlined into output)   |
| `--template`       | Yes        | Jinja2 HTML template                        |
| `-o`, `--out`      | Yes        | Output HTML file                            |
| `--tag`            | No         | Version or tag label (default: `v1.0.0`)    |
| `--sha`            | No         | Commit SHA shown in report                  |
| `--fail-exit-code` | No         | Exit with code `1` if failures/errors exist |
 
 Output
  -- HTML report with:
    ++ Overall summary
    ++ Pass / Fail / Error / Skip counts
    ++ Execution duration
    ++ Interactive failure list
  -- Exit codes
    ++ 0 → success
    1 → failures present (--fail-exit-code)
    2 → fatal error (IO, template, parsing)
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re

#Import Jinja2
try:
    from jinja2 import Environment, BaseLoader, select_autoescape
except ImportError:
    Environment = None

# Converts a value to a python float.
def parse_float(s, default=0.0):
    try:
        return float(s)
    except Exception:
        return default

# Formats a float durations into: 0.123456789s
def format_seconds(sec):
    try:
        return "{:.9f}s".format(float(sec))
    except Exception:
        return "0.000000000s"

# Normalizes a test case into a consistent dictionary format.
def make_case(source_file, suite_name, classname, test_name, time_s, status,
              kind="", message="", details=""):
    return {
        "source_file": source_file,
        "suite_name": suite_name,
        "classname": classname,
        "test_name": test_name,
        "time": float(time_s or 0.0),
        "status": status,   # pass | skip | failure | error
        "kind": kind,       # FAILURE | ERROR for display
        "message": message or "",
        "details": details or "",
    }

# Fallback helper that finds all <testsuite> elements anywhere in the XML tree.
# Used only when the XML root is non-standard.
def iter_all_suites(root):
    if root.tag == "testsuite":
        yield root
    for suite in root.findall(".//testsuite"):
        yield suite

# Parses a single JUnit XML file into normalized test case dictionaries.
def parse_junit_file(path):
    """
    Parse a JUnit XML file into normalized testcase dicts.

    Returns: (cases, warnings)
      cases: list[dict]
      warnings: list[str] (parse errors / oddities to show in report)
    """
    cases = []
    warnings = []
    source_file = os.path.basename(path)

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        warnings.append("Could not parse {}: {}".format(source_file, str(e)))
        return cases, warnings

    # Collect suites depending on root type
    suites = []
    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        # Include direct child suites and nested suites (some tools nest)
        suites = list(root.findall("testsuite"))
        for s in root.findall(".//testsuite"):
            if s not in suites:
                suites.append(s)
    else:
        # Unknown root, try to recover by finding suites anywhere
        suites = list(iter_all_suites(root))
        if not suites:
            warnings.append("No <testsuite> elements found in {}".format(source_file))
            return cases, warnings

    # For each suite, gather testcases
    for suite in suites:
        suite_name = suite.attrib.get("name") or "(unnamed suite)"

        # Note: using .//testcase because some XML nests them
        for tc in suite.findall(".//testcase"):
            classname = tc.attrib.get("classname") or ""
            test_name = tc.attrib.get("name") or "(unnamed test)"
            time_s = parse_float(tc.attrib.get("time", "0"), default=0.0)

            skipped_elem = tc.find("skipped")
            failure_elem = tc.find("failure")
            error_elem = tc.find("error")

            if skipped_elem is not None:
                cases.append(make_case(
                    source_file, suite_name, classname, test_name, time_s, "skip"
                ))
                continue

            if failure_elem is not None:
                msg = (failure_elem.attrib.get("message")
                       or failure_elem.attrib.get("type")
                       or "")
                details = (failure_elem.text or "").strip()
                cases.append(make_case(
                    source_file, suite_name, classname, test_name, time_s,
                    status="failure", kind="FAILURE",
                    message=msg.strip(), details=details
                ))
                continue

            if error_elem is not None:
                msg = (error_elem.attrib.get("message")
                       or error_elem.attrib.get("type")
                       or "")
                details = (error_elem.text or "").strip()
                cases.append(make_case(
                    source_file, suite_name, classname, test_name, time_s,
                    status="error", kind="ERROR",
                    message=msg.strip(), details=details
                ))
                continue

            cases.append(make_case(
                source_file, suite_name, classname, test_name, time_s, "pass"
            ))

    return cases, warnings

# Aggregates all test cases into summary statistics.
def compute_summary(cases):
    total = len(cases)
    passed = sum(1 for c in cases if c["status"] == "pass")
    skipped = sum(1 for c in cases if c["status"] == "skip")
    failed = sum(1 for c in cases if c["status"] == "failure")
    errors = sum(1 for c in cases if c["status"] == "error")
    duration = sum(c.get("time") or 0.0 for c in cases)

    overall = "FAIL" if (failed + errors) > 0 else "PASS"    

    def pct(n):
        return 0.0 if total == 0 else (100.0 * float(n) / float(total))

    # For the stacked bar we want percentages per segment
    return {
        "overall": overall,
        "total": total,
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "errors": errors,
        "duration": duration,
        "pct_pass": pct(passed),
        "pct_skip": pct(skipped),
        "pct_fail": pct(failed),
        "pct_err": pct(errors),
    }

# Compute Suite-level summary.

# Normalization utility that converts an arbitrary string into a safe, 
#     deterministic identifier suitable for use in HTML attributes, CSS 
#     selectors, and JavaScript hooks.
def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "suite"

# Returns a sorted list of suite summary dicts.
def compute_suite_summaries(cases):
    by_suite = {}
    for c in cases:
        name = c.get("suite_name") or "(unnamed suite)"
        rec = by_suite.setdefault(name, {"cases": [], "sources": set()})
        rec["cases"].append(c)
        if c.get("source_file"):
            rec["sources"].add(c["source_file"])

    suite_rows = []
    for suite_name, rec in by_suite.items():
        suite_cases = rec["cases"]
        s = compute_summary(suite_cases)

        bad = [c for c in suite_cases if c.get("status") in ("failure", "error")]
        bad.sort(key=sort_key)
        bad_preview = bad[:5]

        suite_rows.append({
            "suite_name": suite_name,
            "suite_id": slugify(suite_name),
            "overall": s["overall"],
            "total": s["total"],
            "passed": s["passed"],
            "failed": s["failed"],
            "errors": s["errors"],
            "skipped": s["skipped"],
            "duration": s["duration"],
            "duration_fmt": format_seconds(s["duration"]),
            "sources": sorted(rec["sources"]),
            "bad_preview": bad_preview,
        })

    suite_rows.sort(key=lambda r: (r["suite_name"] or "").lower())
    return suite_rows

# Provides deterministic sorting for failure/error cases.
def sort_key(case):
    return (
        case.get("source_file") or "",
        case.get("suite_name") or "",
        case.get("classname") or "",
        case.get("test_name") or "",
        case.get("status") or "",
    )

# Renders the final HTML report using Jinja2.
def render_html_report(summary, cases, parse_warnings, base_css, template_text, inline_js, tag, sha):
    if Environment is None:
        raise RuntimeError("Jinja2 is required. Install with: pip install jinja2")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    bad_cases = [c for c in cases if c["status"] in ("failure", "error")]
    bad_cases.sort(key=sort_key)
    
    suite_rows = compute_suite_summaries(cases)

    overall_dot = "good" if summary["overall"] == "PASS" else "bad"

    # Combine errors into fail for the bar
    bar_pass = summary["pct_pass"]
    bar_skip = summary["pct_skip"]
    bar_fail = summary["pct_fail"] + summary["pct_err"]

    bar_tooltip = "Pass: {:.0f}% • Skip: {:.0f}% • Fail: {:.0f}%".format(
        bar_pass, bar_skip, bar_fail
    )

    env = Environment(
        loader=BaseLoader(),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    tmpl = env.from_string(template_text)

    return tmpl.render(
        base_css=base_css.rstrip(),
        generated=now,
        tag=tag,
        sha=sha,
        inline_js=inline_js,
        summary=summary,
        duration=format_seconds(summary["duration"]),
        overall_dot=overall_dot,
        bar_pass=bar_pass,
        bar_skip=bar_skip,
        bar_fail=bar_fail,
        bar_tooltip=bar_tooltip,
        warnings=parse_warnings,
        bad_cases=bad_cases,
        suite_rows=suite_rows,
    )


# Reads UTF-8 text files with contextual error messages and loading CSS.
def read_text_file(path, label):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError("Could not read {} ({}): {}".format(label, path, e))

# Writes the final HTML output and ensures directories exist.
def write_text_file(path, content):
    # Make output directory if needed
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

# Kiads the Jinja2 template from disk.        
def load_template_text(path):
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Defines and validates all CLI arguments.
def build_arg_parser():
    p = argparse.ArgumentParser(
        description="Generate a single-file HTML report from one or more JUnit XML files."
    )
    p.add_argument(
        "xml_files",
        nargs="+",
        help="One or more JUnit XML files (e.g., frontend.xml backend.xml)"
    )
    p.add_argument(
        "--css",
        required=True,
        help="Path to index.css (base theme; inlined into output)"
    )
    p.add_argument(
        "-o", "--out",
        required=True,
        help="Output HTML file path (e.g., report.html)"
    )
    p.add_argument(
        "--fail-exit-code",
        action="store_true",
        help="Exit with code 1 if overall FAIL. Default: always 0."
    )
    p.add_argument(
        "--template",
        default=None,
        help="Optional path to a Jinja2 HTML template (.j2). If omitted, uses the built-in template."
    )
    p.add_argument(
        "--tag",
        default="v1.0.0",
        help="Tag label shown in header"
    )
    p.add_argument(
        "--sha", 
        default="unknown", 
        help="SHA shown in header"
    )
    p.add_argument(
        "--js",
        required=True,
        default=None,
        help="Optional path to a JavaScript file to inline into the HTML report. "
             "If omitted, uses the built-in JS."
    )

    return p


def main(argv):
    args = build_arg_parser().parse_args(argv)
    
    # Read base CSS
    try:
        base_css = read_text_file(args.css, "CSS")
    except RuntimeError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
        
    # Parse all XML files
    all_cases = []
    warnings = []
    for xml_path in args.xml_files:
        if not os.path.exists(xml_path):
            warnings.append("XML file not found: {}".format(os.path.basename(xml_path)))
            continue

        cases, w = parse_junit_file(xml_path)
        all_cases.extend(cases)
        warnings.extend(w)
    
    summary = compute_summary(all_cases)
    
    template_text = load_template_text(args.template)
    if template_text is None:
        # If you want a built-in fallback template, store it in a TEMPLATE_STR constant.
        # For now, require --template:
        raise RuntimeError("Provide --template report_template.html.j2")
        
    inline_js = read_text_file(args.js, "JavaScript")
    if inline_js is None:
        raise RuntimeError("Provide --js report.js")

    html_out = render_html_report(
        summary=summary,
        cases=all_cases,
        parse_warnings=warnings,
        base_css=base_css,
        template_text=template_text,
        inline_js=inline_js,
        tag=args.tag,
        sha=args.sha,
    )

    try:
        write_text_file(args.out, html_out)
    except Exception as e:
        print("ERROR: could not write output HTML {}: {}".format(args.out, e), file=sys.stderr)
        return 2

    #fail the step if overall FAIL
    if args.fail_exit_code and summary["overall"] == "FAIL":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
