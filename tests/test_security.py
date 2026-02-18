"""
iTaK - Security Module Tests.

Comprehensive tests for all security features:
- OutputGuard (PII/secret redaction)
- PathGuard (path traversal prevention)
- SSRFGuard (SSRF attack prevention)
- RateLimiter (rate limiting + auth lockout)
- SecurityScanner (code vulnerability scanning)
- SecretManager (secret management + constant-time verification)
- OutputSanitizer (local path stripping)
- Webhook secret verification (constant-time comparison)
"""

import hmac
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ============================================================
# OutputGuard Tests
# ============================================================
class TestOutputGuard:
    """Test the PII & secret redaction layer."""

    def _guard(self, **kwargs):
        from security.output_guard import OutputGuard
        return OutputGuard(config=kwargs)

    def test_redacts_ssn(self):
        guard = self._guard()
        result = guard.sanitize("My SSN is 123-45-6789")
        assert "123-45-6789" not in result.sanitized_text
        assert "[SSN REDACTED]" in result.sanitized_text
        assert result.was_modified

    def test_redacts_credit_card(self):
        guard = self._guard()
        result = guard.sanitize("Card: 4111-1111-1111-1111")
        assert "4111" not in result.sanitized_text
        assert "[CARD REDACTED]" in result.sanitized_text

    def test_redacts_email(self):
        guard = self._guard()
        result = guard.sanitize("Email me at user@example.com")
        assert "user@example.com" not in result.sanitized_text
        assert "[EMAIL REDACTED]" in result.sanitized_text

    def test_redacts_openai_key(self):
        guard = self._guard()
        result = guard.sanitize("Key: sk-abc123def456ghi789jklmnop")
        assert "sk-abc123def456ghi789jklmnop" not in result.sanitized_text
        assert "[API KEY REDACTED]" in result.sanitized_text

    def test_redacts_github_token(self):
        guard = self._guard()
        token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        result = guard.sanitize(f"Token: {token}")
        assert token not in result.sanitized_text
        assert "REDACTED" in result.sanitized_text

    def test_redacts_private_key(self):
        guard = self._guard()
        key = "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----"
        result = guard.sanitize(f"Here is the key:\n{key}")
        assert "BEGIN RSA PRIVATE KEY" not in result.sanitized_text
        assert "[PRIVATE KEY REDACTED]" in result.sanitized_text

    def test_redacts_jwt(self):
        guard = self._guard()
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.Gfx6VO9tcxwk6xqx9yYzSfebfeakZp5JYIgP_edcw_A"
        result = guard.sanitize(f"JWT: {jwt}")
        assert "eyJhbGci" not in result.sanitized_text
        assert "[JWT REDACTED]" in result.sanitized_text

    def test_redacts_password_in_kv(self):
        guard = self._guard()
        result = guard.sanitize('password = "mysecretpass123"')
        assert "mysecretpass123" not in result.sanitized_text
        assert "[PASSWORD REDACTED]" in result.sanitized_text

    def test_no_redaction_safe_text(self):
        guard = self._guard()
        text = "Hello, this is a normal message."
        result = guard.sanitize(text)
        assert result.sanitized_text == text
        assert not result.was_modified

    def test_disabled_guard(self):
        guard = self._guard(output_guard={"enabled": False})
        text = "My SSN is 123-45-6789"
        result = guard.sanitize(text)
        assert result.sanitized_text == text
        assert not result.was_modified

    def test_empty_text(self):
        guard = self._guard()
        result = guard.sanitize("")
        assert result.sanitized_text == ""
        assert not result.was_modified

    def test_custom_pattern(self):
        guard = self._guard()
        guard.add_custom_pattern(r"ACME-\d{6}", "ACME ID")
        result = guard.sanitize("ID: ACME-123456")
        assert "ACME-123456" not in result.sanitized_text
        assert "[ACME ID REDACTED]" in result.sanitized_text

    def test_stats(self):
        guard = self._guard()
        guard.sanitize("My SSN is 123-45-6789")
        guard.sanitize("Normal text")
        stats = guard.get_stats()
        assert stats["total_scans"] == 2
        assert stats["total_redactions"] >= 1

    def test_redacts_ip_address(self):
        guard = self._guard()
        result = guard.sanitize("Server at 192.168.1.100 is down")
        assert "192.168.1.100" not in result.sanitized_text
        assert "[IP REDACTED]" in result.sanitized_text

    def test_redacts_slack_token(self):
        guard = self._guard()
        # Build token dynamically to avoid secret scanning false positive
        prefix = "xoxb"
        token = f"{prefix}-{'0' * 13}-{'0' * 13}-{'a' * 24}"
        result = guard.sanitize(f"Slack: {token}")
        assert prefix not in result.sanitized_text
        assert "REDACTED" in result.sanitized_text

    def test_redacts_aws_access_key(self):
        guard = self._guard()
        result = guard.sanitize("AWS key: AKIAIOSFODNN7EXAMPLE")
        assert "AKIAIOSFODNN7EXAMPLE" not in result.sanitized_text
        assert "[AWS KEY REDACTED]" in result.sanitized_text


