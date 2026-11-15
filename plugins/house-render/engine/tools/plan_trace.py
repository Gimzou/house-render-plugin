"""Measure walls on a vector or scanned plan PDF at 1 px = 1 cm. Pure Python + poppler (pdftoppm/pdftotext).

Typical flow (see the update-from-plans skill):
  1. scale:  python3 plan_trace.py scale plan.pdf
       lists text with positions; read the graphic-scale labels (0 ... N m) or two ends of a written
       dimension and compute pt_per_m = (x_N - x_0) / N.
  2. raster: python3 plan_trace.py raster plan.pdf --pt-per-m 35.245 --out work/plan [--page 1]
       renders the page at 1 px = 1 cm (writes work/plan.ppm), prints the most common colours.
  3. wallcolor / map: python3 plan_trace.py map work/plan.ppm --rgb 104,101,90 [--tol 10] [--cell 20]
       ASCII map of wall pixels (one char = cell cm) to see the layout and pick scan lines.
  4. scan: python3 plan_trace.py scan work/plan.ppm --rgb 104,101,90 --rows 300,515 --cols 230,714
       exact wall runs (start, end) in px = cm along each row / column -> wall faces, door and window gaps.
  5. probe: python3 plan_trace.py probe work/plan.ppm --cols 1300 --rows 700 [--dark 170]
       runs of any dark ink (glazing lines, thin frames) where the wall colour filter finds nothing.
Always check one long traced distance against a written dimension and record the check in the data.
"""
import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path


def read_ppm(path):
    raw = Path(path).read_bytes()
    parts = raw.split(b"\n", 3)
    w, h = map(int, parts[1].split())
    return w, h, parts[3]


def runs(flags, minlen=3):
    out, s = [], None
    for i, f in enumerate(list(flags) + [False]):
        if f and s is None:
            s = i
        if not f and s is not None:
            if i - s >= minlen:
                out.append((s, i))
            s = None
    return out


def match(d, i, rgb, tol):
    return all(abs(d[3 * i + k] - rgb[k]) <= tol for k in range(3))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["scale", "raster", "map", "scan", "probe"])
    ap.add_argument("file")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--pt-per-m", type=float)
    ap.add_argument("--out")
    ap.add_argument("--rgb", help="wall colour r,g,b")
    ap.add_argument("--tol", type=int, default=10)
    ap.add_argument("--cell", type=int, default=20)
    ap.add_argument("--rows", default="")
    ap.add_argument("--cols", default="")
    ap.add_argument("--dark", type=int, default=170)
    a = ap.parse_args()

    if a.cmd == "scale":
        txt = subprocess.run(["pdftotext", "-bbox", "-f", str(a.page), "-l", str(a.page), a.file, "-"],
                             capture_output=True, text=True).stdout
        import re
        for m in re.finditer(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)<', txt):
            x0, y0, x1, y1, word = m.groups()
            print(f"{float(x0):8.2f} {float(y0):8.2f} {float(x1):8.2f} {float(y1):8.2f}  {word}")
        print("(empty = scanned PDF: measure the graphic scale on a raster instead)", file=sys.stderr)
        return

    if a.cmd == "raster":
        if not a.pt_per_m:
            sys.exit("--pt-per-m required (from the 'scale' step)")
        dpi = 72.0 * 100.0 / a.pt_per_m  # 100 px per metre
        out = a.out or str(Path(a.file).with_suffix(""))
        subprocess.run(["pdftoppm", "-r", f"{dpi:.4f}", "-f", str(a.page), "-l", str(a.page), "-singlefile",
                        a.file, out], check=True)
        w, h, d = read_ppm(out + ".ppm")
        c = Counter()
        for i in range(0, w * h, 7):
            c[(d[3 * i] // 8 * 8, d[3 * i + 1] // 8 * 8, d[3 * i + 2] // 8 * 8)] += 1
        print(f"wrote {out}.ppm  {w} x {h} px (= cm) at {dpi:.3f} dpi")
        print("most common colours (8-step bins); walls are usually a dark grey/black bin:")
        for k, n in c.most_common(15):
            print("  ", k, n)
        return

    w, h, d = read_ppm(a.file)
    if a.cmd in ("map", "scan"):
        rgb = tuple(int(x) for x in a.rgb.split(","))
        is_wall = lambda x, y: match(d, y * w + x, rgb, a.tol)  # noqa: E731
    else:
        is_wall = lambda x, y: sum(d[3 * (y * w + x) + k] for k in range(3)) / 3 < a.dark  # noqa: E731

    if a.cmd == "map":
        c = a.cell
        for y in range(0, h, c):
            row = "".join("#" if sum(is_wall(xx, yy) for yy in range(y, min(h, y + c), 2)
                                     for xx in range(x, min(w, x + c), 2)) > c * c / 16 else "."
                          for x in range(0, w, c))
            if "#" in row:
                print(f"{y:5d} {row.rstrip('.')}")
        print(f"(one char = {c} cm; left number = y in px/cm)")
        return

    minlen = 3 if a.cmd == "scan" else 1
    for y in [int(s) for s in a.rows.split(",") if s]:
        print(f"row y={y}:", runs((is_wall(x, y) for x in range(w)), minlen))
    for x in [int(s) for s in a.cols.split(",") if s]:
        print(f"col x={x}:", runs((is_wall(x, y) for y in range(h)), minlen))


if __name__ == "__main__":
    main()
