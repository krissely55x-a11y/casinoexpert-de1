"""Shared paths for the onlinecasinoexperte.org repository."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"
SRC = ROOT / "src"
PUBLIC = ROOT / "public"
DIST = ROOT / "dist"
REPORTS = ROOT / "reports"
ARCHIVE = ROOT / "archive"
