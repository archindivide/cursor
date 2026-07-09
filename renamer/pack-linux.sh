#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

RUNTIME="${RUNTIME:-linux-x64}"
OUT="artifacts/publish-${RUNTIME}"

if [[ "${1:-}" == "--framework-dependent" ]]; then
  dotnet publish Renamer.csproj -c Release -r "$RUNTIME" -o "$OUT" --self-contained false
else
  dotnet publish Renamer.csproj -c Release -r "$RUNTIME" -o "$OUT" --self-contained true \
    -p:PublishSingleFile=true \
    -p:IncludeNativeLibrariesForSelfExtract=true
fi

echo ""
echo "Output: $OUT"
echo "Run: chmod +x Renamer && ./Renamer [options]"
