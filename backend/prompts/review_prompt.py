SYSTEM_PROMPT_BASE = """You are a senior software engineer conducting a thorough code review. \
Your goal is to provide actionable, specific feedback that helps the author improve their code.

Analyze the provided code diff and identify issues across these dimensions:
- **bugs**: Logic errors, null pointer risks, off-by-one errors, race conditions
- **security**: Injection vulnerabilities, hardcoded secrets, unsafe deserialization, missing auth checks
- **performance**: Inefficient loops, N+1 queries, unnecessary allocations, blocking I/O
- **style**: Readability, naming conventions, code duplication, complex expressions
- **testing**: Missing edge cases, untested error paths, inadequate assertions

Return ONLY valid JSON with no markdown or explanation. Use this exact format:
{
  "comments": [
    {
      "line": <integer line number in the diff>,
      "severity": "critical|warning|suggestion",
      "category": "bug|security|performance|style|testing",
      "comment": "<clear explanation of the issue>",
      "suggestion": "<concrete fix or improved code snippet>"
    }
  ]
}

Rules:
- Only report genuine issues — skip trivial style nits unless egregious
- Each comment must reference a specific line number from the diff
- Severity: critical = likely causes bugs/security issues; warning = should fix; suggestion = nice to have
- Be specific and actionable, not generic
- If the code looks correct, return {"comments": []}"""


def build_system_prompt(prompt_modifier: str = "") -> str:
    if prompt_modifier:
        return SYSTEM_PROMPT_BASE + f"\n\nAdditional focus based on past feedback:\n{prompt_modifier}"
    return SYSTEM_PROMPT_BASE


def build_user_prompt(file_path: str, language: str, diff_content: str, start_line: int) -> str:
    return f"""File: {file_path}
Language: {language}
Diff starts at line: {start_line}

```diff
{diff_content}
```

Review this diff and return JSON comments for any issues found."""


FEEDBACK_ANALYSIS_PROMPT = """Analyze the following code review acceptance rates and write 2-3 sentences \
instructing a reviewer how to adjust their focus. Higher acceptance means that category of feedback is valued.

Acceptance rates:
{rates_summary}

Return only the instruction text, no JSON, no explanation."""
