# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in Kanso, please report it privately to help us address it responsibly:

### How to Report

**GitHub Security Advisory**: Use [GitHub's private vulnerability reporting](https://github.com/dstmrk/kanso/security/advisories/new)

### What to Include

Please include as much information as possible:
- Type of vulnerability (e.g., SQL injection, XSS, credential exposure)
- Step-by-step instructions to reproduce
- Potential impact
- Suggested fix (if you have one)

## Security Best Practices for Self-Hosting

Since Kanso is self-hosted and handles sensitive financial data, please follow these guidelines:

### Credentials Management
- ✅ **Never commit** Google Sheets credentials to version control
- ✅ Use `.env.*.local` files (gitignored) for secrets
- ✅ Set proper file permissions on `config/credentials/` (read-only for app user)
- ✅ Rotate credentials periodically

### Network Security
- ✅ Use **HTTPS** if exposing Kanso to the internet (reverse proxy with SSL/TLS)
- ✅ Restrict access via **firewall rules** or **VPN**
- ✅ Consider using **authentication layer** (e.g., authelia, basic auth via reverse proxy)
- ✅ Don't expose port 6789 directly to the internet

### Docker Security
- ✅ Kanso runs as **non-root user** in Docker (user `kanso`, UID 1000)
- ✅ Credentials mounted as **read-only** volumes
- ✅ Keep Docker images updated: `docker compose pull && docker compose up -d`
- ✅ Use Docker **secrets** for production deployments if needed

### Updates
- ✅ Watch GitHub releases for security updates
- ✅ Subscribe to **Dependabot alerts** (enable in repo settings)
- ✅ Review changelog before updating

## Known Limitations

### Current Security Model (v0.1.x)

- **Data storage**: Currently relies on Google Sheets API (data at rest security managed by Google)
- **Session management**: Uses NiceGUI's built-in session handling
- **Authentication**: Not implemented (assumes trusted network/VPN access)
- **Audit logging**: Basic application logs only

Thank you for helping keep Kanso and its users secure! 🙏
