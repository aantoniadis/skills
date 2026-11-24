#!/usr/bin/env bash
# pypa/pipx PR 2229 at its pinned base and head, cloned from a local cache; no remote is left behind.
set -e
git clone -q /tmp/real-pr-cache/pipx/pipx.git .
git checkout -q fix/force-retry-keeps-venv
git remote remove origin
git branch -D pr2229 upstream-main >/dev/null 2>&1 || true
printf 'from __future__ import annotations\n\n__version__ = version = "1.99.0.dev0"\n__version_tuple__ = version_tuple = (1, 99, 0, "dev0")\n' > src/pipx/version.py
