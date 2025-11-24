#!/usr/bin/env bash
set -euo pipefail

# ====== CONFIG ======
PROJECT_NAME="todolist"
SETTINGS_FILE="todo/settings.py"
VERSION_VAR="APP_VERSION"
# ====================

usage() {
  echo "Usage: ./build.sh version=X.Y.Z"
  echo "Exemple: ./build.sh version=1.0.1"
  exit 1
}

# ---- Lire le paramètre version=... ----
if [[ $# -ne 1 ]]; then usage; fi

if [[ "$1" =~ ^version=([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
  VERSION="${BASH_REMATCH[1]}"
else
  echo "Not a good parameter: $1"
  usage
fi

# ---- Checks ----
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Not in a git repo."
  exit 1
}

[[ -f "$SETTINGS_FILE" ]] || {
  echo "File not found: $SETTINGS_FILE"
  exit 1
}

# ---- Ruff lint ----
echo "🔍 Running Ruff..."
if ! py -3.12 -m pipenv run ruff check .; then
    echo "Ruff lint failed. Fix the issues above before building."
    exit 1
fi
echo "Ruff passed"

# ---- Django tests ----
echo "🧪 Running Django tests..."
if ! py -3.12 -m pipenv run python manage.py test; then
    echo "⚠️ Django tests failed — continuing anyway (non-blocking)"
else
    echo "Tests passed"
fi

# ---- Update APP_VERSION ----
echo "Update version ${VERSION_VAR} -> ${VERSION}"

# Replace : APP_VERSION = "1.0.0"
if sed --version >/dev/null 2>&1; then
  # GNU sed (Linux)
  sed -i -E "s/^(${VERSION_VAR}[[:space:]]*=[[:space:]]*)[\"'][^\"']*[\"']/\1\"${VERSION}\"/" "$SETTINGS_FILE"
else
  # BSD sed (macOS)
  sed -i '' -E "s/^(${VERSION_VAR}[[:space:]]*=[[:space:]]*)[\"'][^\"']*[\"']/\1\"${VERSION}\"/" "$SETTINGS_FILE"
fi

grep -qE "^${VERSION_VAR}[[:space:]]*=[[:space:]]*\"${VERSION}\"" "$SETTINGS_FILE" || {
  echo "Line ${VERSION_VAR} not found/modified."
  echo "   Make sure you have: ${VERSION_VAR} = \"1.0.0\" in settings.py"
  exit 1
}

# ---- Commit the version ----
git add "$SETTINGS_FILE"
if git diff --cached --quiet; then
  echo "Nothing to commit (version already up to date)."
else
  git commit -m "chore: bump version to ${VERSION}"
fi

# ---- Tag the current commit ----
if git rev-parse "${VERSION}" >/dev/null 2>&1; then
  echo "❌ tag ${VERSION} already exists."
  exit 1
fi

echo "🏷️  Tag ${VERSION}"
git tag -a "${VERSION}" -m "Version ${VERSION}"

# ---- Generate the .zip tarball ----
ARCHIVE="${PROJECT_NAME}-${VERSION}.zip"
echo "📦 Generation ${ARCHIVE}"

git archive \
  --format=zip \
  --prefix="${PROJECT_NAME}-${VERSION}/" \
  --output="${ARCHIVE}" \
  "${VERSION}"

echo "✅ OK: ${ARCHIVE} generated."
echo "👉 Don't forget to push the tag: git push origin ${VERSION}"
