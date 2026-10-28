# camera-claim-audit

An offline static auditor for documentation about local device image capture
and attached imaging device intake. Source is parsed, never imported or run.
No runtime dependencies are required. Requires Python 3.9 or later.

Install and run:

```sh
python3 -m pip install .
camera-claim-audit /path/to/project
python3 -m camera_claim_audit /path/to/project --json --verbose
python3 -m unittest discover
```

Root README.md and Markdown beneath any docs path component supply claims.
Fenced blocks are excluded; inline code counts. Matching lowercases text,
expands negative contractions, replaces hyphens with spaces, and joins lines
within paragraphs. Exact word-boundary templates alone count; negative spans
are removed first. Bare device nouns and instructions to the user do not count.
Screen grabs, audio, speech, key input, clipboard operations and network sends
are outside this audit's scope.

Production evidence requires a provider-resolved cv2 VideoCapture device read,
a bound picamera2 Picamera2 capture method, or a bound legacy picamera PiCamera
capture or recording method. Plain assignments, self attributes and chained
calls are recognized per module. A string first argument to VideoCapture is a
file source. Object construction alone is insufficient. Tests, fixtures, docs,
examples and symlinks are excluded from production evidence. Evidence solely
in tests produces MEDIUM. Missing positive evidence and contradictory negative
documentation produce HIGH, at most one finding per family. Without source,
a positive assertion fails and a negative assertion passes. Without claims,
the result passes regardless of source evidence.

Options: --json emits structured findings and evidence; --verbose shows source
paths; repeat --ignore GLOB to exclude relative paths; --fail-on HIGH is the
default, while --fail-on MEDIUM also fails on test-only evidence. --version
prints 0.1.0. Exit codes are 0 for passing the threshold, 2 for findings meeting
the threshold, and 1 for invalid usage or unreadable roots. MEDIUM findings
remain visible even when the verdict is PASS.

## Limitations

Only the fixed templates in the package phrase table are recognized. This is
static evidence, not a hardware or runtime guarantee. Scope and control flow
are not modeled; bindings and imports are tracked per module. Dynamic imports,
wrapper functions, cross-module receivers, assignment aliases and shell imaging
helpers (ffmpeg, fswebcam, imagesnap) are not resolved. Strings, comments,
docstrings, file loaders, screen grabs, display and save operations alone are
insufficient. Environment files are never opened. Invalid source syntax supplies
no evidence. Ignore patterns use relative paths and standard glob matching.
