# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Neighborhood BBS, please **do not** open a public GitHub issue. Instead, please report it responsibly by emailing:

**Email:** security@neighborhood-bbs.local

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

We will acknowledge receipt within 48 hours and provide an estimated timeline for a fix.

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| 1.x     | ✅ Yes    | Current release, receives security updates |
| < 1.0   | ❌ No     | Pre-release, no longer supported |

## Security Updates

We release security patches as soon as possible after discovery and verification. Critical vulnerabilities are released as soon as a fix is available.

## Security Features

Neighborhood BBS includes:
- ✅ **Input Sanitization** - All user inputs sanitized with bleach library
- ✅ **Rate Limiting** - Flask-Limiter prevents brute force and DoS attacks
- ✅ **CORS Protection** - Configurable CORS origins, prevents unauthorized domain access
- ✅ **Security Headers** - X-Frame-Options, CSP, HSTS, X-Content-Type-Options
- ✅ **SQL Injection Prevention** - Parameterized queries throughout
- ✅ **XSS Prevention** - Frontend and backend HTML escaping
- ✅ **HTTPS Ready** - Supports SSL/TLS configuration
- ✅ **Session Security** - Secure cookie settings (HttpOnly, SameSite)

## Best Practices for Deployment

When deploying Neighborhood BBS to production:

1. **Use HTTPS/TLS**
   ```bash
   # Set SESSION_COOKIE_SECURE=true
   export SESSION_COOKIE_SECURE=true
   ```

2. **Set a Strong SECRET_KEY**
   ```bash
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **Restrict CORS Origins**
   ```bash
   export CORS_ORIGINS="https://yourdomain.com"
   ```

4. **Enable Rate Limiting**
   - Already enabled by default
   - Adjust limits in src/chat/routes.py and src/board/routes.py

5. **Use Environment Variables**
   - Never commit secrets to git
   - Use .env file locally (add to .gitignore)
   - Use GitHub Secrets for CI/CD

6. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

7. **Run Behind a Reverse Proxy**
   - Use Nginx or Apache
   - Enable rate limiting at reverse proxy level
   - Handle TLS termination

## Known Vulnerabilities

None currently known. If you discover one, please report it using the process above.

## Security Testing

The project includes:
- ✅ Unit tests for security features
- ✅ Input validation testing
- ✅ XSS prevention verification
- ✅ SQL injection prevention verification
- ✅ CORS testing

## Security Disclosure Timeline

We follow responsible disclosure practices:
- **Day 0:** Vulnerability reported
- **Day 1:** Acknowledgment and assessment
- **Day 7:** Initial fix prepared (or timeline communicated)
- **Day 30:** Public disclosure (if no fix available earlier)

## Third-Party Dependencies

All dependencies are monitored for vulnerabilities. Run:
```bash
safety check
```

## Compliance

Neighborhood BBS is designed with privacy and security in mind:
- All data stays local (no cloud sync)
- No telemetry or tracking
- Open source for auditability
- MIT License for transparency

## Questions?

For security questions (non-vulnerability related), please use:
- **GitHub Discussions:** Ask in the Security category
- **Issues:** Tag with `security` label
- **Email:** security@neighborhood-bbs.local

---

**Last Updated:** March 15, 2026
