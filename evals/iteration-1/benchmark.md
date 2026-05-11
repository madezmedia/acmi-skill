# ACMI Skill Benchmark — Iteration 1

## Aggregate

| Config | Mean pass rate | Tokens (mean) | Duration (mean ms) | n |
|---|---|---|---|---|
| with_skill | 100% | 82988 | 58010 | 3 |
| without_skill | 60% | 69068 | 32307 | 3 |

**Delta pass rate (with − without): +40%**

## Per-eval

### eval-1-fresh-session-bootstrap

| Config | Pass rate | Passes/Total | Tokens | Duration (ms) |
|---|---|---|---|---|
| with_skill | 100% | 5/5 | 81803 | 70126 |
| without_skill | 80% | 4/5 | 69690 | 40180 |

### eval-2-log-milestone-with-chain

| Config | Pass rate | Passes/Total | Tokens | Duration (ms) |
|---|---|---|---|---|
| with_skill | 100% | 6/6 | 85499 | 41274 |
| without_skill | 33% | 2/6 | 68356 | 26478 |

### eval-3-session-end-rollup

| Config | Pass rate | Passes/Total | Tokens | Duration (ms) |
|---|---|---|---|---|
| with_skill | 100% | 6/6 | 81662 | 62629 |
| without_skill | 67% | 4/6 | 69159 | 30264 |
