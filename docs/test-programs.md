# Test program READMEs (template)

Every `corpus/cases/caseNN-<slug>/README.md` is written in English under the headings below. The
report's Test Corpus section is compiled from these files.

```
# caseNN-<slug> — <one-line title>

## Defect
- Class: heap overflow / underflow / use-after-free / double free / invalid free
- Access: read / write / free
- In one line: which object, when, and how it is accessed illegally

## Trigger
- The allocation sequence (as alloc.h calls, with sizes and order)
- Which line holds the illegal access, and at what offset

## Memory layout
- under malloc: what lies between objects (malloc header, ASan redzone, alignment padding)
- under the arena: objects sit back to back, with only alignment slack between them
- under the free list: same size class; after a free, the next allocation gets the same block
(draw a small picture; ASCII is fine)

## Expected results and rationale
| tool | malloc | CMA unannotated | CMA annotated | rationale |
|---|---|---|---|---|
| ASan | DETECTED | MISSED | DETECTED | the 1-byte overflow lands in ... |
| Valgrind | ... | ... | ... | |
| HWASan | ... | ... | n/a | no CMA annotation interface |

## Negative control
- which line `-DST_NEGATIVE_CONTROL` changes, and why the allocation traffic is identical to the bug version
```

The full expected table lives in `case.json` (`expected`: one row per tool, one column per
allocator arm, plus a `why`); the README explains the rows that matter. Dated local runs go at the
end, each under its own `## Local smoke run (<date>, <machine>, development only, not citable)`
heading. An old run's section is never edited; a new run gets a new section.
