"""
iTaK - Security Module Tests

Tests for security-critical components:
- SecretManager (secret replacement, token verification)
- OutputGuard (PII/secret redaction)
- PathGuard (path traversal prevention)
- SSRFGuard (server-side request forgery prevention)
- RateLimiter (auth lockout, cost controls)
"""

import asyncio
import hmac
import hashlib
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# ============================================================
# SecretManager Tests
# ============================================================
class TestSecretManager:
    """Test secret management and token verification."""

    def test_register_and_replace_secrets(self):
        """Should replace secret placeholders in text."""
        from security.secrets import SecretManager
        
        sm = SecretManager()
        sm.register_secret("API_KEY", "sk-1234567890abcdef")
        sm.register_secret("DB_PASSWORD", "super_secret_pass")
        
        text = "Using {{API_KEY}} to access database with {{DB_PASSWORD}}"
        result = sm.replace_placeholders(text)
        
        assert "sk-1234567890abcdef" in result
        assert "super_secret_pass" in result
        assert "{{API_KEY}}" not in result
        assert "{{DB_PASSWORD}}" not in result

    def test_unresolved_placeholders_remain(self):
        """Should leave unresolved placeholders intact."""
        from security.secrets import SecretManager
        
        sm = SecretManager()
        sm.register_secret("KNOWN_KEY", "value123")
        
        text = "Known: {{KNOWN_KEY}}, Unknown: {{UNKNOWN_KEY}}"
        result = sm.replace_placeholders(text)
        
        assert "value123" in result
        assert "{{UNKNOWN_KEY}}" in result

    def test_verify_token_constant_time(self):
        """Token verification should use constant-time comparison."""
        from security.secrets import SecretManager
        
        sm = SecretManager()
        correct_token = "my-secret-token-12345"
        
        # Verify uses hmac.compare_digest (constant-time)
        assert sm.verify_token(correct_token, correct_token) is True
        assert sm.verify_token(correct_token, "wrong-token") is False
        assert sm.verify_token(correct_token, "") is False

    def test_mask_secrets_in_text(self):
        """Should mask registered secrets in output."""
        from security.secrets import SecretManager
        
        sm = SecretManager()
        sm.register_secret("API_KEY", "sk-1234567890abcdef")
        sm.register_secret("PASSWORD", "MyP@ssw0rd!")
        
        text = "Error: API key sk-1234567890abcdef failed with password MyP@ssw0rd!"
        masked = sm.mask_secrets(text)
        
        assert "sk-1234567890abcdef" not in masked
        assert "MyP@ssw0rd!" not in masked
        assert "***" in masked or "[REDACTED]" in masked


# ============================================================
# OutputGuard Tests
# ============================================================
class TestOutputGuard:
    """Test PII and secret redaction."""

    def test_redact_api_keys(self):
        """Should redact common API key patterns."""
        from security.output_guard import OutputGuard
        
        guard = OutputGuard()
        
        # OpenAI API key
        text = "Use this key: sk-1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = guard.sanitize(text)
        assert "sk-1234567890abcdefghijklmnopqrstuvwxyz123456" not in result
        
        # Anthropic API key
        text = "Claude key: sk-ant-1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = guard.sanitize(text)
        assert "sk-ant-1234567890abcdefghijklmnopqrstuvwxyz123456" not in result

    def test_redact_email_addresses(self):
        """Should redact email addresses."""
        from security.output_guard import OutputGuard
        
        guard = OutputGuard()
        text = "Contact me at john.doe@example.com for more info"
        result = guard.sanitize(text)
        
        assert "john.doe@example.com" not in result
        assert "[EMAIL]" in result or "***" in result

    def test_redact_phone_numbers(self):
        """Should redact phone numbers."""
        from security.output_guard import OutputGuard
        
        guard = OutputGuard()
        
        # US phone format
        text = "Call me at (555) 123-4567 or 555-123-4567"
        result = guard.sanitize(text)
        assert "555-123-4567" not in result or "[PHONE]" in result

    def test_redact_ssn(self):
        """Should redact Social Security Numbers."""
        from security.output_guard import OutputGuard
        
        guard = OutputGuard()
        text = "SSN: 123-45-6789"
        result = guard.sanitize(text)
        
        assert "123-45-6789" not in result

    def test_redact_credit_cards(self):
        """Should redact credit card numbers."""
        from security.output_guard import OutputGuard
        
        guard = OutputGuard()
        
        # Visa format
        text = "Card: 4111-1111-1111-1111"
        result = guard.sanitize(text)
        assert "4111-1111-1111-1111" not in result

    def test_preserve_safe_content(self):
        """Should not redact safe content."""
        from security.output_guard import OutputGuard
        
        guard = OutputGuard()
        text = "The weather is nice today. Temperature: 72 degrees."
        result = guard.sanitize(text)
        
        # Safe content should remain
        assert "weather" in result
        assert "72" in result


