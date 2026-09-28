"""`python -m document_converter` opens the app; with CLI options it runs the CLI."""

import sys

_CLI_FLAGS = {"-t", "--to", "--formats", "--version", "-h", "--help", "-o", "--out-dir", "--overwrite"}


def main() -> int:
    # Files alone (from "Open with" or a drop on the app icon) should open the app, not the CLI.
    if any(arg.split("=", 1)[0] in _CLI_FLAGS for arg in sys.argv[1:]):
        from .cli import main as cli_main
        return cli_main()
    from .gui import main as gui_main
    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
