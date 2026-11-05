#!/usr/bin/env bash
# Device-free dev loop for an Android Gradle project: run the JVM tests (and
# Roborazzi golden verification) and print ONLY what matters: failing tests,
# their first lines, golden diff percentages, and compile errors. Full log
# goes to <module>/build/loop.log. Exit code mirrors Gradle's.
#
# Usage: dev_loop.sh [--record] [--module app] [--dir PROJECT] [gradle args...]
#   --record        re-record goldens (:<module>:recordRoborazziDebug)
#   --module NAME   Gradle module (default: app)
#   --dir PROJECT   project root holding ./gradlew (default: .)
#   anything else   passed to Gradle, e.g. --tests '*ScreenTest'
# Env: LOOP_VERIFY_TASK / LOOP_RECORD_TASK override the task names, e.g. to run
#      plain :app:testDebugUnitTest in a project without Roborazzi.
set -uo pipefail

module=app
dir=.
record=0
pass=()
while (($#)); do
  case "$1" in
    --record) record=1 ;;
    --module) module="$2"; shift ;;
    --dir) dir="$2"; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) pass+=("$1") ;;
  esac
  shift
done
cd "$dir" || { echo "no such directory: $dir" >&2; exit 2; }
[[ -x ./gradlew ]] || { echo "no executable ./gradlew in $PWD" >&2; exit 2; }

task=${LOOP_VERIFY_TASK:-:$module:verifyRoborazziDebug}
((record)) && task=${LOOP_RECORD_TASK:-:$module:recordRoborazziDebug}

build=$module/build
log=$build/loop.log
mkdir -p "$build"
start=$SECONDS
./gradlew "$task" --console=plain "${pass[@]}" >"$log" 2>&1
status=$?

# Only trust result files from this run: Gradle leaves old ones behind when a
# build fails before tests (compile error), which would print stale failures.
if ((status == 0)) || grep -q "tests completed" "$log"; then
python3 -I - "$build" <<'EOF'
import glob, json, sys, xml.etree.ElementTree as ET
build = sys.argv[1]
fails = 0
for f in sorted(glob.glob(f'{build}/test-results/testDebugUnitTest/*.xml')):
    for tc in ET.parse(f).getroot().iter('testcase'):
        for bad in list(tc.iter('failure')) + list(tc.iter('error')):
            fails += 1
            msg = (bad.get('message') or bad.text or '').strip().splitlines()
            print(f"FAIL {tc.get('classname').rsplit('.', 1)[-1]}.{tc.get('name')}")
            for line in msg[:4]:
                print(f"     {line[:200]}")
for f in glob.glob(f'{build}/test-results/roborazzi/debug/results/*.json'):
    r = json.load(open(f))
    if r.get('type') == 'changed':
        print(f"DIFF {r['golden_file_path'].rsplit('/', 1)[-1]} {r.get('diff_percentage', 0) * 100:.2f}% -> {r.get('compare_file_path')}")
if fails:
    print(f"{fails} failing test(s)")
EOF
elif ((status != 0)); then
  grep -E "^e: |error:|What went wrong" -A3 "$log" | head -30
fi

verdict=PASS; ((status != 0)) && verdict=FAIL
echo "$verdict in $((SECONDS - start))s (log: $log)"
exit $status
