#!/bin/bash
# Print the app version: VERSION + "+<commit count>.<short sha>".
# Same rule as frontend/vite.config.ts and backend/app/core/version.py.
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
echo "$(cat "$root/VERSION")+$(git -C "$root" rev-list --count HEAD).$(git -C "$root" rev-parse --short HEAD)"
