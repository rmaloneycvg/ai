"""Unit tests for file path → commit type heuristic detection."""

import pytest

from src.lib.detect_changes import detect_type, detect_scope, group_changes, sort_groups
from src.lib.git_ops import GitStatus, StatusEntry


@pytest.mark.unit
class TestDetectType:
    """Tests for detect_type() function."""

    # High confidence: test files
    def test_tests_directory(self):
        assert detect_type("tests/test_auth.py") == ("test", "high")

    def test_test_prefix(self):
        assert detect_type("test_utils.py") == ("test", "high")

    def test_test_suffix(self):
        assert detect_type("auth.test.ts") == ("test", "high")

    def test_spec_suffix(self):
        assert detect_type("auth.spec.ts") == ("test", "high")

    # High confidence: CI files
    def test_github_workflows(self):
        assert detect_type(".github/workflows/ci.yml") == ("ci", "high")

    def test_gitlab_ci(self):
        assert detect_type(".gitlab-ci.yml") == ("ci", "high")

    def test_jenkinsfile(self):
        assert detect_type("Jenkinsfile") == ("ci", "high")

    # High confidence: docs
    def test_docs_directory(self):
        assert detect_type("docs/api.md") == ("docs", "high")

    def test_changelog(self):
        assert detect_type("CHANGELOG.md") == ("docs", "high")

    def test_markdown_file(self):
        assert detect_type("README.md") == ("docs", "high")

    # High confidence: build/infra
    def test_dockerfile(self):
        assert detect_type("Dockerfile") == ("build", "high")

    def test_docker_compose(self):
        assert detect_type("docker-compose.yml") == ("build", "high")

    def test_k8s_directory(self):
        assert detect_type("k8s/deployment.yaml") == ("build", "high")

    def test_tiltfile(self):
        assert detect_type("Tiltfile") == ("build", "high")

    def test_terraform(self):
        assert detect_type("main.tf") == ("build", "high")

    # Medium confidence: dependency files
    def test_package_json(self):
        assert detect_type("package.json") == ("build", "medium")

    def test_pyproject_toml(self):
        assert detect_type("pyproject.toml") == ("build", "medium")

    # Medium confidence: style
    def test_css_file(self):
        assert detect_type("styles.css") == ("style", "medium")

    def test_scss_file(self):
        assert detect_type("theme.scss") == ("style", "medium")

    # Medium confidence: chore
    def test_gitignore(self):
        assert detect_type(".gitignore") == ("chore", "medium")

    def test_makefile(self):
        assert detect_type("Makefile") == ("chore", "medium")

    def test_scripts_directory(self):
        assert detect_type("scripts/deploy.sh") == ("chore", "medium")

    def test_editorconfig(self):
        assert detect_type(".editorconfig") == ("chore", "medium")

    # Default: new source files → feat
    def test_new_source_file(self):
        assert detect_type("src/auth/login.ts", is_new=True) == ("feat", "medium")

    # Default: modified source files → fix
    def test_modified_source_file(self):
        assert detect_type("src/auth/login.ts", is_new=False) == ("fix", "low")


@pytest.mark.unit
class TestDetectScope:
    """Tests for detect_scope() function."""

    def test_common_scope_under_src(self):
        files = ["src/auth/login.ts", "src/auth/session.ts"]
        assert detect_scope(files) == "auth"

    def test_common_scope_under_api(self):
        files = ["api/users/routes.ts", "api/users/handlers.ts"]
        assert detect_scope(files) == "users"

    def test_no_scope_multiple_dirs(self):
        files = ["src/auth/login.ts", "src/payments/checkout.ts"]
        assert detect_scope(files) is None

    def test_no_scope_root_files(self):
        files = ["README.md"]
        # Single part path — returns the filename which contains a dot, so returns None
        assert detect_scope(files) is None

    def test_scope_from_tests(self):
        files = ["tests/auth/test_login.py", "tests/auth/test_session.py"]
        assert detect_scope(files) == "auth"

    def test_empty_files(self):
        assert detect_scope([]) is None


@pytest.mark.unit
class TestGroupChanges:
    """Tests for group_changes() function."""

    def test_groups_by_type(self):
        status = GitStatus(
            staged=[
                StatusEntry(path="tests/test_auth.py", index="A", work_tree=" "),
                StatusEntry(path="src/auth/login.ts", index="A", work_tree=" "),
            ],
            unstaged=[],
            untracked=[],
        )
        groups = group_changes(status)
        assert "test" in groups
        assert "feat" in groups
        assert "tests/test_auth.py" in groups["test"]
        assert "src/auth/login.ts" in groups["feat"]

    def test_untracked_as_new(self):
        status = GitStatus(
            staged=[],
            unstaged=[],
            untracked=["src/new_feature.py"],
        )
        groups = group_changes(status)
        assert "feat" in groups
        assert "src/new_feature.py" in groups["feat"]

    def test_empty_status(self):
        status = GitStatus(staged=[], unstaged=[], untracked=[])
        groups = group_changes(status)
        assert groups == {}

    def test_modified_goes_to_fix(self):
        status = GitStatus(
            staged=[StatusEntry(path="src/api/handler.ts", index="M", work_tree=" ")],
            unstaged=[],
            untracked=[],
        )
        groups = group_changes(status)
        assert "fix" in groups


@pytest.mark.unit
class TestSortGroups:
    """Tests for sort_groups() function."""

    def test_sorts_ci_before_feat(self):
        groups = {"feat": ["a.ts"], "ci": ["ci.yml"]}
        sorted_result = sort_groups(groups)
        types = [t for t, _ in sorted_result]
        assert types.index("ci") < types.index("feat")

    def test_sorts_build_before_test(self):
        groups = {"test": ["test.py"], "build": ["Dockerfile"]}
        sorted_result = sort_groups(groups)
        types = [t for t, _ in sorted_result]
        assert types.index("build") < types.index("test")

    def test_all_types_have_defined_order(self):
        from src.lib.detect_changes import COMMIT_ORDER
        for t in ("ci", "build", "chore", "docs", "style", "refactor", "perf", "test", "fix", "feat"):
            assert t in COMMIT_ORDER