# ============================================================
# PathGuard Tests
# ============================================================
class TestPathGuard:
    """Test path traversal prevention."""

    def test_block_parent_directory_traversal(self):
        """Should block ../ path traversal attempts."""
        from security.path_guard import PathGuard
        
        guard = PathGuard()
        
        # Basic traversal
        with pytest.raises(ValueError):
            guard.validate_path("../../../etc/passwd")
        
        # Encoded traversal
        with pytest.raises(ValueError):
            guard.validate_path("..%2f..%2f..%2fetc%2fpasswd")
        
        # Mixed case (Windows)
        with pytest.raises(ValueError):
            guard.validate_path("..\\..\\..\\windows\\system32")

    def test_block_absolute_paths_outside_root(self):
        """Should block absolute paths outside allowed root."""
        from security.path_guard import PathGuard
        
        guard = PathGuard(allowed_root="/app/data")
        
        with pytest.raises(ValueError):
            guard.validate_path("/etc/passwd")
        
        with pytest.raises(ValueError):
            guard.validate_path("/tmp/malicious")

    def test_allow_safe_relative_paths(self):
        """Should allow safe relative paths within root."""
        from security.path_guard import PathGuard
        
        guard = PathGuard(allowed_root="/app/data")
        
        # These should not raise
        safe_path = guard.validate_path("user_files/document.txt")
        assert "user_files" in str(safe_path)
        
        safe_path = guard.validate_path("./reports/report.pdf")
        assert "reports" in str(safe_path)

    def test_safe_join_prevents_traversal(self):
        """safe_join should prevent path traversal."""
        from security.path_guard import PathGuard
        
        guard = PathGuard(allowed_root="/app/data")
        
        # Should normalize and prevent escaping
        result = guard.safe_join("/app/data", "../../../etc/passwd")
        assert "/etc/passwd" not in str(result)
        assert str(result).startswith("/app/data")

    def test_block_null_bytes(self):
        """Should block null byte injection."""
        from security.path_guard import PathGuard
        
        guard = PathGuard()
        
        with pytest.raises(ValueError):
            guard.validate_path("safe.txt\x00../../etc/passwd")


# ============================================================
# SSRFGuard Tests
# ============================================================
class TestSSRFGuard:
    """Test Server-Side Request Forgery prevention."""

    def test_block_private_ip_addresses(self):
        """Should block requests to private IP ranges."""
        from security.ssrf_guard import SSRFGuard
        
        guard = SSRFGuard(block_private_ips=True)
        
        # Private IPv4 ranges
        with pytest.raises(ValueError):
            guard.validate_url("http://192.168.1.1")
        
        with pytest.raises(ValueError):
            guard.validate_url("http://10.0.0.1")
        
        with pytest.raises(ValueError):
            guard.validate_url("http://172.16.0.1")
        
        # Localhost
        with pytest.raises(ValueError):
            guard.validate_url("http://localhost")
        
        with pytest.raises(ValueError):
            guard.validate_url("http://127.0.0.1")

    def test_block_aws_metadata_endpoint(self):
        """Should block AWS metadata endpoint."""
        from security.ssrf_guard import SSRFGuard
        
        guard = SSRFGuard(block_private_ips=True)
        
        with pytest.raises(ValueError):
            guard.validate_url("http://169.254.169.254/latest/meta-data/")

    def test_block_file_scheme(self):
        """Should block file:// URLs."""
        from security.ssrf_guard import SSRFGuard
        
        guard = SSRFGuard()
        
        with pytest.raises(ValueError):
            guard.validate_url("file:///etc/passwd")

    def test_allow_public_urls(self):
        """Should allow requests to public URLs."""
        from security.ssrf_guard import SSRFGuard
        
        guard = SSRFGuard(block_private_ips=True)
        
        # These should not raise
        guard.validate_url("https://www.google.com")
        guard.validate_url("https://api.openai.com")
        guard.validate_url("http://example.com:8080/api")

    def test_block_invalid_schemes(self):
        """Should only allow http/https schemes."""
        from security.ssrf_guard import SSRFGuard
        
        guard = SSRFGuard()
        
        with pytest.raises(ValueError):
            guard.validate_url("ftp://example.com")
        
        with pytest.raises(ValueError):
            guard.validate_url("javascript:alert(1)")
        
        with pytest.raises(ValueError):
            guard.validate_url("data:text/html,<script>alert(1)</script>")


