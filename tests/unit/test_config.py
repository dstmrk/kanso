"""Tests for application configuration management."""

import os
from pathlib import Path

import pytest

from app.core.config import AppConfig, _parse_bool


class TestParseBool:
    """Test _parse_bool helper function."""

    def test_parse_true_lowercase(self):
        """Should parse 'true' as True."""
        assert _parse_bool("true") is True

    def test_parse_true_uppercase(self):
        """Should parse 'TRUE' as True."""
        assert _parse_bool("TRUE") is True

    def test_parse_true_mixed_case(self):
        """Should parse 'True' as True."""
        assert _parse_bool("True") is True

    def test_parse_one_as_true(self):
        """Should parse '1' as True."""
        assert _parse_bool("1") is True

    def test_parse_yes_as_true(self):
        """Should parse 'yes' as True."""
        assert _parse_bool("yes") is True

    def test_parse_on_as_true(self):
        """Should parse 'on' as True."""
        assert _parse_bool("on") is True

    def test_parse_false_lowercase(self):
        """Should parse 'false' as False."""
        assert _parse_bool("false") is False

    def test_parse_zero_as_false(self):
        """Should parse '0' as False."""
        assert _parse_bool("0") is False

    def test_parse_no_as_false(self):
        """Should parse 'no' as False."""
        assert _parse_bool("no") is False

    def test_parse_off_as_false(self):
        """Should parse 'off' as False."""
        assert _parse_bool("off") is False

    def test_parse_none_returns_default_false(self):
        """Should return False when value is None and no default provided."""
        assert _parse_bool(None) is False

    def test_parse_none_returns_custom_default(self):
        """Should return custom default when value is None."""
        assert _parse_bool(None, default=True) is True

    def test_parse_invalid_string_as_false(self):
        """Should parse invalid strings as False."""
        assert _parse_bool("invalid") is False
        assert _parse_bool("") is False
        assert _parse_bool("maybe") is False


class TestAppConfigDataclass:
    """Test AppConfig dataclass structure."""

    def test_app_config_has_required_attributes(self, tmp_path):
        """Should have all required attributes."""
        config = AppConfig(app_root=tmp_path)

        assert hasattr(config, "app_root")
        assert hasattr(config, "environment")
        assert hasattr(config, "debug")
        assert hasattr(config, "log_level")
        assert hasattr(config, "assets_sheet_name")
        assert hasattr(config, "liabilities_sheet_name")
        assert hasattr(config, "expenses_sheet_name")
        assert hasattr(config, "incomes_sheet_name")
        assert hasattr(config, "app_port")
        assert hasattr(config, "title")
        assert hasattr(config, "default_theme")

    def test_app_config_defaults(self, tmp_path):
        """Should have correct default values."""
        config = AppConfig(app_root=tmp_path)

        assert config.environment == "prod"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.static_files_folder == "static"
        assert config.assets_sheet_name == "Assets"
        assert config.liabilities_sheet_name == "Liabilities"
        assert config.expenses_sheet_name == "Expenses"
        assert config.incomes_sheet_name == "Incomes"
        assert config.app_port == 9525
        assert config.root_path == ""
        assert config.title == "kanso - your minimal money tracker"
        assert config.default_theme == "light"
        assert config.reload is False
        assert config.uvicorn_log_level == "warning"
        assert config.cache_ttl_seconds == 86400


