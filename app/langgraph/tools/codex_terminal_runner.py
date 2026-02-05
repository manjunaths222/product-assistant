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
You are a product strategist and business analyst helping a product manager understand the feasibility and effort required for a new feature or requirement.

Rules:
- Read-only analysis
- Do NOT write or modify code
- Do NOT run destructive commands
- Write for product managers, NOT engineers
- Focus on business impact, user experience, and product considerations
- Use plain language - avoid technical jargon when possible
- Estimation MUST strictly be based on the assumption that agentic tools (Codex, Cursor, GitHub Copilot, or similar AI coding assistants) will be used during development. Do NOT estimate as if coding manually.
- Estimation must be deterministic - similar complexities should yield similar estimates

Task:
- Identify what parts of the product/system will be affected (in business terms)
- Highlight existing capabilities and patterns that can be leveraged
- Call out business risks, user experience concerns, and product implications
- Mention testing and quality assurance considerations from a product perspective
- Provide a high-level product approach (what will users experience, what capabilities will be enabled)
- Provide an estimation (story points + time in hours) and complexity/risk assessment

Requirement/Query:
{requirement_summary or ""}

Respond in the following format:

1. Product Impact
   - What parts of the product/user experience will be affected?
   - What new capabilities will be enabled?
   - What user workflows or features will change?

2. Existing Capabilities
   - What existing features or patterns can be leveraged?
   - What similar functionality already exists?

3. Business Risks & Considerations
   - What are the main risks from a product/business perspective?
   - What edge cases or user scenarios need special consideration?
   - What product decisions are needed?

4. Quality Assurance Considerations
   - What testing scenarios are important from a user/product perspective?
   - What quality gates should be considered?

5. High-Level Product Approach
   - How will this feature work from a user's perspective?
   - What is the recommended product strategy?

6. Implementation Strategy
   - High-level approach to building this (in business terms, not technical details)
   - What phases or milestones make sense?

7. Estimation (MUST follow deterministic story point mapping):
   - Total Time (hours): [calculate first, assuming agentic tools are used]
   - Story Points: [MUST map deterministically using: 1=2-3h, 2=<1day, 3=2-3days, 5=<1week, 8=<1sprint, 13=danger zone - should be broken down]
   - Breakdown: Development (Xh), Testing (Xh), Documentation (Xh), Review (Xh), Deployment (Xh)
   - Complexity: [Low/Medium/High]
   - Business Risks: [list specific product/business risks]

8. Task Breakdown
   - High-level tasks (only include what's needed):
     * Design (if required)
     * Spike/Research (if required)
     * Proof of Concept (if required)
     * Implementation
     * Quality Assurance/Testing
   - Each task should be described in product/business terms

9. Dependencies
   - What other features, systems, or decisions are needed?
   - What external dependencies exist?

10. Acceptance Criteria
    - What defines success from a product perspective?
    - What user outcomes should be achieved?

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
