import sys
sys.path.insert(0, sys.argv[1])
from pa_render import node, render
out = sys.argv[2]
LBL = "Label@2.5.1"
def sess_btn(name, sess_expr):
    sel = f"psOvSession = {sess_expr}"
    return node(name, LBL, {"Align": "Align.Center", "BorderColor": "uiGold", "BorderThickness": "1",
        "Color": f"If({sel}, uiInk, uiGold)", "Fill": f"If({sel}, uiGold, RGBA(0, 0, 0, 0))", "FillPortions": "0",
        "FontWeight": "FontWeight.Bold", "Height": "36", "OnSelect": f"Set(psOvSession, {sess_expr})", "Size": "10",
        "Text": f'({sess_expr}) & " SESSION"', "Width": "140"})
lines = render(sess_btn("lblPsOvSessCur", "psSession")) + render(sess_btn("lblPsOvSessPrev", "psSession - 1"))
open(f"{out}/13b-into-conPsOvTop.paste.yaml", "w").write("\n".join(lines) + "\n")
print(len(lines), "lines")
