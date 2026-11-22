#!/usr/bin/env bash
# tox-dev/filelock PR 659 at its pinned base and head, cloned from a local cache; no remote is left behind.
set -e
git clone -q /tmp/real-pr-cache/filelock/filelock.git .
git checkout -q feat/strict-owner-claims
git remote remove origin
printf 'from __future__ import annotations\n\n__version__ = version = "0.0.0"\n__version_tuple__ = version_tuple = (0, 0, 0)\n' > src/filelock/version.py
