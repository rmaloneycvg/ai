"""Unit tests for ticket system integration."""

import pytest

from src.lib.ticket import (
    get_ticket_url,
    detect_ticket_system,
    extract_ticket_from_branch,
    format_branch_name,
    format_pr_title,
    validate_branch_name,
)


@pytest.mark.unit
class TestGetTicketUrl:
    """Tests for get_ticket_url() function."""

    def test_returns_url_when_set(self, env_with_ticket_url):
        assert get_ticket_url() == "https://mycompany.atlassian.net"

    def test_returns_none_when_not_set(self, env_without_ticket_url):
        assert get_ticket_url() is None

    def test_returns_none_for_empty_string(self, monkeypatch):
        monkeypatch.setenv("TICKET_SYSTEM_URL", "")
        assert get_ticket_url() is None

    def test_returns_none_for_whitespace(self, monkeypatch):
        monkeypatch.setenv("TICKET_SYSTEM_URL", "   ")
        assert get_ticket_url() is None


@pytest.mark.unit
class TestDetectTicketSystem:
    """Tests for detect_ticket_system() function."""

    def test_jira(self):
        assert detect_ticket_system("https://mycompany.atlassian.net") == "jira"

    def test_linear(self):
        assert detect_ticket_system("https://linear.app") == "linear"

    def test_shortcut(self):
        assert detect_ticket_system("https://app.shortcut.com") == "shortcut"

    def test_youtrack(self):
        assert detect_ticket_system("https://myteam.youtrack.cloud") == "youtrack"

    def test_generic(self):
        assert detect_ticket_system("https://custom-tool.example.com") == "generic"


@pytest.mark.unit
class TestExtractTicketFromBranch:
    """Tests for extract_ticket_from_branch() function."""

    def test_extracts_jira_ticket(self):
        assert extract_ticket_from_branch("feat/PROJ-123-add-login") == "PROJ-123"

    def test_extracts_from_hotfix(self):
        assert extract_ticket_from_branch("hotfix/INC-456-fix-payment") == "INC-456"

    def test_no_ticket_returns_none(self):
        assert extract_ticket_from_branch("feat/add-login") is None

    def test_no_ticket_in_dev(self):
        assert extract_ticket_from_branch("dev") is None

    def test_extracts_first_match(self):
        assert extract_ticket_from_branch("feat/PROJ-123-BUG-456") == "PROJ-123"


@pytest.mark.unit
class TestFormatBranchName:
    """Tests for format_branch_name() function."""

    def test_with_ticket(self):
        result = format_branch_name("feat", "add user auth", "PROJ-123")
        assert result == "feat/PROJ-123-add-user-auth"

    def test_without_ticket(self):
        result = format_branch_name("fix", "null pointer")
        assert result == "fix/null-pointer"

    def test_kebab_cases_description(self):
        result = format_branch_name("feat", "Add User Authentication")
        assert result == "feat/add-user-authentication"

    def test_strips_special_chars(self):
        result = format_branch_name("fix", "bug: crashes on login!")
        assert result == "fix/bug-crashes-on-login"

    def test_uppercase_ticket(self):
        result = format_branch_name("feat", "auth", "proj-123")
        assert result == "feat/PROJ-123-auth"

    def test_hotfix_format(self):
        result = format_branch_name("hotfix", "payment timeout", "INC-789")
        assert result == "hotfix/INC-789-payment-timeout"


@pytest.mark.unit
class TestFormatPrTitle:
    """Tests for format_pr_title() function."""

    def test_with_scope_and_ticket(self):
        result = format_pr_title("feat", "add login page", scope="auth", ticket="PROJ-123")
        assert result == "feat(auth): PROJ-123 add login page"

    def test_without_ticket(self):
        result = format_pr_title("fix", "handle null response", scope="api")
        assert result == "fix(api): handle null response"

    def test_without_scope(self):
        result = format_pr_title("chore", "update gitignore")
        assert result == "chore: update gitignore"

    def test_without_scope_with_ticket(self):
        result = format_pr_title("feat", "add feature", ticket="PROJ-456")
        assert result == "feat: PROJ-456 add feature"


@pytest.mark.unit
class TestValidateBranchName:
    """Tests for validate_branch_name() function."""

    def test_valid_feat_branch(self):
        is_valid, error = validate_branch_name("feat/add-user-auth")
        assert is_valid is True
        assert error == ""

    def test_valid_with_ticket(self):
        is_valid, error = validate_branch_name("feat/PROJ-123-add-login")
        assert is_valid is True

    def test_protected_branches_always_valid(self):
        for branch in ("prod", "staging", "dev", "main", "master"):
            is_valid, _ = validate_branch_name(branch)
            assert is_valid is True

    def test_invalid_no_slash(self):
        is_valid, error = validate_branch_name("add-login")
        assert is_valid is False
        assert "type" in error.lower() or "formatted" in error.lower()

    def test_invalid_unknown_type(self):
        is_valid, error = validate_branch_name("feature/add-login")
        assert is_valid is False
        assert "Invalid branch type" in error

    def test_invalid_empty_description(self):
        is_valid, error = validate_branch_name("feat/")
        assert is_valid is False

    def test_invalid_too_long(self):
        long_name = "feat/" + "a" * 80
        is_valid, error = validate_branch_name(long_name)
        assert is_valid is False
        assert "too long" in error.lower()

    def test_valid_hotfix_branch(self):
        is_valid, _ = validate_branch_name("hotfix/INC-123-fix-payment")
        assert is_valid is True
