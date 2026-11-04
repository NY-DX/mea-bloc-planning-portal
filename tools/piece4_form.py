import sys
sys.path.insert(0, sys.argv[1])
from pa_render import node, render, split, split_bfs
out_dir = sys.argv[2]

LOCK = "If(psLocked, DisplayMode.View, DisplayMode.Edit)"
GC, LBL = "GroupContainer@1.5.0", "Label@2.5.1"

def caption(name, text):
    return node(name, LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiMuted",
        "FillPortions": "0", "FontWeight": "FontWeight.Semibold", "Height": "18", "Size": "9", "Text": f'"{text}"'})

def field(name, cap, inner, visible=None):
    p = {"DropShadow": "DropShadow.None", "FillPortions": "1", "LayoutDirection": "LayoutDirection.Vertical", "LayoutGap": "4"}
    if visible: p["Visible"] = visible
    return node(name, GC, p, [caption(name.replace("fld", "lbl") + "Cap", cap), inner], "AutoLayout")

def combo(name, column, default, label):
    return node(name, "ComboBox@0.0.51", {"AccessibleLabel": f'"{label}"', "AlignInContainer": "AlignInContainer.Stretch",
        "DefaultSelectedItems": default, "DisplayMode": LOCK, "FillPortions": "0", "Height": "36",
        "Items": f"Choices([@EmployeeStatusTable].{column})"})

def choice_default(column, prefill=True):
    src = f"Coalesce(psRecord.{column}.Value, psPrev.{column}.Value)" if prefill else f"psRecord.{column}.Value"
    return f"Filter(Choices([@EmployeeStatusTable].{column}), Value = {src})"

def toggle(name, checked, label):
    return node(name, "Toggle@1.1.5", {"AccessibleLabel": f'"{label}"', "Checked": checked, "DisplayMode": LOCK,
        "Height": "36", "Label": 'If(Self.Checked, "Yes", "No")'})

def section(name, text):
    return node(name, LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiGold", "FillPortions": "0",
        "FontWeight": "FontWeight.Bold", "Height": "22", "Size": "10", "Text": f'"{text}"'})

def row(name, kids):
    return node(name, GC, {"AlignInContainer": "AlignInContainer.Stretch", "DropShadow": "DropShadow.None",
        "FillPortions": "0", "Height": "64", "LayoutDirection": "LayoutDirection.Horizontal", "LayoutGap": "24",
        "LayoutMinHeight": "64"}, kids, "AutoLayout")

GLOBAL = """Switch(
    cmbPsRegional.Selected.Value,
    "(MEA) E", "N/A",
    "(MEA) G1", "GG5", "(MEA) G1+", "GG5", "(MEA) G2", "GG5", "(MEA) G2+", "GG5",
    "(MEA) G3", "GG4", "(MEA) G3+", "GG4",
    "(MEA) G4M / G4P", "GG3",
    "(MEA) M2/G5", "GG2", "(MEA) M2+/G6", "GG2",
    "(MEA) M1/G7", "GG1",
    "—"
)"""
INFO = """If(
    IsBlank(psRecord),
    "FY" & psFY & " has no saved record yet" &
        If(IsBlank(psPrev), ".", ", so the fields are pre-filled from FY" & (psFY - 1) & "."),
    "FY" & psFY & " saved record, last updated " & Text(psRecord.'Last Updated', "dd mmm yyyy")
) & If(psLocked, "  Read-only: mobility employee managed by their home department.", "")"""