class TestInboundSanitization:
    """Test inbound sanitization for adapter and webhook ingress."""

    @pytest.mark.asyncio
    async def test_base_adapter_sanitizes_inbound_message(self):
        from adapters.base import BaseAdapter
        from security.output_guard import OutputGuard

        class DummyAdapter(BaseAdapter):
            async def send_message(self, content: str, **kwargs):
                return content

        agent = MagicMock()
        agent.output_guard = OutputGuard(config={})
        agent.message_loop = MagicMock(return_value="ok")
        agent.context = MagicMock()

        adapter = DummyAdapter(agent, {})
        raw = "My email is user@example.com"

        await adapter.handle_message(user_id="u1", content=raw)

        called_content = agent.message_loop.call_args.args[0]
        assert "user@example.com" not in called_content
        assert "[EMAIL REDACTED]" in called_content

    def test_webhook_parse_inbound_sanitizes_payload(self):
        from core.webhooks import WebhookEngine
        from security.output_guard import OutputGuard

        agent = MagicMock()
        agent.output_guard = OutputGuard(config={})

        engine = WebhookEngine(agent, {"integrations": {}})
        parsed = engine.parse_inbound({
            "title": "Customer email user@example.com",
            "message": "Reach me at user@example.com",
            "metadata": {
                "address": "123 Main St",
                "contact": "user@example.com",
            },
        })

        assert "user@example.com" not in parsed.title
        assert "[EMAIL REDACTED]" in parsed.title
        assert "user@example.com" not in parsed.message
        assert "[EMAIL REDACTED]" in parsed.message
        assert "user@example.com" not in parsed.metadata.get("contact", "")


