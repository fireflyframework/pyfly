"""Tests for startup banner rendering."""

from pyfly.core.banner import BannerMode, BannerPrinter


class TestBannerMode:
    def test_text_mode(self):
        assert BannerMode.TEXT.value == "TEXT"

    def test_minimal_mode(self):
        assert BannerMode.MINIMAL.value == "MINIMAL"

    def test_off_mode(self):
        assert BannerMode.OFF.value == "OFF"


class TestBannerPrinterText:
    def test_default_banner_contains_ascii_art(self):
        printer = BannerPrinter(mode=BannerMode.TEXT, version="0.1.0")
        output = printer.render()
        assert "____" in output
        assert "PyFly" in output

    def test_default_banner_contains_version(self):
        printer = BannerPrinter(mode=BannerMode.TEXT, version="1.2.3")
        output = printer.render()
        assert "v1.2.3" in output

    def test_default_banner_contains_framework_line(self):
        printer = BannerPrinter(mode=BannerMode.TEXT, version="0.1.0")
        output = printer.render()
        assert ":: PyFly Framework ::" in output


class TestBannerPrinterMinimal:
    def test_minimal_banner_one_line(self):
        printer = BannerPrinter(mode=BannerMode.MINIMAL, version="0.1.0")
        output = printer.render()
        assert output.strip() == ":: PyFly :: (v0.1.0)"

    def test_minimal_banner_version(self):
        printer = BannerPrinter(mode=BannerMode.MINIMAL, version="2.0.0")
        output = printer.render()
        assert "v2.0.0" in output


class TestBannerPrinterOff:
    def test_off_returns_empty(self):
        printer = BannerPrinter(mode=BannerMode.OFF, version="0.1.0")
        output = printer.render()
        assert output == ""


class TestBannerPrinterCustomFile:
    def test_custom_banner_file(self, tmp_path):
        banner_file = tmp_path / "custom-banner.txt"
        banner_file.write_text("Hello ${pyfly.version} - ${app.name}")
        printer = BannerPrinter(
            mode=BannerMode.TEXT,
            version="0.1.0",
            app_name="OrderService",
            custom_location=str(banner_file),
        )
        output = printer.render()
        assert "Hello 0.1.0 - OrderService" in output

    def test_custom_banner_profiles_placeholder(self, tmp_path):
        banner_file = tmp_path / "banner.txt"
        banner_file.write_text("Profiles: ${profiles.active}")
        printer = BannerPrinter(
            mode=BannerMode.TEXT,
            version="0.1.0",
            active_profiles=["dev", "local"],
            custom_location=str(banner_file),
        )
        output = printer.render()
        assert "Profiles: dev, local" in output

    def test_missing_custom_file_falls_back_to_default(self):
        printer = BannerPrinter(
            mode=BannerMode.TEXT,
            version="0.1.0",
            custom_location="/nonexistent/banner.txt",
        )
        output = printer.render()
        assert ":: PyFly Framework ::" in output


class TestBannerFromConfig:
    def test_from_config_text_mode(self):
        from pyfly.core.config import Config

        config = Config({"pyfly": {"banner": {"mode": "TEXT"}}})
        printer = BannerPrinter.from_config(config, version="0.1.0")
        assert printer._mode == BannerMode.TEXT

    def test_from_config_off_mode(self):
        from pyfly.core.config import Config

        config = Config({"pyfly": {"banner": {"mode": "OFF"}}})
        printer = BannerPrinter.from_config(config, version="0.1.0")
        assert printer._mode == BannerMode.OFF

    def test_from_config_defaults_to_text(self):
        from pyfly.core.config import Config

        config = Config({})
        printer = BannerPrinter.from_config(config, version="0.1.0")
        assert printer._mode == BannerMode.TEXT
