# Security Policy

## Supported versions

The `main` branch and the latest tagged release (`v0.1.1`) are the actively supported versions. Older tagged versions do not receive security fixes.

## Reporting a vulnerability

If you discover a security issue in `google-hotels-mcp`, please **do not open a public GitHub issue**. Instead:

1. Open a [private security advisory](https://github.com/huynhtanan/google-hotels-mcp/security/advisories/new) on this repository, **or**
2. Email the maintainer at `huynhtanan90@gmail.com` with the subject `[security] google-hotels-mcp`.

Please include:

- A description of the issue and the impact (what an attacker could do).
- A reproduction: input, expected behavior, actual behavior, and the version/commit SHA.
- Any suggested fix or mitigation if you have one.

We will acknowledge the report within **72 hours** and aim to publish a patch release within **7 days** for high-severity issues (anything that can lead to remote code execution, credential leakage, or SSRF against a user's Apify token).

## Scope

In scope:

- The Python code under `src/google_hotels_mcp/`.
- The MCP tool handlers and the way the server validates arguments before forwarding them to the Apify REST API.
- The handling of the user's `APIFY_TOKEN` environment variable (it must never be logged, echoed back in tool output, or sent to any host other than `api.apify.com`).

Out of scope:

- Vulnerabilities in the upstream Apify actors themselves (report them on the actor's issue page under <https://apify.com/zet46>).
- Vulnerabilities in the `mcp` SDK, `httpx`, Claude Desktop, Cursor, or Windsurf — report those to their respective projects.

## Dependencies

Dependencies are pinned to minor-version ranges in `pyproject.toml` and the exact resolved set is tracked in `requirements.txt`. GitHub Dependabot runs weekly against `pip` and `github-actions` and opens PRs for upstream security advisories.