class TestAppConfigFromEnv:
    """Test AppConfig.from_env classmethod."""

    def test_from_env_with_defaults(self, tmp_path, monkeypatch):
        """Should load with default values when env vars not set."""
        # Clear all relevant env vars
        for key in os.environ.copy():
            if key.startswith(
                (
                    "APP_",
                    "DEBUG",
                    "LOG_",
                    "STATIC_",
                    "ASSETS_",
                    "LIABILITIES_",
                    "EXPENSES_",
                    "INCOMES_",
                    "ROOT_",
                    "DEFAULT_",
                    "RELOAD",
                    "UVICORN_",
                    "CACHE_",
                )
            ):
                monkeypatch.delenv(key, raising=False)

        config = AppConfig.from_env(tmp_path)

        assert config.app_root == tmp_path
        assert config.environment == "prod"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.app_port == 9525

    def test_from_env_with_custom_values(self, tmp_path, monkeypatch):
        """Should load custom values from environment variables."""
        monkeypatch.setenv("APP_ENV", "dev")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "debug")
        monkeypatch.setenv("APP_PORT", "8080")
        monkeypatch.setenv("APP_TITLE", "Custom Title")
        monkeypatch.setenv("DEFAULT_THEME", "dark")
        monkeypatch.setenv("RELOAD", "yes")
        monkeypatch.setenv("CACHE_TTL_SECONDS", "3600")

        config = AppConfig.from_env(tmp_path)

        assert config.environment == "dev"
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.app_port == 8080
        assert config.title == "Custom Title"
        assert config.default_theme == "dark"
        assert config.reload is True
        assert config.cache_ttl_seconds == 3600

    def test_from_env_with_sheet_names(self, tmp_path, monkeypatch):
        """Should load custom sheet names from environment."""
        monkeypatch.setenv("ASSETS_SHEET_NAME", "MyAssets")
        monkeypatch.setenv("LIABILITIES_SHEET_NAME", "MyLiabilities")
        monkeypatch.setenv("EXPENSES_SHEET_NAME", "MyExpenses")
        monkeypatch.setenv("INCOMES_SHEET_NAME", "MyIncomes")

        config = AppConfig.from_env(tmp_path)

        assert config.assets_sheet_name == "MyAssets"
        assert config.liabilities_sheet_name == "MyLiabilities"
        assert config.expenses_sheet_name == "MyExpenses"
        assert config.incomes_sheet_name == "MyIncomes"

    def test_from_env_with_static_folder(self, tmp_path, monkeypatch):
        """Should load custom static folder from environment."""
        monkeypatch.setenv("STATIC_FILES_FOLDER", "public")

        config = AppConfig.from_env(tmp_path)

        assert config.static_files_folder == "public"

    def test_from_env_with_root_path(self, tmp_path, monkeypatch):
        """Should load custom root path from environment."""
        monkeypatch.setenv("ROOT_PATH", "/api/v1")

        config = AppConfig.from_env(tmp_path)

        assert config.root_path == "/api/v1"

    def test_from_env_with_uvicorn_log_level(self, tmp_path, monkeypatch):
        """Should load custom Uvicorn log level from environment."""
        monkeypatch.setenv("UVICORN_LOG_LEVEL", "info")

        config = AppConfig.from_env(tmp_path)

        assert config.uvicorn_log_level == "info"

    def test_from_env_debug_parsing_variations(self, tmp_path, monkeypatch):
        """Should parse various boolean representations for DEBUG."""
        test_cases = [
            ("true", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("DEBUG", env_value)
            config = AppConfig.from_env(tmp_path)
            assert config.debug is expected, f"Failed for DEBUG={env_value}"

    def test_from_env_reload_parsing_variations(self, tmp_path, monkeypatch):
        """Should parse various boolean representations for RELOAD."""
        test_cases = [
            ("true", True),
            ("1", True),
            ("false", False),
            ("0", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("RELOAD", env_value)
            config = AppConfig.from_env(tmp_path)
            assert config.reload is expected, f"Failed for RELOAD={env_value}"

    def test_from_env_log_level_uppercase_conversion(self, tmp_path, monkeypatch):
        """Should convert log level to uppercase."""
        monkeypatch.setenv("LOG_LEVEL", "debug")

        config = AppConfig.from_env(tmp_path)

        assert config.log_level == "DEBUG"

    def test_from_env_int_port_conversion(self, tmp_path, monkeypatch):
        """Should convert port to integer."""
        monkeypatch.setenv("APP_PORT", "8000")

        config = AppConfig.from_env(tmp_path)

        assert isinstance(config.app_port, int)
        assert config.app_port == 8000

    def test_from_env_int_cache_ttl_conversion(self, tmp_path, monkeypatch):
        """Should convert cache TTL to integer."""
        monkeypatch.setenv("CACHE_TTL_SECONDS", "7200")

        config = AppConfig.from_env(tmp_path)

        assert isinstance(config.cache_ttl_seconds, int)
        assert config.cache_ttl_seconds == 7200


class TestAppConfigStaticPath:
    """Test static_path property."""

    def test_static_path_returns_full_path(self, tmp_path):
        """Should return full absolute path to static files."""
        config = AppConfig(app_root=tmp_path, static_files_folder="static")

        static_path = config.static_path

        assert static_path == tmp_path / "static"
        assert isinstance(static_path, Path)

    def test_static_path_with_custom_folder(self, tmp_path):
        """Should return path with custom static folder name."""
        config = AppConfig(app_root=tmp_path, static_files_folder="public")

        static_path = config.static_path

        assert static_path == tmp_path / "public"

    def test_static_path_is_absolute(self, tmp_path):
        """Should return absolute path."""
        config = AppConfig(app_root=tmp_path)

        static_path = config.static_path

        assert static_path.is_absolute()


class TestAppConfigValidate:
    """Test validate method."""

    def test_validate_succeeds_when_static_folder_exists(self, tmp_path):
        """Should not raise error when static folder exists."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()

        config = AppConfig(app_root=tmp_path, static_files_folder="static")

        # Should not raise
        config.validate()

    def test_validate_fails_when_static_folder_missing(self, tmp_path):
        """Should raise FileNotFoundError when static folder doesn't exist."""
        config = AppConfig(app_root=tmp_path, static_files_folder="static")

        with pytest.raises(FileNotFoundError) as exc_info:
            config.validate()

        assert "Static files folder not found" in str(exc_info.value)
        assert "static" in str(exc_info.value)

    def test_validate_with_custom_folder_name(self, tmp_path):
        """Should validate custom static folder name."""
        public_dir = tmp_path / "public"
        public_dir.mkdir()

        config = AppConfig(app_root=tmp_path, static_files_folder="public")

        # Should not raise
        config.validate()

    def test_validate_fails_with_custom_folder_missing(self, tmp_path):
        """Should raise error when custom static folder doesn't exist."""
        config = AppConfig(app_root=tmp_path, static_files_folder="public")

        with pytest.raises(FileNotFoundError) as exc_info:
            config.validate()

        assert "public" in str(exc_info.value)


class TestAppConfigIntegration:
    """Integration tests for AppConfig."""

    def test_full_config_lifecycle(self, tmp_path, monkeypatch):
        """Should load from env, validate, and access properties."""
        # Setup environment
        monkeypatch.setenv("APP_ENV", "dev")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("APP_PORT", "8080")

        # Create static folder
        static_dir = tmp_path / "static"
        static_dir.mkdir()

        # Load config
        config = AppConfig.from_env(tmp_path)

        # Validate
        config.validate()

        # Access properties
        assert config.static_path == static_dir
        assert config.environment == "dev"
        assert config.debug is True
        assert config.app_port == 8080

    def test_config_with_all_env_vars_set(self, tmp_path, monkeypatch):
        """Should handle all environment variables set at once."""
        # Set all possible env vars
        env_vars = {
            "APP_ENV": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "warning",
            "STATIC_FILES_FOLDER": "assets",
            "ASSETS_SHEET_NAME": "CustomAssets",
            "LIABILITIES_SHEET_NAME": "CustomLiabilities",
            "EXPENSES_SHEET_NAME": "CustomExpenses",
            "INCOMES_SHEET_NAME": "CustomIncomes",
            "APP_PORT": "3000",
            "ROOT_PATH": "/app",
            "APP_TITLE": "My Finance App",
            "DEFAULT_THEME": "dark",
            "RELOAD": "true",
            "UVICORN_LOG_LEVEL": "debug",
            "CACHE_TTL_SECONDS": "1800",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = AppConfig.from_env(tmp_path)

        # Verify all values were loaded correctly
        assert config.environment == "production"
        assert config.debug is False
        assert config.log_level == "WARNING"
        assert config.static_files_folder == "assets"
        assert config.assets_sheet_name == "CustomAssets"
        assert config.liabilities_sheet_name == "CustomLiabilities"
        assert config.expenses_sheet_name == "CustomExpenses"
        assert config.incomes_sheet_name == "CustomIncomes"
        assert config.app_port == 3000
        assert config.root_path == "/app"
        assert config.title == "My Finance App"
        assert config.default_theme == "dark"
        assert config.reload is True
        assert config.uvicorn_log_level == "debug"
        assert config.cache_ttl_seconds == 1800
