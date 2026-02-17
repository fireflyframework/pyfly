# tests/shell/test_exports.py
"""Tests for pyfly.shell public API exports."""


class TestShellExports:
    def test_core_decorators(self):
        from pyfly.shell import shell_argument, shell_component, shell_method, shell_option

        assert callable(shell_method)
        assert callable(shell_option)
        assert callable(shell_argument)
        assert callable(shell_component)

    def test_runner_protocols(self):
        from pyfly.shell import ApplicationArguments, ApplicationRunner, CommandLineRunner

        assert ApplicationArguments is not None
        assert CommandLineRunner is not None
        assert ApplicationRunner is not None

    def test_port(self):
        from pyfly.shell import ShellRunnerPort

        assert ShellRunnerPort is not None

    def test_models(self):
        from pyfly.shell import CommandResult, ShellParam

        assert ShellParam is not None
        assert CommandResult is not None
