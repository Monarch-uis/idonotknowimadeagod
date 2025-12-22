# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **DO NOT** open a public issue
2. Email the maintainers privately at [your-email@example.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and provide updates every 7 days until resolved.

## Security Best Practices

### For Users
- Always use the latest version
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Run security audits: `pip-audit` and `safety check`
- Use virtual environments
- Don't process untrusted EPUB files without sandboxing
- Review config.json for secure settings

### For Contributors
- Follow secure coding practices
- Validate all user inputs
- Use parameterized queries for any database operations
- Avoid shell injection vulnerabilities
- Keep dependencies minimal and audited
- Use secrets management for API keys

## Known Security Considerations

1. **EPUB Processing**: EPUBs are ZIP files that can contain arbitrary content. Always process from trusted sources.
2. **FFmpeg**: External dependency - keep updated to latest stable version
3. **TTS API Keys**: If using paid TTS services, secure API keys using environment variables
4. **File Paths**: Path traversal is mitigated by `core/path_utils.py` - do not bypass these utilities

## Dependency Security

We use:
- GitHub Dependabot for automated dependency updates
- `pip-audit` for CVE scanning
- `safety` for known vulnerability checks
- Regular manual security reviews

Last Security Audit: [Date]
