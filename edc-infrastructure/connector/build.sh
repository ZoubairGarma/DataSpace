#!/usr/bin/env bash
# Usage : ./build.sh [tag-ou-commit-Samples]
set -euo pipefail
REF="${1:-main}"
docker build -t edc-connector:local --build-arg EDC_SAMPLES_REF="$REF" "$(dirname "$0")"
echo "OK : image edc-connector:local construite (Samples @ $REF)"
cd "$(dirname "$0")/.."
docker build -t edc-connector:local --build-arg EDC_SAMPLES_REF="$REF" .