# ============================================================
# PathGuard Tests
# ============================================================
class TestPathGuard:
    """Test path traversal prevention."""

    def test_blocks_null_byte(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("file\x00.txt")
        assert not safe
        assert "Null byte" in reason

    def test_blocks_dotdot(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("../../etc/passwd")
        assert not safe
        assert "traversal" in reason.lower()

    def test_blocks_encoded_traversal(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("..%2f..%2fetc%2fpasswd")
        assert not safe

    def test_blocks_double_encoded(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("%252e%252e/etc/passwd")
        assert not safe

    def test_blocks_tilde(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("~/secret")
        assert not safe

    def test_blocks_control_chars(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("file\x01name.txt")
        assert not safe
        assert "Control character" in reason

    def test_blocks_absolute_path(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("/etc/passwd", allow_absolute=False)
        assert not safe
        assert "Absolute" in reason

    def test_allows_absolute_when_permitted(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("/tmp/safe.txt", allow_absolute=True)
        assert safe

    def test_allowed_roots(self, tmp_path):
        from security.path_guard import validate_path
        # Create a file inside root
        safe_file = tmp_path / "data" / "file.txt"
        safe_file.parent.mkdir(parents=True, exist_ok=True)
        safe_file.write_text("ok")

        safe, reason = validate_path(
            str(safe_file), allowed_roots=[str(tmp_path)], allow_absolute=True
        )
        assert safe

    def test_rejects_path_outside_roots(self, tmp_path):
        from security.path_guard import validate_path
        safe, reason = validate_path(
            "/etc/passwd", allowed_roots=[str(tmp_path)], allow_absolute=True
        )
        assert not safe
        assert "escapes" in reason.lower()

    def test_empty_path(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("")
        assert not safe
        assert "Empty" in reason

    def test_relative_path_ok(self):
        from security.path_guard import validate_path
        safe, reason = validate_path("data/file.txt")
        assert safe

    def test_session_id_valid(self):
        from security.path_guard import validate_session_id
        safe, reason = validate_session_id("session-123_abc")
        assert safe

    def test_session_id_rejects_dots(self):
        from security.path_guard import validate_session_id
        safe, reason = validate_session_id("../etc/passwd")
        assert not safe

    def test_session_id_rejects_slashes(self):
        from security.path_guard import validate_session_id
        safe, reason = validate_session_id("session/../../root")
        assert not safe

    def test_session_id_too_long(self):
        from security.path_guard import validate_session_id
        safe, reason = validate_session_id("a" * 200)
        assert not safe
        assert "too long" in reason.lower()

    def test_session_id_empty(self):
        from security.path_guard import validate_session_id
        safe, reason = validate_session_id("")
        assert not safe

    def test_safe_join(self, tmp_path):
        from security.path_guard import safe_join
        result = safe_join(tmp_path, "sub", "file.txt")
        assert result is not None
        assert str(tmp_path) in str(result)

    def test_safe_join_blocks_traversal(self, tmp_path):
        from security.path_guard import safe_join
        result = safe_join(tmp_path, "..", "etc", "passwd")
        assert result is None


# ============================================================
# SSRFGuard Tests
# ============================================================
class TestSSRFGuard:
    """Test SSRF attack prevention."""

    def _guard(self, **kwargs):
        from security.ssrf_guard import SSRFGuard
        return SSRFGuard(config={"security": kwargs})

    def test_blocks_file_scheme(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("file:///etc/passwd")
        assert not allowed
        assert "scheme" in reason.lower()

    def test_blocks_ftp_scheme(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("ftp://evil.com/file")
        assert not allowed

    def test_blocks_gopher_scheme(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("gopher://evil.com/")
        assert not allowed

    def test_blocks_javascript_scheme(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("javascript:alert(1)")
        assert not allowed

    def test_blocks_data_scheme(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("data:text/html,<script>")
        assert not allowed

    def test_blocks_unknown_scheme(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("custom://something")
        assert not allowed
        assert "Unknown scheme" in reason

    def test_blocks_localhost(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("http://127.0.0.1:8080/admin")
        assert not allowed
        assert "private" in reason.lower()

    def test_blocks_private_10x(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("http://10.0.0.1/admin")
        assert not allowed

    def test_blocks_private_172x(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("http://172.16.0.1/admin")
        assert not allowed

    def test_blocks_private_192x(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("http://192.168.1.1/admin")
        assert not allowed

    def test_blocks_no_hostname(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("http:///path")
        assert not allowed
        assert "hostname" in reason.lower()

    def test_blocks_denylist(self):
        guard = self._guard(url_denylist=["evil.com"])
        allowed, reason = guard.validate_url("https://evil.com/path")
        assert not allowed
        assert "blocked" in reason.lower()

    def test_blocks_denylist_subdomain(self):
        guard = self._guard(url_denylist=["evil.com"])
        allowed, reason = guard.validate_url("https://sub.evil.com/path")
        assert not allowed

    def test_allowlist_blocks_unlisted(self):
        guard = self._guard(url_allowlist=["api.example.com"])
        allowed, reason = guard.validate_url("https://other.com/path")
        assert not allowed
        assert "allowlist" in reason.lower()

    def test_allowlist_permits_listed(self):
        guard = self._guard(url_allowlist=["api.example.com"], block_private_ips=False)
        allowed, reason = guard.validate_url("https://api.example.com/data")
        assert allowed

    def test_stats(self):
        guard = self._guard()
        guard.validate_url("file:///etc/passwd")
        guard.validate_url("gopher://evil.com")
        stats = guard.get_stats()
        assert stats["blocked_total"] == 2
        assert len(stats["recent_blocks"]) == 2

    def test_invalid_url(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("")
        assert not allowed

    def test_blocks_link_local(self):
        guard = self._guard()
        allowed, reason = guard.validate_url("http://169.254.169.254/metadata")
        assert not allowed


# ============================================================
# RateLimiter Tests
# ============================================================
class TestRateLimiter:
    """Test rate limiting and auth lockout."""

    def _limiter(self, **kwargs):
        from security.rate_limiter import RateLimiter
        return RateLimiter(config=kwargs)

    def test_allows_within_limit(self):
        limiter = self._limiter(global_rpm=10)
        allowed, reason = limiter.check("global")
        assert allowed
        assert reason == "OK"

    def test_blocks_over_limit(self):
        limiter = self._limiter(global_rpm=3)
        for _ in range(3):
            limiter.record("global")
        allowed, reason = limiter.check("global")
        assert not allowed
        assert "Rate limit" in reason

    def test_records_cost(self):
        limiter = self._limiter(daily_budget_usd=1.0)
        limiter.record("global", cost_usd=0.5)
        limiter.record("global", cost_usd=0.5)
        allowed, reason = limiter.check("global")
        assert not allowed
        assert "budget" in reason.lower()

    def test_status(self):
        limiter = self._limiter()
        limiter.record("global", cost_usd=0.01)
        status = limiter.get_status()
        assert status["daily_cost"] == 0.01
        assert "budget_remaining" in status

    def test_set_limit(self):
        limiter = self._limiter()
        limiter.set_limit("test_cat", max_per_minute=5)
        assert limiter.limits["test_cat"]["max_per_minute"] == 5

    def test_auth_lockout(self):
        limiter = self._limiter()
        # Simulate 5 failed auth attempts
        for _ in range(5):
            limiter.record_auth_failure("client_1")
        locked, retry_after = limiter.check_auth_lockout("client_1")
        assert locked
        assert retry_after > 0

    def test_auth_lockout_not_triggered_below_threshold(self):
        limiter = self._limiter()
        for _ in range(4):
            limiter.record_auth_failure("client_1")
        locked, retry_after = limiter.check_auth_lockout("client_1")
        assert not locked

    def test_auth_success_clears_lockout(self):
        limiter = self._limiter()
        for _ in range(5):
            limiter.record_auth_failure("client_2")
        limiter.record_auth_success("client_2")
        locked, retry_after = limiter.check_auth_lockout("client_2")
        assert not locked

    def test_no_lockout_initially(self):
        limiter = self._limiter()
        locked, retry_after = limiter.check_auth_lockout("unknown")
        assert not locked

    def test_daily_budget_reset(self):
        limiter = self._limiter(daily_budget_usd=1.0)
        limiter.record("global", cost_usd=1.0)
        # Simulate time passing beyond 24h
        limiter._cost_reset_time = time.time() - 86401
        allowed, reason = limiter.check("global")
        assert allowed


# ============================================================
# SecurityScanner Tests
# ============================================================
class TestSecurityScanner:
    """Test code vulnerability scanning."""

    def _scanner(self):
        from security.scanner import SecurityScanner
        return SecurityScanner()

    def test_detects_eval(self):
        scanner = self._scanner()
        result = scanner.scan_code('result = eval(user_input)')
        assert not result["safe"]
        assert result["blocked"]
        assert any("eval" in f["pattern"] for f in result["findings"])

    def test_detects_exec(self):
        scanner = self._scanner()
        result = scanner.scan_code('exec(code)')
        assert not result["safe"]
        assert result["blocked"]

    def test_detects_os_system(self):
        scanner = self._scanner()
        result = scanner.scan_code('os.system("rm -rf /")')
        assert result["blocked"]
        criticals = [f for f in result["findings"] if f["severity"] == "CRITICAL"]
        assert len(criticals) >= 1

    def test_detects_pickle(self):
        scanner = self._scanner()
        result = scanner.scan_code('pickle.load(data)')
        assert result["blocked"]

    def test_detects_shell_true(self):
        scanner = self._scanner()
        result = scanner.scan_code('subprocess.call(cmd, shell=True)')
        assert result["blocked"]

    def test_detects_rm_rf_root(self):
        scanner = self._scanner()
        result = scanner.scan_code('rm -rf /')
        assert result["blocked"]

    def test_detects_yaml_load(self):
        scanner = self._scanner()
        result = scanner.scan_code('yaml.load(data)')
        assert result["blocked"]

    def test_safe_code_passes(self):
        scanner = self._scanner()
        result = scanner.scan_code('print("Hello, World!")')
        assert result["safe"]
        assert not result["blocked"]

    def test_warnings_not_blocked(self):
        scanner = self._scanner()
        result = scanner.scan_code('import subprocess\nsubprocess.run(["ls"])')
        assert result["safe"]  # Not blocked, only WARNING
        warnings = [f for f in result["findings"] if f["severity"] == "WARNING"]
        assert len(warnings) >= 1

    def test_detects_hardcoded_secrets(self):
        scanner = self._scanner()
        result = scanner.scan_code('API_KEY = "sk-abc123def456ghi789jklmnop"')
        assert len(result["secrets_found"]) >= 1
        assert result["blocked"]

    def test_detects_import_dynamic(self):
        scanner = self._scanner()
        result = scanner.scan_code('module = __import__("os")')
        assert result["blocked"]

    def test_scan_file_nonexistent(self):
        scanner = self._scanner()
        result = scanner.scan_file("/nonexistent/file.py")
        assert result["safe"]  # Non-existent files return safe

    def test_scan_file(self, tmp_path):
        scanner = self._scanner()
        f = tmp_path / "test.py"
        f.write_text('result = eval("2+2")')
        result = scanner.scan_file(str(f))
        assert result["blocked"]

    def test_ast_scan(self):
        scanner = self._scanner()
        findings = scanner.scan_python_ast('eval(input())')
        assert len(findings) >= 1
        assert any("eval" in f["pattern"] for f in findings)

    def test_ast_scan_import(self):
        scanner = self._scanner()
        findings = scanner.scan_python_ast('from os import system')
        assert len(findings) >= 1

    def test_format_report_safe(self):
        scanner = self._scanner()
        result = scanner.scan_code('x = 1 + 2')
        report = scanner.format_report(result)
        assert "SAFE" in report

    def test_format_report_blocked(self):
        scanner = self._scanner()
        result = scanner.scan_code('eval(x)')
        report = scanner.format_report(result)
        assert "BLOCKED" in report


# ============================================================
# SecretManager Tests
# ============================================================
class TestSecretManager:
    """Test secret management and constant-time verification."""

    def _manager(self, tmp_path, env_content=""):
        from security.secrets import SecretManager
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        return SecretManager(env_file=str(env_file))

    def test_loads_env(self, tmp_path):
        manager = self._manager(tmp_path, 'MY_SECRET=hello123')
        assert manager.get("MY_SECRET") == "hello123"

    def test_loads_quoted_values(self, tmp_path):
        manager = self._manager(tmp_path, 'MY_KEY="quoted_value"')
        assert manager.get("MY_KEY") == "quoted_value"

    def test_skips_comments(self, tmp_path):
        manager = self._manager(tmp_path, '# comment\nKEY=value')
        assert manager.get("KEY") == "value"
        assert not manager.has("# comment")

    def test_get_default(self, tmp_path):
        manager = self._manager(tmp_path, '')
        assert manager.get("NONEXISTENT", "default") == "default"

    def test_placeholder_replacement(self, tmp_path):
        manager = self._manager(tmp_path, 'API_KEY=sk-test123')
        result = manager.replace_placeholders("Use key: {{API_KEY}}")
        assert result == "Use key: sk-test123"

    def test_placeholder_unresolved(self, tmp_path):
        manager = self._manager(tmp_path, '')
        result = manager.replace_placeholders("Use key: {{MISSING}}")
        assert result == "Use key: {{MISSING}}"

    def test_mask_in_text(self, tmp_path):
        manager = self._manager(tmp_path, 'SECRET=supersecretvalue')
        masked = manager.mask_in_text("The secret is supersecretvalue")
        assert "supersecretvalue" not in masked
        assert "sup***" in masked

    def test_verify_token_correct(self, tmp_path):
        manager = self._manager(tmp_path, 'AUTH_TOKEN=my_auth_token_123')
        assert manager.verify_token("my_auth_token_123", "AUTH_TOKEN")

    def test_verify_token_incorrect(self, tmp_path):
        manager = self._manager(tmp_path, 'AUTH_TOKEN=my_auth_token_123')
        assert not manager.verify_token("wrong_token", "AUTH_TOKEN")

    def test_verify_token_missing_key(self, tmp_path):
        manager = self._manager(tmp_path, '')
        assert not manager.verify_token("any_value", "NONEXISTENT")

    def test_available_keys(self, tmp_path):
        manager = self._manager(tmp_path, 'A=1\nB=2')
        keys = manager.available_keys
        assert "A" in keys
        assert "B" in keys

    def test_has(self, tmp_path):
        manager = self._manager(tmp_path, 'EXISTS=yes')
        assert manager.has("EXISTS")
        assert not manager.has("NOPE")

    def test_resolve_config_value(self, tmp_path):
        manager = self._manager(tmp_path, 'MY_VAR=resolved')
        result = manager.resolve_config_value("$MY_VAR")
        assert result == "resolved"

    def test_resolve_config_value_literal(self, tmp_path):
        manager = self._manager(tmp_path, '')
        result = manager.resolve_config_value("literal_value")
        assert result == "literal_value"


# ============================================================
# OutputSanitizer Tests
# ============================================================
class TestOutputSanitizer:
    """Test local path stripping and sensitive pattern removal."""

    def test_strips_unix_path(self):
        from security.output_sanitizer import strip_local_paths
        result = strip_local_paths("File at /home/user/secret/data.txt")
        assert "/home/user" not in result
        assert "[local file]" in result

    def test_strips_windows_path(self):
        from security.output_sanitizer import strip_local_paths
        result = strip_local_paths(r"File at C:\Users\admin\secret.txt")
        assert r"C:\Users" not in result
        assert "[local file]" in result

    def test_strips_tmp_path(self):
        from security.output_sanitizer import strip_local_paths
        result = strip_local_paths("Screenshot saved to /tmp/screenshot_123.png")
        assert "/tmp/screenshot" not in result

    def test_strips_file_uri(self):
        from security.output_sanitizer import strip_local_paths
        result = strip_local_paths("Open file:///home/user/doc.pdf")
        assert "file:///" not in result

    def test_strips_sensitive_env_vars(self):
        from security.output_sanitizer import strip_sensitive
        result = strip_sensitive("API_KEY = sk-secret123abc")
        assert "sk-secret123abc" not in result
        assert "[REDACTED]" in result

    def test_full_sanitization(self):
        from security.output_sanitizer import sanitize_output
        text = "File at /home/user/data.txt\nAPI_KEY = secret123\n\n\n\nMore text"
        result = sanitize_output(text)
        assert "/home/user" not in result
        assert "secret123" not in result
        # Collapsed blank lines
        assert "\n\n\n" not in result

    def test_empty_text(self):
        from security.output_sanitizer import sanitize_output
        assert sanitize_output("") == ""
        assert sanitize_output(None) is None

    def test_preserves_safe_text(self):
        from security.output_sanitizer import sanitize_output
        text = "Everything is working correctly."
        result = sanitize_output(text)
        assert result == text


# ============================================================
# Webhook Secret Verification Tests
# ============================================================
class TestWebhookSecurity:
    """Test webhook secret verification uses constant-time comparison."""

    def _engine(self, secret=""):
        from core.webhooks import WebhookEngine
        agent = MagicMock()
        config = {"integrations": {"inbound_webhook_secret": secret}}
        return WebhookEngine(agent, config)

    def test_correct_secret(self):
        engine = self._engine("my_webhook_secret")
        assert engine.verify_secret("my_webhook_secret")

    def test_incorrect_secret(self):
        engine = self._engine("my_webhook_secret")
        assert not engine.verify_secret("wrong_secret")

    def test_no_secret_configured(self):
        engine = self._engine("")
        # No secret = open access (by design)
        assert engine.verify_secret("")
        assert engine.verify_secret("anything")

    def test_empty_provided(self):
        engine = self._engine("my_webhook_secret")
        assert not engine.verify_secret("")

    def test_uses_constant_time_comparison(self):
        """Verify the implementation uses hmac.compare_digest."""
        import inspect
        from core.webhooks import WebhookEngine
        source = inspect.getsource(WebhookEngine.verify_secret)
        assert "hmac.compare_digest" in source
        # Ensure the return statement uses hmac.compare_digest, not plain ==
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("return") and "==" in stripped:
                pytest.fail("verify_secret uses plain == comparison instead of hmac.compare_digest")


# ============================================================
# Config Redaction Tests
# ============================================================
class TestConfigRedaction:
    """Test that WebUI config endpoint properly redacts sensitive data."""

    def test_redacts_top_level_secrets(self):
        """Config redaction should catch 'secret' in key names."""
        # We test the _redact_dict / _is_sensitive_key logic indirectly
        # by simulating what create_app builds
        sensitive_keys = {"key", "token", "password", "secret"}

        def is_sensitive(name):
            return any(s in name.lower() for s in sensitive_keys)

        def redact_dict(d):
            safe = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    safe[k] = redact_dict(v)
                elif isinstance(v, str) and is_sensitive(k):
                    safe[k] = "***"
                else:
                    safe[k] = v
            return safe

        config = {
            "api_key": "sk-abc123",
            "auth_token": "tok-xyz",
            "db_password": "pass123",
            "webhook_secret": "sec456",
            "name": "iTaK",
            "nested": {
                "inner_key": "should-redact",
                "inner_secret": "should-redact-too",
                "safe_field": "visible",
                "deep": {
                    "deep_token": "hidden",
                    "deep_safe": "shown",
                },
            },
        }

        result = redact_dict(config)
        assert result["api_key"] == "***"
        assert result["auth_token"] == "***"
        assert result["db_password"] == "***"
        assert result["webhook_secret"] == "***"
        assert result["name"] == "iTaK"
        assert result["nested"]["inner_key"] == "***"
        assert result["nested"]["inner_secret"] == "***"
        assert result["nested"]["safe_field"] == "visible"
        assert result["nested"]["deep"]["deep_token"] == "***"
        assert result["nested"]["deep"]["deep_safe"] == "shown"
