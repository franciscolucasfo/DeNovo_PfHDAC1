#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ATOM_SECTION = "@<TRIPOS>ATOM"

def format_atom_line(parts):
    """
    Reescreve linha ATOM com colunas alinhadas corretamente
    Mol2 esperado:
    atom_id atom_name x y z atom_type subst_id subst_name charge
    """

    atom_id = int(parts[0])
    atom_name = parts[1]
    x = float(parts[2])
    y = float(parts[3])
    z = float(parts[4])
    atom_type = parts[5]
    subst_id = int(parts[6]) if len(parts) > 6 else 1
    subst_name = parts[7] if len(parts) > 7 else "UNL1"
    charge = float(parts[8]) if len(parts) > 8 else 0.0

    return (
        f"{atom_id:7d} "
        f"{atom_name:<4s} "
        f"{x:10.4f} "
        f"{y:10.4f} "
        f"{z:10.4f} "
        f"{atom_type:<6s} "
        f"{subst_id:4d} "
        f"{subst_name:<6s} "
        f"{charge:10.4f}\n"
    )

def process_one(path_str: str, backup: bool = True):
    p = Path(path_str)
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=False)

        in_atom = False
        changed = 0
        out = []

        for line in lines:
            if line.startswith(ATOM_SECTION):
                in_atom = True
                out.append(line + "\n")
                continue

            if line.startswith("@<TRIPOS>") and not line.startswith(ATOM_SECTION):
                in_atom = False
                out.append(line + "\n")
                continue

            if not in_atom:
                out.append(line + "\n")
                continue

            if not line.strip():
                out.append(line + "\n")
                continue

            parts = line.split()

            if len(parts) < 6:
                out.append(line + "\n")
                continue

            atom_name = parts[1]
            atom_type = parts[5]

            # Forçar H.spc se nome começa com H
            if atom_name.startswith("H"):
                if atom_type != "H.spc":
                    parts[5] = "H.spc"
                    changed += 1

            # Reformatar linha completamente
            new_line = format_atom_line(parts)
            out.append(new_line)

        if changed > 0:
            if backup:
                bak = p.with_suffix(p.suffix + ".bak")
                if not bak.exists():
                    bak.write_text("\n".join(lines) + "\n", encoding="utf-8")

            p.write_text("".join(out), encoding="utf-8")

        return (p.name, changed, None)

    except Exception as e:
        return (p.name, 0, f"{type(e).__name__}: {e}")

def main():
    ap = argparse.ArgumentParser(
        description="Corrige H.spc e reindenta corretamente seção @<TRIPOS>ATOM."
    )
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    files = [str(p) for p in Path(".").glob("*.mol2") if p.is_file()]
    print(f"Encontrados {len(files)} arquivos .mol2 na pasta atual.")

    total = 0
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(process_one, f, not args.no_backup) for f in files]
        for fut in as_completed(futs):
            name, n, err = fut.result()
            if err:
                print(f"[ERRO] {name}: {err}")
            else:
                print(f"[OK] {name}: {n} mudanças")
                total += n

    print(f"\nTotal de substituições: {total}")

if __name__ == "__main__":
    main()