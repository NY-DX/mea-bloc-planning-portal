import sys, re
sys.path.insert(0, sys.argv[1])
from pa_render import node, render, split_bfs
out, repo = sys.argv[2], sys.argv[3]
GC, LBL = "GroupContainer@1.5.0", "Label@2.5.1"
VAR = "BrowseLayout_Vertical_ThreeTextVariant_ver5.0"

def section(text, start, end=None):
    """Formula following a '// <start>' header in an edits file, up to the next '// ' header."""
    lines = text.split("\n"); out = []; on = False
    for l in lines:
        if l.startswith("// ") and start in l: on = True; continue
        if on and l.startswith("//"): break
        if on: out.append(l)
    return "\n".join(out).strip()

e7 = open(f"{repo}/rebuild/07f-planned-hire-edits.txt").read()
e9 = open(f"{repo}/rebuild/09b-delegation-edits.txt").read()
refresh = open(f"{repo}/rebuild/05b-PlanningScreen.OnVisible.fx.txt").read()
refresh = refresh[refresh.index("Set(psRecord, LookUp"):].strip()
state_text = section(e7, "lblPsFYState (inside galPsYears)  >  Text")
state_color = section(e7, "lblPsFYState  >  Color")
remove = section(e9, "lblPsRemoveHire  >  OnSelect")
assert state_text and state_color and remove

title_block = node("conPsTitleBlock", GC, {"DropShadow": "DropShadow.None", "FillPortions": "1",
    "LayoutDirection": "LayoutDirection.Vertical", "LayoutGap": "2", "LayoutJustifyContent": "LayoutJustifyContent.Center"}, [
    node("lblMainTitle", LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiInk", "FillPortions": "0",
        "FontWeight": "FontWeight.Bold", "Height": "36", "Size": "20",
        "Text": 'If(IsBlank(psSelected), "SELECT AN EMPLOYEE", Upper(psSelected.FullName))'}),
    node("lblMainPlaceholder", LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiMuted", "FillPortions": "0",
        "Height": "22", "Size": "11", "Text":
        'If(\n    IsBlank(psSelected),\n    "Pick someone from the list on the left.",\n'
        '    psSelected.AddressCode & "  ·  " & psSelected.EmployeeNo &\n'
        '    Switch(psSelected.Kind, "Mobility", "  ·  Mobility (assigned to one of your departments)", "Planned", "  ·  Planned hire", "")\n)'}),
], "AutoLayout")
remove_btn = node("lblPsRemoveHire", LBL, {"Align": "Align.Center", "BorderColor": "uiDanger", "BorderThickness": "1",
    "Color": "uiDanger", "FillPortions": "0", "FontWeight": "FontWeight.Bold", "Height": "36", "OnSelect": remove,
    "Size": "9", "Text": 'If(psConfirmRemove, "CLICK AGAIN TO REMOVE", "REMOVE PLANNED HIRE")',
    "Visible": '!IsBlank(psSelected) && psSelected.Kind = "Planned"', "Width": "170"})
years = node("galPsYears", "Gallery@2.15.0", {"BorderThickness": "0", "FillPortions": "0", "Height": "64",
    "Items": "psYears", "OnSelect": "Set(psFY, ThisItem.FY);\n" + refresh,
    "TemplateFill": "If(ThisItem.FY = psFY, RGBA(212, 160, 23, 0.18), RGBA(0, 0, 0, 0.04))",
    "TemplatePadding": "3", "TemplateSize": "64", "Visible": "!IsBlank(psSelected)", "Width": "490", "WrapCount": "5"}, [
    node("lblPsFYText", LBL, {"Align": "Align.Center", "Color": "If(ThisItem.FY = psFY, uiGold, uiInk)",
        "FontWeight": "FontWeight.Bold", "Height": "28", "OnSelect": "Select(Parent)", "Size": "14",
        "Text": "Text(ThisItem.FY)", "Width": "Parent.TemplateWidth", "X": "0", "Y": "6"}),
    node("lblPsFYState", LBL, {"Align": "Align.Center", "Color": state_color, "FontWeight": "FontWeight.Bold",
        "Height": "18", "OnSelect": "Select(Parent)", "Size": "7", "Text": state_text,
        "Width": "Parent.TemplateWidth", "X": "0", "Y": "36"}),
], VAR)
top = node("conPsTopBar", GC, {"AlignInContainer": "AlignInContainer.Stretch", "DropShadow": "DropShadow.None",
    "FillPortions": "0", "Height": "72", "LayoutAlignItems": "LayoutAlignItems.Center",
    "LayoutDirection": "LayoutDirection.Horizontal", "LayoutGap": "16", "LayoutMinHeight": "72"},
    [title_block, remove_btn, years], "AutoLayout")
for i, (t, lines) in enumerate(split_bfs([top], "conPlanMain"), 1):
    fn = f"{out}/11b-part{i:02d}-into-{t}.paste.yaml"
    open(fn, "w").write("\n".join(lines) + "\n")
    print(fn.split("/")[-1], len(lines), "lines")