form = node("conPsForm", GC, {"AlignInContainer": "AlignInContainer.Stretch", "DropShadow": "DropShadow.None",
    "FillPortions": "1", "LayoutDirection": "LayoutDirection.Vertical", "LayoutGap": "10",
    "LayoutOverflowY": "LayoutOverflow.Scroll", "Visible": "!IsBlank(psSelected)"}, [
    node("lblPsRecordInfo", LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiMuted", "FillPortions": "0",
        "Height": "22", "Size": "10", "Text": INFO}),
    section("lblPsSecPosition", "POSITION"),
    row("conPsRowPosition", [
        field("fldPsBizCorp", "BIZ / CORP", combo("cmbPsBizCorp", "EmploymentType", choice_default("EmploymentType"), "Biz/Corp")),
        field("fldPsHRCode", "HR CODE", combo("cmbPsHRCode", "Division", choice_default("Division"), "HR Code")),
        field("fldPsAddress", "ADDRESS CODE", combo("cmbPsAddress", "AddressCode", choice_default("AddressCode"), "Address Code")),
    ]),
    section("lblPsSecGrade", "GRADE"),
    row("conPsRowGrade", [
        field("fldPsRegional", "REGIONAL GRADE", combo("cmbPsRegional", "RegionalGrade", choice_default("RegionalGrade"), "Regional Grade")),
        field("fldPsGlobal", "GLOBAL GRADE (FROM REGIONAL)", node("lblPsGlobalValue", LBL, {"AlignInContainer": "AlignInContainer.Stretch",
            "Color": "uiInk", "Fill": "RGBA(0, 0, 0, 0.04)", "FillPortions": "0", "FontWeight": "FontWeight.Semibold",
            "Height": "36", "PaddingLeft": "10", "Size": "12", "Text": GLOBAL})),
        field("fldPsPromotion", "PROMOTION THIS YEAR", toggle("tglPsPromotion", "Coalesce(psRecord.Promotion, false)", "Promotion")),
    ]),
    section("lblPsSecStatus", "STATUS"),
    row("conPsRowStatus", [
        field("fldPsHQ", "HQ EMPLOYMENT", toggle("tglPsHQ", "Coalesce(psRecord.HQEmployment, psPrev.HQEmployment, false)", "HQ Employment")),
        field("fldPsResignation", "RESIGNATION", toggle("tglPsResignation", "Coalesce(psRecord.Resignation, false)", "Resignation")),
        field("fldPsSuccession", "SUCCESSION NEEDED", toggle("tglPsSuccession", "Coalesce(psRecord.Succession, false)", "Succession")),
    ]),
    section("lblPsSecMobility", "MOBILITY / TRANSFER"),
    row("conPsRowMobility", [
        field("fldPsMobility", "ON MOBILITY", toggle("tglPsMobility", "Coalesce(psRecord.Mobility, psPrev.Mobility, false)", "Mobility")),
        field("fldPsMobRegion", "MOBILITY REGION", combo("cmbPsMobRegion", "MobilityRegion",
            "If(tglPsMobility.Checked, " + choice_default("MobilityRegion") + ")", "Mobility Region"), "tglPsMobility.Checked"),
        field("fldPsMobAC", "MOBILITY ADDRESS CODE", combo("cmbPsMobAC", "MobilityAC",
            "If(tglPsMobility.Checked, " + choice_default("MobilityAC") + ")", "Mobility Address Code"), "tglPsMobility.Checked"),
    ]),
    section("lblPsSecRemark", "REMARK"),
    node("txtPsRemark", "TextInput@0.0.54", {"AccessibleLabel": '"Remark"', "AlignInContainer": "AlignInContainer.Stretch",
        "DisplayMode": LOCK, "FillPortions": "0", "Height": "36", "Placeholder": '"Optional note for this year"',
        "Value": "psRecord.Remark"}),
], "AutoLayout")

full = render(form)
open(f"{out_dir}/04-form-FULL-into-conPlanMain.paste.yaml", "w").write("\n".join(full) + "\n")
print("full:", len(full), "lines")
for i, (target, lines) in enumerate(split_bfs([form], "conPlanMain"), 1):
    fn = f"{out_dir}/04-part{i:02d}-into-{target}.paste.yaml"
    open(fn, "w").write("\n".join(lines) + "\n")
    print(fn.split("/")[-1], len(lines), "lines")
