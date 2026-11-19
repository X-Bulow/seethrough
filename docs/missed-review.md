# Auditing missed detections

`harness/audit-missed.py` checks whether a MISSED verdict is supported by the recorded build settings, execution markers, control outcomes, and raw diagnostics. Run it against one or more constructed-case result bundles:

```bash
python3 harness/audit-missed.py results/2026-11-13-lab-* \
  --replica results/2026-11-10-ec2-b-{core,memsys5,lookaside,rewrite} --list
python3 harness/audit-missed.py results/2026-11-13-lima-hwasan --list
```

The script exits with status 1 if a mechanical check fails. It checks that defects reached `ST READY`, controls are clean, execution completed or has a recorded crash, and diagnostics do not contain an overlooked defect report. For Memcheck it also checks the error summary. `--replica` compares verdicts with another machine's bundles. This audit covers constructed cases; the real SQLite runner uses separate reachability markers and an ASan/rewrite gate.

## Mechanisms behind missed detections

| Mechanism | Explanation |
|---|---|
| Hidden suballocation | The detector sees the backing pool as one live allocation, so accesses between logical objects remain valid. |
| Access to another live object | Address-based annotations permit the destination object's bytes even when the access originates from a different object. |
| Reuse | Once storage belongs to a new allocation, addressability alone cannot distinguish an old pointer. |
| Ownership error | ASan poisoning and HWASan tagging cannot describe a bad free that performs no invalid access; Memcheck mempool requests can describe ownership. |
| Tag granularity | HWASan's annotation interface tags 16-byte granules, leaving small alignment gaps with the object's tag. |
| Far access | An access beyond the pool may land outside poisoned memory or cause a signal without a boundary diagnosis. |
| Tag collision | A random HWASan tag can match a short-granule value and allow an otherwise invalid access. |

A signal-handler SEGV alone is not a defect diagnosis. The classifier records such bug executions as MISSED with a crash note. See [hwasan.md](hwasan.md) for tagging limitations and [allocator-annotations.md](allocator-annotations.md) for annotation precision.
