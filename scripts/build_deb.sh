#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="daily-time-stats"
VERSION="0.1.0"
BUILD_DIR="$ROOT/build"
PYI_DIST="$ROOT/dist/$APP_NAME"
DEB_ROOT="$BUILD_DIR/debroot"
DEB_OUT="$ROOT/dist/deb"
ENTRYPOINT="$ROOT/scripts/entrypoint.py"

cd "$ROOT"
mkdir -p "$BUILD_DIR" "$ROOT/dist" "$DEB_OUT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYINSTALLER_ENV=()

if "$PYTHON_BIN" -m venv "$BUILD_DIR/venv" >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    . "$BUILD_DIR/venv/bin/activate"
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    pip install -e .
    PYINSTALLER_ENV=(python -m PyInstaller)
else
    echo "python3-venv unavailable; using project-local dependency target." >&2
    rm -rf "$BUILD_DIR/deps"
    "$PYTHON_BIN" -m pip install --target "$BUILD_DIR/deps" -r requirements.txt
    PYINSTALLER_ENV=(env "PYTHONPATH=$BUILD_DIR/deps:$ROOT/src" "$PYTHON_BIN" -m PyInstaller)
fi

"${PYINSTALLER_ENV[@]}" \
    --noconfirm \
    --clean \
    --name "$APP_NAME" \
    --windowed \
    --paths "$ROOT/src" \
    --add-data "$ROOT/src/daily_time_stats/assets:daily_time_stats/assets" \
    "$ENTRYPOINT"

rm -rf "$DEB_ROOT"
mkdir -p \
    "$DEB_ROOT/DEBIAN" \
    "$DEB_ROOT/opt/$APP_NAME" \
    "$DEB_ROOT/usr/bin" \
    "$DEB_ROOT/usr/share/applications" \
    "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps"

cp -a "$PYI_DIST/." "$DEB_ROOT/opt/$APP_NAME/"
cp "$ROOT/packaging/control" "$DEB_ROOT/DEBIAN/control"
cp "$ROOT/packaging/daily-time-stats.desktop" "$DEB_ROOT/usr/share/applications/daily-time-stats.desktop"
cp "$ROOT/src/daily_time_stats/assets/app-icon.svg" "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps/daily-time-stats.svg"
cp "$ROOT/packaging/daily-time-stats.sh" "$DEB_ROOT/usr/bin/daily-time-stats"
chmod 0755 "$DEB_ROOT/usr/bin/daily-time-stats"
chmod -R go-w "$DEB_ROOT"

dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DEB_OUT/${APP_NAME}_${VERSION}_amd64.deb"
echo "$DEB_OUT/${APP_NAME}_${VERSION}_amd64.deb"
