"""Process-level CLI discovery, help and failure contracts."""

import json
import subprocess
import sys

from semrush_web_mcp.server import REPORTS


def run(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "semrush_web_mcp.cli", *arguments],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_cli_discovery_matches_the_mcp_catalog():
    result = run("reports", "--json")
    assert result.returncode == 0, result.stderr
    catalog = json.loads(result.stdout)
    assert {item["name"] for item in catalog} == set(REPORTS)
    assert result.stderr == ""
    for item in catalog:
        assert item["input_schema"] == REPORTS[item["name"]].query.model_json_schema()


def test_native_command_help_lists_query_flags():
    result = run("keyword-ideas", "--help")
    assert result.returncode == 0
    assert "--keyword" in result.stdout
    assert "--questions-only" in result.stdout
    assert "--database" in result.stdout
    assert "--json" in result.stdout


def test_invalid_query_fails_before_contacting_a_browser():
    result = run(
        "keyword-ideas",
        "--keyword",
        "seo",
        "--limit",
        "-1",
        "--cdp-url",
        "http://127.0.0.1:1",
        "--json",
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "browser unavailable" not in result.stderr
    assert "limit" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_browser_is_a_clean_report_failure():
    result = run("account-status", "--cdp-url", "http://127.0.0.1:1", "--json")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "browser unavailable" in result.stderr
    assert "Traceback" not in result.stderr


def test_json_array_arguments_validate_before_browser_connection():
    result = run("keyword-gap", "--domains", '["openai.com"]', "--cdp-url", "http://127.0.0.1:1")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "domains" in result.stderr
    assert "browser unavailable" not in result.stderr
    assert "Traceback" not in result.stderr
