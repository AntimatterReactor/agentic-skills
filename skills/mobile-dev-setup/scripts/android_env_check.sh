#!/usr/bin/env bash
# Read-only Android toolchain check for a Gradle project (Linux, WSL, macOS).
# Usage: android_env_check.sh [project_dir] [--devices]
#   --devices  also run `adb devices` (starts the adb server if it is not running)
# Prints PASS / WARN / FAIL / INFO lines; exit 1 when any FAIL.
set -uo pipefail

dir="."
devices=0
for a in "$@"; do
  case "$a" in
    --devices) devices=1 ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) dir="$a" ;;
  esac
done
cd "$dir" || { echo "FAIL no such directory: $dir"; exit 1; }

fails=0
pass() { echo "PASS $*"; }
warn() { echo "WARN $*"; }
info() { echo "INFO $*"; }
fail() { echo "FAIL $*"; fails=$((fails + 1)); }

# --- platform -------------------------------------------------------------
wsl=0
if grep -qi microsoft /proc/version 2>/dev/null; then
  wsl=1
  info "WSL detected: USB phones need usbipd on Windows (usbipd attach --wsl --busid <id>); adb server must run as root if 'no permissions'"
fi

# --- project shape --------------------------------------------------------
if [[ -f gradlew ]]; then
  [[ -x gradlew ]] && pass "gradlew is executable" || fail "gradlew is not executable (chmod +x gradlew)"
else
  fail "no gradlew here; run from the project root (the dir holding settings.gradle[.kts])"
fi
settings=$(ls settings.gradle.kts settings.gradle 2>/dev/null | head -1)
[[ -n "$settings" ]] && pass "found $settings" || fail "no settings.gradle[.kts]"

wrapper=gradle/wrapper/gradle-wrapper.properties
if [[ -f $wrapper ]]; then
  info "Gradle wrapper: $(sed -n 's/.*gradle-\(.*\)-\(bin\|all\)\.zip.*/\1/p' $wrapper | head -1)"
fi

# --- JDK ------------------------------------------------------------------
if command -v java >/dev/null 2>&1; then
  jv=$(java -version 2>&1 | head -1)
  pass "java on PATH: $jv"
else
  fail "no java on PATH (the wrapper needs a JDK to start; 17 is enough when a daemon toolchain is configured)"
fi
if [[ -f gradle/gradle-daemon-jvm.properties ]]; then
  tv=$(sed -n 's/^toolchainVersion=//p' gradle/gradle-daemon-jvm.properties)
  info "daemon JVM pinned to $tv (gradle-daemon-jvm.properties); a foojay resolver in settings provisions it"
  grep -q 'foojay' "$settings" 2>/dev/null && pass "foojay toolchain resolver configured" \
    || warn "daemon JVM is pinned but settings has no foojay-resolver; the toolchain may not auto-download"
fi

