# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email us at: laakhay.corp@gmail.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- We will acknowledge receipt within 48 hours
- We will provide a detailed response within 7 days
- We will keep you informed of our progress
- We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Best Practices

When using Laakhay-TA:

- Always validate input data before processing
- Use appropriate data types (Price, Qty, etc.) for financial calculations
- Be cautious with user-defined indicators in shared environments
- Keep the library updated to the latest version

## Security Considerations

- The library uses immutable data structures to prevent accidental data modification
- All financial calculations use Decimal precision to avoid floating-point errors
- Custom indicators run as regular Python functions - ensure they're from trusted sources
- CSV loading functions validate data types and handle malformed input gracefully
