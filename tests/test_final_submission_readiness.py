"""Final Phase 24 submission readiness test suite."""

import re
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestSubmissionReadiness:
    """Test suite ensuring complete repository readiness for Hiver evaluation."""

    def test_phase_24_scripts_execute_cleanly(self):
        """Verify quickstart, smoke test, and audit scripts exit with status 0."""
        scripts_to_test = [
            REPO_ROOT / "scripts" / "quickstart.py",
            REPO_ROOT / "scripts" / "final_smoke_test.py",
            REPO_ROOT / "scripts" / "final_assignment_audit.py",
            REPO_ROOT / "scripts" / "validate_final_report.py",
        ]
        for script in scripts_to_test:
            assert script.exists(), f"Script missing: {script}"
            res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
            assert res.returncode == 0, f"Script {script.name} failed with stderr: {res.stderr}\nstdout: {res.stdout}"

    def test_run_agent_demo_execution(self):
        """Verify run_agent.py --demo runs and produces structured decision card."""
        script = REPO_ROOT / "scripts" / "run_agent.py"
        res = subprocess.run([sys.executable, str(script), "--demo"], capture_output=True, text=True)
        assert res.returncode == 0
        assert "AI SUPPORT AGENT DEMO" in res.stdout
        assert "Final Decision:" in res.stdout
        assert "AUTO_HANDLE" in res.stdout
        assert "ESCALATE_TO_HUMAN" in res.stdout

    def test_mandatory_phase_24_documents_exist(self):
        """Verify presence of all Phase 24 summary and readiness documents."""
        docs = [
            REPO_ROOT / "demo" / "README.md",
            REPO_ROOT / "reports" / "final_interview_cheatsheet.md",
            REPO_ROOT / "reports" / "final_submission_checklist.md",
            REPO_ROOT / "reports" / "notion_submission_notes.md",
            REPO_ROOT / "reports" / "final_project_readiness.md",
            REPO_ROOT / "reports" / "final_file_inventory.md",
        ]
        for d in docs:
            assert d.exists(), f"Mandatory document missing: {d}"

    def test_no_api_keys_or_secrets_in_tracked_files(self):
        """Audit repository to verify zero real API keys or tokens exist in tracked files."""
        sensitive_patterns = [
            re.compile(r"sk-[a-zA-Z0-9]{20,}"),
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        ]
        # Check text files in repo (excluding .git)
        for p in REPO_ROOT.rglob("*.py"):
            if ".venv" in p.parts or "__pycache__" in p.parts:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for pat in sensitive_patterns:
                assert not pat.search(text), f"Found potential secret in {p}"

        for p in REPO_ROOT.rglob("*.md"):
            if ".venv" in p.parts:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for pat in sensitive_patterns:
                assert not pat.search(text), f"Found potential secret in {p}"

    def test_readme_relative_links_resolve(self):
        """Verify that markdown links in README.md point to actual existing files."""
        readme = REPO_ROOT / "README.md"
        text = readme.read_text(encoding="utf-8")
        # Find local markdown links e.g. [text](reports/...) or [text](DECISION_LOG.md)
        local_links = re.findall(r"\[.*?\]\(((?!http|#|mailto).*?)\)", text)
        for link in local_links:
            # Strip anchors if any
            clean_link = link.split("#")[0].strip()
            if clean_link:
                target = REPO_ROOT / clean_link
                assert target.exists(), f"Broken relative link in README: {clean_link}"
