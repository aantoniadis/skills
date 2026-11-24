#!/usr/bin/env bash
# urllib3/urllib3 PR 5095 at its pinned base and head, cloned from a local cache; no remote is left behind.
set -e
git clone -q /tmp/real-pr-cache/urllib3/urllib3.git .
git checkout -q fix-percent-encode-hosts
git remote remove origin
printf '# This file is generated at build time.\nfrom __future__ import annotations\n\n__version__ = version = "2.6.0.dev0"\n__version_tuple__ = version_tuple = (2, 6, 0, "dev0")\n' > src/urllib3/_version.py