# --- Android SDK ----------------------------------------------------------
sdk=""
if [[ -f local.properties ]]; then
  sdk=$(sed -n 's/^sdk\.dir=//p' local.properties | head -1)
  sdk=${sdk//\\:/:}
fi
sdk=${sdk:-${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}}
[[ -z "$sdk" && -d "$HOME/Android/Sdk" ]] && sdk="$HOME/Android/Sdk"
if [[ -z "$sdk" ]]; then
  fail "no SDK found: set sdk.dir in local.properties (gitignored) or ANDROID_HOME"
elif [[ ! -d "$sdk" ]]; then
  fail "SDK dir does not exist: $sdk"
else
  pass "SDK at $sdk"
  [[ -f local.properties ]] || warn "no local.properties; Gradle may not find the SDK (it must be gitignored)"
  [[ -x $sdk/platform-tools/adb ]] && pass "platform-tools/adb present" || warn "no $sdk/platform-tools/adb"
  sm="$sdk/cmdline-tools/latest/bin/sdkmanager"
  [[ -x $sm ]] && pass "sdkmanager present (cmdline-tools/latest)" || warn "no cmdline-tools/latest; install it to accept licences and add packages"
  [[ -d $sdk/licenses ]] && pass "licences accepted dir present" || warn "no $sdk/licenses; run: sdkmanager --licenses"

  build_file=$(ls app/build.gradle.kts app/build.gradle 2>/dev/null | head -1)
  if [[ -n "$build_file" ]]; then
    csdk=$(grep -A3 -E 'compileSdk' "$build_file" | grep -oE '[0-9]{2}(\.[0-9]+)?' | head -1)  # also handles compileSdk { version = release(37) }
    if [[ -n "$csdk" ]]; then
      ls -d "$sdk"/platforms/android-"$csdk"* >/dev/null 2>&1 \
        && pass "platform android-$csdk installed" \
        || fail "compileSdk $csdk but no $sdk/platforms/android-$csdk* (sdkmanager \"platforms;android-$csdk\")"
    fi
    [[ -d $sdk/build-tools ]] && info "build-tools: $(ls "$sdk/build-tools" | tr '\n' ' ')" || warn "no build-tools installed"
  else
    info "no app/build.gradle[.kts]; skipped compileSdk check"
  fi
fi

# --- adb ------------------------------------------------------------------
if command -v adb >/dev/null 2>&1; then
  pass "adb on PATH: $(command -v adb)"
  if ((devices)); then
    out=$(timeout 10 adb devices 2>&1 | tail -n +2 | sed '/^$/d')
    [[ -z "$out" ]] && warn "adb sees no devices" || { echo "$out" | sed 's/^/INFO device: /'; echo "$out" | grep -q 'no permissions' && warn "'no permissions': adb kill-server && sudo adb start-server"; }
  fi
else
  warn "no adb on PATH (only needed for on-device runs)"
fi

# --- gradle.properties ----------------------------------------------------
if [[ -f gradle.properties ]]; then
  for k in org.gradle.parallel org.gradle.caching org.gradle.configuration-cache; do
    grep -qE "^$k=true" gradle.properties && pass "$k=true" || warn "$k not enabled in gradle.properties"
  done
  xmx=$(sed -n 's/.*-Xmx\([0-9]*[mMgG]\).*/\1/p' gradle.properties | head -1)
  [[ -n "$xmx" ]] && info "daemon heap -Xmx$xmx" || warn "no -Xmx in org.gradle.jvmargs (default heap is small for Robolectric/KSP builds)"
else
  warn "no gradle.properties"
fi

# --- version catalog ------------------------------------------------------
[[ -f gradle/libs.versions.toml ]] && pass "version catalog present" || info "no gradle/libs.versions.toml (a catalog keeps plugin and library versions in one place)"

# --- repo hygiene ---------------------------------------------------------
if [[ -d .git || -f .gitignore ]]; then
  gi_check() { # label, extended regex matched against .gitignore lines
    grep -qE "$2" .gitignore 2>/dev/null && pass ".gitignore covers $1" || warn ".gitignore does not cover $1"
  }
  gi_check local.properties '^/?local\.properties$'
  gi_check keystore.properties '^/?keystore\.properties$'
  gi_check '*.jks' '^\*\.jks$'
  gi_check '*.keystore' '^\*\.keystore$'
  gi_check build/ '^/?(\*\*/)?build/?$'
  if [[ -f .gitattributes ]] && grep -q 'filter=lfs' .gitattributes; then
    git lfs version >/dev/null 2>&1 && pass "git-lfs installed (repo uses LFS)" || fail "repo uses Git LFS but git-lfs is not installed; binaries would commit as pointers"
  fi
  [[ -f keystore.properties ]] && git check-ignore -q keystore.properties 2>/dev/null \
    && pass "keystore.properties exists and is ignored" || true
fi

# --- wrappers -------------------------------------------------------------
for s in build.sh test.sh scripts/loop.sh run_app.sh release.sh; do
  [[ -f $s ]] && { [[ -x $s ]] && pass "$s is executable" || warn "$s exists but is not executable"; }
done

echo
((fails)) && { echo "$fails FAIL(s)"; exit 1; } || { echo "no FAILs"; exit 0; }
