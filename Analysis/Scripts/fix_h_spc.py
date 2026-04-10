#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ATOM_SECTION = "@<TRIPOS>ATOM"

def process_one(path_str: str, backup: bool = True) -> tuple[str, int, str | None]:
    p = Path(path_str)
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

        in_atom = False
        changed = 0
        out = []

        for line in lines:
            if line.startswith(ATOM_SECTION):
                in_atom = True
                out.append(line)
                continue

            # saiu da seção ATOM ao encontrar qualquer outro @<TRIPOS>
            if line.startswith("@<TRIPOS>") and not line.startswith(ATOM_SECTION):
                in_atom = False
                out.append(line)
                continue

            if not in_atom:
                out.append(line)
                continue

            raw = line.rstrip("\n")
            if not raw.strip():
                out.append(line)
                continue

            parts = raw.split()
            # precisa ter pelo menos até atom_type
            if len(parts) < 6:
                out.append(line)
                continue

            atom_name = parts[1]   # H1, H2, HA...
            atom_type = parts[5]   # aqui que queremos H.spc

            # Regra LigBuilder: se o nome começa com H, o tipo deve ser H.spc
            if atom_name.startswith("H") and atom_type != "H.spc":
                # achar exatamente o 6º token na linha original e substituir preservando espaços
                spans = []
                i = 0
                n = len(raw)
                while i < n:
                    while i < n and raw[i].isspace():
                        i += 1
                    if i >= n:
                        break
                    j = i
                    while j < n and not raw[j].isspace():
                        j += 1
                    spans.append((i, j))
                    i = j

                if len(spans) >= 6:
                    a, b = spans[5]
                    old = raw[a:b]
                    new = "H.spc"
                    if len(old) > len(new):
                        new += " " * (len(old) - len(new))
                    raw = raw[:a] + new + raw[b:]
                    changed += 1

            out.append(raw + "\n")

        if changed > 0:
            if backup:
                bak = p.with_suffix(p.suffix + ".bak")
                if not bak.exists():
                    bak.write_text("".join(lines), encoding="utf-8")
            p.write_text("".join(out), encoding="utf-8")

        return (p.name, changed, None)

    except Exception as e:
        return (p.name, 0, f"{type(e).__name__}: {e}")

def main():
    ap = argparse.ArgumentParser(description="Força atom_type=H.spc para linhas H* na seção @<TRIPOS>ATOM (pasta atual).")
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1, help="Nº de processos (default: núcleos).")
    ap.add_argument("--no-backup", action="store_true", help="Não criar .bak.")
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