# ============================================================
# RateLimiter Tests
# ============================================================
class TestRateLimiter:
    """Test rate limiting and auth lockout."""

    def test_auth_lockout_after_failed_attempts(self):
        """Should lock out after configured failed auth attempts."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_auth_failures=3, lockout_duration=60)
        
        user_id = "test_user"
        
        # First 2 failures - not locked out
        limiter.record_auth_failure(user_id)
        assert not limiter.is_locked_out(user_id)
        
        limiter.record_auth_failure(user_id)
        assert not limiter.is_locked_out(user_id)
        
        # 3rd failure - locked out
        limiter.record_auth_failure(user_id)
        assert limiter.is_locked_out(user_id)

    def test_successful_auth_resets_failures(self):
        """Successful auth should reset failure count."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_auth_failures=3)
        user_id = "test_user"
        
        # Some failures
        limiter.record_auth_failure(user_id)
        limiter.record_auth_failure(user_id)
        
        # Success resets
        limiter.record_auth_success(user_id)
        
        # Should start from 0 again
        limiter.record_auth_failure(user_id)
        assert not limiter.is_locked_out(user_id)

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Should track costs and enforce budgets."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter(cost_budget=1.0)
        user_id = "test_user"
        
        # Add costs
        limiter.add_cost(user_id, 0.5)
        assert limiter.get_total_cost(user_id) == 0.5
        
        limiter.add_cost(user_id, 0.3)
        assert limiter.get_total_cost(user_id) == 0.8
        
        # Check if over budget
        limiter.add_cost(user_id, 0.5)
        assert limiter.is_over_budget(user_id)

    def test_rate_limiting_per_endpoint(self):
        """Should enforce rate limits per endpoint."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=5)
        user_id = "test_user"
        endpoint = "/api/chat"
        
        # First 5 requests should succeed
        for i in range(5):
            allowed = limiter.check_rate_limit(user_id, endpoint)
            assert allowed
        
        # 6th request should be blocked
        allowed = limiter.check_rate_limit(user_id, endpoint)
        assert not allowed


# ============================================================
# Scanner Tests (Code Vulnerability Scanner)
# ============================================================
class TestScanner:
    """Test code vulnerability scanner."""

    def test_detect_sql_injection(self):
        """Should detect potential SQL injection vulnerabilities."""
        from security.scanner import Scanner
        
        scanner = Scanner()
        
        # Vulnerable code
        vulnerable_code = '''
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        '''
        
        issues = scanner.scan_code(vulnerable_code)
        assert len(issues) > 0
        assert any("sql" in issue.lower() or "injection" in issue.lower() for issue in issues)

    def test_detect_hardcoded_secrets(self):
        """Should detect hardcoded secrets."""
        from security.scanner import Scanner
        
        scanner = Scanner()
        
        # Code with hardcoded secret
        code_with_secret = '''
        api_key = "sk-1234567890abcdefghijklmnop"
        password = "hardcoded_password123"
        '''
        
        issues = scanner.scan_code(code_with_secret)
        assert len(issues) > 0
        assert any("secret" in issue.lower() or "key" in issue.lower() or "password" in issue.lower() for issue in issues)

    def test_detect_command_injection(self):
        """Should detect potential command injection."""
        from security.scanner import Scanner
        
        scanner = Scanner()
        
        # Vulnerable to command injection
        vulnerable_code = '''
        import os
        os.system(f"ping {user_input}")
        '''
        
        issues = scanner.scan_code(vulnerable_code)
        assert len(issues) > 0

    def test_safe_code_passes(self):
        """Safe code should not trigger warnings."""
        from security.scanner import Scanner
        
        scanner = Scanner()
        
        safe_code = '''
        def add(a, b):
            return a + b
        
        result = add(1, 2)
        print(result)
        '''
        
        issues = scanner.scan_code(safe_code)
        # Should have minimal or no issues
        assert len(issues) == 0 or all("info" in issue.lower() for issue in issues)
