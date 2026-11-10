#!/usr/bin/env python3
"""Generate the B3 annotated memsys5 amalgamation from pinned SQLite 3.53.3.

The source in vendor/ stays pristine. Every replacement must match once, so
an upstream version change fails closed instead of silently omitting a hook.
"""
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_memsys5.py vendor/sqlite3.c build/sqlite3.c")
    source = Path(sys.argv[1]).read_text()

    def replace(old: str, new: str) -> None:
        nonlocal source
        count = source.count(old)
        if count != 1:
            raise SystemExit(f"memsys5 patch anchor matched {count} times: {old[:70]!r}")
        source = source.replace(old, new, 1)

    replace(
        "#ifdef SQLITE_ENABLE_MEMSYS5\n\n/*\n** A minimum allocation",
        "#ifdef SQLITE_ENABLE_MEMSYS5\n#include \"st_annot.h\"\n\n/*\n** A minimum allocation",
    )
    replace(
        "  next = MEM5LINK(i)->next;\n  prev = MEM5LINK(i)->prev;\n",
        "  ST_UNPOISON(MEM5LINK(i), sizeof(Mem5Link));\n"
        "  ST_DEFINED(MEM5LINK(i), sizeof(Mem5Link));\n"
        "  next = MEM5LINK(i)->next;\n  prev = MEM5LINK(i)->prev;\n",
    )
    replace(
        "    MEM5LINK(prev)->next = next;\n",
        "    ST_UNPOISON(MEM5LINK(prev), sizeof(Mem5Link));\n"
        "    ST_DEFINED(MEM5LINK(prev), sizeof(Mem5Link));\n"
        "    MEM5LINK(prev)->next = next;\n"
        "    ST_POISON(MEM5LINK(prev), sizeof(Mem5Link));\n"
        "    ST_NOACCESS(MEM5LINK(prev), sizeof(Mem5Link));\n",
    )
    replace(
        "    MEM5LINK(next)->prev = prev;\n  }\n}\n\n/*\n** Link the chunk",
        "    ST_UNPOISON(MEM5LINK(next), sizeof(Mem5Link));\n"
        "    ST_DEFINED(MEM5LINK(next), sizeof(Mem5Link));\n"
        "    MEM5LINK(next)->prev = prev;\n"
        "    ST_POISON(MEM5LINK(next), sizeof(Mem5Link));\n"
        "    ST_NOACCESS(MEM5LINK(next), sizeof(Mem5Link));\n"
        "  }\n"
        "  ST_POISON(MEM5LINK(i), sizeof(Mem5Link));\n"
        "  ST_NOACCESS(MEM5LINK(i), sizeof(Mem5Link));\n"
        "}\n\n/*\n** Link the chunk",
    )
    replace(
        "  x = MEM5LINK(i)->next = mem5.aiFreelist[iLogsize];\n  MEM5LINK(i)->prev = -1;\n",
        "  ST_UNPOISON(MEM5LINK(i), sizeof(Mem5Link));\n"
        "  ST_DEFINED(MEM5LINK(i), sizeof(Mem5Link));\n"
        "  x = MEM5LINK(i)->next = mem5.aiFreelist[iLogsize];\n"
        "  MEM5LINK(i)->prev = -1;\n",
    )
    replace(
        "    MEM5LINK(x)->prev = i;\n  }\n  mem5.aiFreelist[iLogsize] = i;\n",
        "    ST_UNPOISON(MEM5LINK(x), sizeof(Mem5Link));\n"
        "    ST_DEFINED(MEM5LINK(x), sizeof(Mem5Link));\n"
        "    MEM5LINK(x)->prev = i;\n"
        "    ST_POISON(MEM5LINK(x), sizeof(Mem5Link));\n"
        "    ST_NOACCESS(MEM5LINK(x), sizeof(Mem5Link));\n"
        "  }\n"
        "  mem5.aiFreelist[iLogsize] = i;\n"
        "  ST_POISON(MEM5LINK(i), sizeof(Mem5Link));\n"
        "  ST_NOACCESS(MEM5LINK(i), sizeof(Mem5Link));\n",
    )
    replace(
        "    p = memsys5MallocUnsafe(nBytes);\n    memsys5Leave();\n",
        "    p = memsys5MallocUnsafe(nBytes);\n"
        "    if( p ){\n"
        "      ST_POOL_ALLOC(mem5.zPool, p, nBytes);\n"
        "      ST_UNPOISON(p, nBytes);\n"
        "    }\n"
        "    memsys5Leave();\n",
    )
    replace(
        "static void memsys5Free(void *pPrior){\n  assert( pPrior!=0 );\n  memsys5Enter();\n  memsys5FreeUnsafe(pPrior);\n  memsys5Leave();\n}",
        "static void memsys5Free(void *pPrior){\n"
        "  int n;\n"
        "  assert( pPrior!=0 );\n"
        "  memsys5Enter();\n"
        "  n = memsys5Size(pPrior);\n"
        "  memsys5FreeUnsafe(pPrior);\n"
        "  ST_POOL_FREE(mem5.zPool, pPrior);\n"
        "  ST_POISON(pPrior, n);\n"
        "  memsys5Leave();\n}",
    )
    replace(
        "  mem5.aCtrl = (u8 *)&mem5.zPool[mem5.nBlock*mem5.szAtom];\n\n  for(ii=0; ii<=LOGMAX; ii++)",
        "  mem5.aCtrl = (u8 *)&mem5.zPool[mem5.nBlock*mem5.szAtom];\n"
        "  ST_POOL_CREATE(mem5.zPool, 0, 0);\n"
        "  ST_POISON(mem5.zPool, mem5.nBlock*mem5.szAtom);\n"
        "  ST_NOACCESS(mem5.zPool, mem5.nBlock*mem5.szAtom);\n\n"
        "  for(ii=0; ii<=LOGMAX; ii++)",
    )
    replace(
        "static void memsys5Shutdown(void *NotUsed){\n  UNUSED_PARAMETER(NotUsed);\n  mem5.mutex = 0;",
        "static void memsys5Shutdown(void *NotUsed){\n"
        "  UNUSED_PARAMETER(NotUsed);\n"
        "  ST_POOL_DESTROY(mem5.zPool);\n"
        "  ST_UNPOISON(mem5.zPool, mem5.nBlock*mem5.szAtom);\n"
        "  mem5.mutex = 0;",
    )
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(source)


if __name__ == "__main__":
    main()
