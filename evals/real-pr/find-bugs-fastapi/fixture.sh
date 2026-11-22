#!/usr/bin/env bash
# fastapi/fastapi PR 15745 at its pinned base and head, cloned from a local cache; no remote is left behind.
set -e
git clone -q /tmp/real-pr-cache/fastapi/fastapi.git .
git checkout -q refactor/router-tree
git remote remove origin
