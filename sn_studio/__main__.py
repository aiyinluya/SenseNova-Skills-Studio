"""CLI entry: python -m sn_studio [--port 7860] [--theme light|dark]

After UI layout changes: stop the running server, run ``python -m sn_studio`` again,
then hard-refresh the browser (Ctrl+F5) so Gradio CSS updates apply.
"""

from __future__ import annotations

import argparse

from sn_studio.ui.app import launch


def main() -> None:
    parser = argparse.ArgumentParser(prog="sn_studio", description="SenseNova Skills Studio")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=7860, help="Bind port")
    parser.add_argument("--share", action="store_true", help="Gradio public share link")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="UI theme")
    args = parser.parse_args()
    launch(host=args.host, port=args.port, share=args.share, theme=args.theme)


if __name__ == "__main__":
    main()
