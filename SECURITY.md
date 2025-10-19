# Security Policy

## 🔒 Security Overview

The Minecraft AI Chatbot takes security seriously. As an open source project that integrates with external AI services and handles user data, we are committed to ensuring the security and privacy of our users and contributors.

## 🚨 Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it responsibly. **Do not** report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 📧 How to Report

Please send security reports to: **security@wicz.cloud**

You can also create a private security advisory on GitHub:
1. Go to the [Security tab](https://github.com/webwicz/mc_ai/security) in this repository
2. Click "Report a vulnerability"
3. Provide detailed information about the issue

### 📋 What to Include

Please include as much of the following information as possible to help us understand and resolve the issue quickly:

- **Issue Type**: e.g., buffer overflow, SQL injection, cross-site scripting, authentication bypass
- **Severity**: Critical, High, Medium, Low
- **Affected Components**: Which parts of the codebase are impacted
- **Affected Versions**: Which versions of the software are vulnerable
- **Prerequisites**: Any special configuration or setup required
- **Steps to Reproduce**: Detailed reproduction steps
- **Proof of Concept**: Code, screenshots, or other evidence
- **Impact Assessment**: How an attacker could exploit this vulnerability
- **Potential Fixes**: Any suggested remediation approaches

### 🕐 Response Timeline

We will acknowledge receipt of your report within **48 hours** and provide a more detailed response within **7 days** indicating our next steps.

We will keep you informed about our progress throughout the process of fixing the vulnerability.

## 🛡️ Supported Versions

We actively maintain security updates for the following versions:

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.x.x   | :white_check_mark: | :white_check_mark: |
| < 1.0   | :x:                | :x:               |

## 🔐 Security Considerations

### External Dependencies
This project integrates with:
- **x.ai API**: For AI model access
- **Nextcloud Talk API**: For chat functionality
- **Docker**: For containerization

### Data Handling
- User messages are processed by external AI services
- No persistent storage of sensitive user data
- API keys should be properly secured in environment variables

### Best Practices for Users
- Use strong, unique API keys
- Keep dependencies updated
- Run in isolated environments when possible
- Monitor for unusual activity

## 📜 Disclosure Policy

We follow a coordinated disclosure process:

1. **Report Received**: Initial acknowledgment within 48 hours
2. **Investigation**: Security assessment and impact analysis
3. **Fix Development**: Create and test security patches
4. **Public Disclosure**: Release fixes and security advisories
5. **Credit**: Acknowledge reporters (with permission)

## 🏷️ Security Updates

Security updates will be:
- Released as patch versions (e.g., 1.2.3 → 1.2.4)
- Documented in release notes
- Tagged with appropriate severity labels
- Communicated through GitHub Security Advisories

## 🙏 Recognition

We appreciate security researchers who help keep our project safe. With your permission, we will acknowledge your contribution in our security advisories and release notes.

## 📞 Contact

For security-related questions or concerns:
- **Email**: security@wicz.cloud
- **GitHub Security Tab**: [Repository Security](https://github.com/webwicz/mc_ai/security)

Thank you for helping keep the Minecraft AI Chatbot community safe! 🛡️</content>
<parameter name="filePath">/home/bill/mc_ai/SECURITY.md
