"""Unit tests for conventional commit validation and rewriting."""

import pytest

from src.lib.conventional import validate, parse, rewrite_message, is_hotfix_allowed, VALID_TYPES


@pytest.mark.unit
class TestValidate:
    """Tests for the validate() function."""

    def test_valid_simple(self):
        assert validate("feat: add login page") is True

    def test_valid_with_scope(self):
        assert validate("fix(auth): handle null token") is True

    def test_valid_all_types(self):
        for commit_type in VALID_TYPES:
            assert validate(f"{commit_type}: some description") is True

    def test_valid_with_body(self):
        msg = "feat(api): add pagination\n\nAdded limit/offset params to the query layer."
        assert validate(msg) is True

    def test_invalid_no_type(self):
        assert validate("add login page") is False

    def test_invalid_no_colon(self):
        assert validate("feat add login page") is False

    def test_invalid_no_space_after_colon(self):
        assert validate("feat:add login page") is False

    def test_invalid_unknown_type(self):
        assert validate("feature: add login page") is False

    def test_invalid_empty(self):
        assert validate("") is False

    def test_invalid_just_type(self):
        assert validate("feat:") is False

    def test_valid_scope_with_hyphens(self):
        assert validate("fix(user-auth): handle edge case") is True

    def test_valid_scope_with_underscore(self):
        assert validate("refactor(api_client): simplify retry logic") is True

    def test_invalid_scope_with_spaces(self):
        assert validate("fix(user auth): handle edge case") is False

    def test_valid_hotfix_type(self):
        assert validate("hotfix: fix payment timeout") is True


@pytest.mark.unit
class TestParse:
    """Tests for the parse() function."""

    def test_parse_simple(self):
        result = parse("feat: add login")
        assert result == {"type": "feat", "scope": None, "description": "add login"}

    def test_parse_with_scope(self):
        result = parse("fix(auth): handle null token")
        assert result == {"type": "fix", "scope": "auth", "description": "handle null token"}

    def test_parse_invalid(self):
        assert parse("bad message") is None

    def test_parse_extracts_first_line(self):
        result = parse("feat: add login\n\nBody text here")
        assert result == {"type": "feat", "scope": None, "description": "add login"}


@pytest.mark.unit
class TestRewrite:
    """Tests for the rewrite_message() function."""

    def test_rewrite_fix_keyword(self):
        result = rewrite_message("fixed the bug")
        assert result == "fix: fixed the bug"

    def test_rewrite_add_keyword(self):
        result = rewrite_message("added new endpoint")
        assert result == "feat: added new endpoint"

    def test_rewrite_test_keyword(self):
        result = rewrite_message("updated tests for auth")
        assert result == "test: updated tests for auth"

    def test_rewrite_refactor_keyword(self):
        result = rewrite_message("refactored the payment module")
        assert result == "refactor: refactored the payment module"

    def test_rewrite_docs_keyword(self):
        result = rewrite_message("document the API usage")
        assert result == "docs: document the API usage"

    def test_rewrite_wip_drops(self):
        assert rewrite_message("WIP") is None
        assert rewrite_message("wip") is None

    def test_rewrite_temp_drops(self):
        assert rewrite_message("tmp") is None
        assert rewrite_message("temp") is None

    def test_rewrite_typo_drops(self):
        assert rewrite_message("typo") is None

    def test_rewrite_unknown_returns_none(self):
        assert rewrite_message("random gibberish") is None

    def test_rewrite_build_keyword(self):
        result = rewrite_message("upgrade dependencies")
        assert result == "build: upgrade dependencies"

    def test_rewrite_style_keyword(self):
        result = rewrite_message("format code with prettier")
        assert result == "style: format code with prettier"

    def test_rewrite_ci_keyword(self):
        result = rewrite_message("ci pipeline update")
        assert result == "ci: ci pipeline update"

    def test_rewrite_perf_keyword(self):
        result = rewrite_message("optimize query performance")
        assert result == "perf: optimize query performance"


@pytest.mark.unit
class TestIsHotfixAllowed:
    """Tests for is_hotfix_allowed() function."""

    def test_allowed_on_hotfix_branch(self):
        assert is_hotfix_allowed("hotfix/PROJ-123-fix-payment") is True

    def test_allowed_on_hotfix_branch_no_ticket(self):
        assert is_hotfix_allowed("hotfix/fix-payment") is True

    def test_not_allowed_on_feature_branch(self):
        assert is_hotfix_allowed("feat/add-login") is False

    def test_not_allowed_on_dev(self):
        assert is_hotfix_allowed("dev") is False

    def test_not_allowed_on_main(self):
        assert is_hotfix_allowed("main") is False
