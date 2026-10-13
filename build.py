"""Assemble the terminal page from web/.
  python3 build.py               -> index.html (static hosting: loads data/*.json next to it)
  python3 build.py --artifact F  -> F (claude.ai artifact body, same app, TRIGGER_ID from env)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = lambda p: open(os.path.join(HERE, "web", p), encoding="utf8").read()
import base64
def css():
    # police embarquée (Noto Sans variable, sous-ensemble latin, droit + italique ; licence SIL OFL) : aucune dépendance externe
    c = W("style.css")
    for f in ("ns-n", "ns-i"):
        b = base64.b64encode(open(os.path.join(HERE, "web", "fonts", f"{f}.woff2"), "rb").read()).decode()
        c = c.replace(f"url(fonts/{f}.woff2)", f"url(data:font/woff2;base64,{b})")
    return c
_ico = base64.b64encode(open(os.path.join(HERE, "web", "icons", "favicon.svg"), "rb").read()).decode()
HEAD = ('<title>FQT Terminal</title>\n'
        f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{_ico}">\n'
        '<meta name="description" content="Terminal de marché : BRVM (48 actions, indices, obligations, dividendes), UEMOA, actions US, macro, quant.">\n'
        '<meta name="robots" content="noindex, nofollow">\n'
        '<style>\n' + css() + '\n</style>\n')
import glob
import re
PAGES = sorted((os.path.basename(f) for f in glob.glob(os.path.join(HERE, "web", "pages*.js"))), key=lambda n: int(re.sub(r"\D", "", n) or 0))
JS = "".join("<script>\n" + W(f) + "\n</script>\n" for f in ["engine.js", "chart.js"] + PAGES + ["core.js"])
BODY = W("body.html")
if "--artifact" in sys.argv:
    out = sys.argv[sys.argv.index("--artifact") + 1]
    trig = os.environ.get("TRIGGER_ID", "__TRIGGER_ID__")
    open(out, "w", encoding="utf8").write(HEAD + BODY + JS.replace("'__TRIGGER_ID__'", "'" + trig + "'"))
    print("artifact", out)
else:
    html = ('<!doctype html>\n<html lang="fr"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="alternate icon" href="/favicon.ico">\n' + HEAD + '</head><body>\n' + BODY + JS + '</body></html>\n')
    open(os.path.join(HERE, "index.html"), "w", encoding="utf8").write(html)
    # dossier servi par Vercel (outputDirectory « public ») : main est déployable tel quel
    import shutil
    os.makedirs(os.path.join(HERE, "public"), exist_ok=True)
    open(os.path.join(HERE, "public", "index.html"), "w", encoding="utf8").write(html)
    shutil.copy(os.path.join(HERE, "deploy", "robots.txt"), os.path.join(HERE, "public", "robots.txt"))
    shutil.copy(os.path.join(HERE, "web", "fonts", "LICENSE-NotoSans.txt"), os.path.join(HERE, "public", "LICENSE-fonts.txt"))
    for f in ("favicon.ico", "favicon.svg", "apple-touch-icon.png"):  # icône propre au terminal (sinon le navigateur garde une ancienne icône)
        shutil.copy(os.path.join(HERE, "web", "icons", f), os.path.join(HERE, "public", f))
    print("index.html", len(html))
