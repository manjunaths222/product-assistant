"""
Run Codex analysis in a subprocess using the cloned repo as the working directory.
Based on jira-planbot implementation
"""

import os
import subprocess
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def run_codex_in_terminal(repo_path: str, requirement_summary: str) -> str:
    """
    Run Codex analysis in a separate process with cwd set to the cloned repo.

    Args:
        repo_path: Path to the cloned repository
        requirement_summary: Requirement description/query

    Returns:
        Analysis text (stdout) or an empty string on failure.
    """
    if not repo_path:
        logger.warning("No repo_path provided for terminal Codex analysis.")
        return ""

    # Ensure PYTHONPATH points to the project root (parent of "app")
    env = os.environ.copy()
    output_path = f"/tmp/codex_last_message_{os.getpid()}_{int(time.time())}.txt"

    prompt = f"""
You are an expert software architect and senior engineer analyzing a production codebase.

Rules:
- Read-only analysis
- Do NOT write or modify code
- Do NOT run destructive commands
- Estimation MUST strictly be based on the assumption that agentic tools (Codex, Cursor, GitHub Copilot, or similar AI coding assistants) will be used during development. Do NOT estimate as if coding manually.
- Estimation must include breakdown of dev effort, testing effort, documentation effort, etc. Make sure to include all the details in the estimation.

Task:
- Identify impacted modules and files
- Highlight existing patterns
- Call out risks, edge cases, tech debt
- Mention testing implications
- Provide a high-level design approach and technical implementation strategy
- Provide an estimation (story points + time in hours) and complexity/risk assessment

Requirement/Query:
{requirement_summary or ""}

Respond in the following format:

1. Impacted Files
2. Existing Patterns
3. Risks & Edge Cases
4. Test Considerations
5. Architectural Design
6. Technical Approach
7. Estimation (MUST follow story point mapping):
   - Total Time (hours): [calculate first, assuming agentic tools]
   - Story Points: [map using: 1=2-3h, 2=<1day, 3=2-3days, 5=<1week, 8=<1sprint, 13=danger]
   - Breakdown: Dev (Xh), Testing (Xh), Docs (Xh), Review (Xh), Deploy (Xh)
   - Complexity: [Low/Medium/High]
   - Risks: [list specific risks]
8. Task Breakdown
   - List of specific, actionable subtasks
   - Each task should reference specific files/modules
9. Dependencies
10. Acceptance Criteria

""".strip()

    try:
        result = subprocess.run(
            [
                "codex",
                "exec",
                "-C",
                repo_path,
                "--sandbox",
                "read-only",
                "--color",
                "never",
                "--output-last-message",
                output_path,
                "-",
            ],
            cwd=repo_path,
            env=env,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                "Terminal Codex analysis failed (rc=%s): %s",
                result.returncode,
                (result.stderr or "").strip(),
            )
            return ""

        try:
            output_file = Path(output_path)
            if output_file.exists():
                return output_file.read_text(errors="ignore").strip()
        except Exception as read_error:
            logger.warning("Failed to read Codex output file: %s", str(read_error))

        return (result.stdout or "").strip()
    except Exception as e:
        logger.error(f"Error running terminal Codex analysis: {str(e)}", exc_info=True)
        return ""

