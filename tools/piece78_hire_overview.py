import sys
sys.path.insert(0, sys.argv[1])
from pa_render import node, render, split_bfs
out = sys.argv[2]
GC, LBL = "GroupContainer@1.5.0", "Label@2.5.1"

def write(prefix, nodes, target):
    for i, (t, lines) in enumerate(split_bfs(nodes, target), 1):
        fn = f"{out}/{prefix}{i:02d}-into-{t}.paste.yaml"
        open(fn, "w").write("\n".join(lines) + "\n")
        print(fn.split("/")[-1], len(lines), "lines")

def cap(name, text):
    return node(name, LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiMuted", "FillPortions": "0",
        "FontWeight": "FontWeight.Semibold", "Height": "18", "Size": "9", "Text": f'"{text}"'})

def btn(name, text, onselect, primary=False, extra=None):
    p = {"Align": "Align.Center", "FillPortions": "0", "FontWeight": "FontWeight.Bold", "Height": "40",
         "OnSelect": onselect, "Size": "11", "Text": text, "Width": "150"}
    if primary:
        p.update({"Color": "uiInk", "Fill": "If(Self.DisplayMode = DisplayMode.Edit, uiGold, uiGoldDim)"})
    else:
        p.update({"BorderColor": "uiGold", "BorderThickness": "1", "Color": "uiGold"})
    p.update(extra or {})
    return node(name, LBL, p)

# ---------------- piece 7: planned hires ----------------
add_btn = node("lblPsAddHire", LBL, {"Align": "Align.Center", "AlignInContainer": "AlignInContainer.Stretch",
    "BorderColor": "uiGold", "BorderThickness": "1", "Color": "uiGold", "FillPortions": "0",
    "FontWeight": "FontWeight.Bold", "Height": "36", "OnSelect": "Reset(txtPsHireName);\nSet(psShowHire, true)",
    "Size": "10", "Text": '"+  ADD PLANNED HIRE"'})
write("07b-part", [add_btn], "conPlanSidebar")

start_fy = node("lblPsStartFY", LBL, {"FillPortions": "0", "Text":
    '// Fiscal year in which a planned hire starts (blank for real employees)\n'
    'If(psSelected.Kind = "Planned" && StartsWith(psSelected.EmployeeNo, "TBH FY"), Right(psSelected.EmployeeNo, 4), "")',
    "Visible": "false", "Width": "0"})
write("07c-part", [start_fy], "conPlanFooter")

REMOVE = """If(
    !psConfirmRemove,
    Set(psConfirmRemove, true),

    Set(psConfirmRemove, false);
    Set(psHireError, "");
    IfError(
        RemoveIf(EmployeeStatusTable, Employee.Id = psSelected.ID);
        Remove(EmployeeTable, LookUp(EmployeeTable, ID = psSelected.ID));
        true,
        Set(psHireError, FirstError.Message)
    );
    If(
        IsBlank(psHireError),
        Notify("Removed planned hire " & psSelected.FullName & ".", NotificationType.Success);
        RemoveIf(psEmployees, ID = psSelected.ID);
        Set(psSelected, Blank());
        Clear(psStatus),
        Notify("Could not remove: " & psHireError, NotificationType.Error)
    )
)"""
remove = node("lblPsRemoveHire", LBL, {"Align": "Align.Center", "BorderColor": "uiDanger", "BorderThickness": "1",
    "Color": "uiDanger", "FillPortions": "0", "FontWeight": "FontWeight.Bold", "Height": "36", "OnSelect": REMOVE,
    "Size": "9", "Text": 'If(psConfirmRemove, "CLICK AGAIN TO REMOVE", "REMOVE PLANNED HIRE")',
    "Visible": 'psSelected.Kind = "Planned"', "Width": "190"})
write("07d-part", [remove], "conPsYearBar")

CREATE = """Set(psHireError, "");
IfError(
    Set(
        psNewHire,
        Patch(
            EmployeeTable,
            Defaults(EmployeeTable),
            {
                Title: Trim(txtPsHireName.Value),
                'FirstName ': Trim(txtPsHireName.Value),
                'LastName ': "",
                'Employee ID': "TBH FY" & cmbPsHireYear.Selected.Value,
                AddressCode: cmbPsHireDept.Selected,
                PlannedHire: true
            }
        )
    ),
    Set(psHireError, FirstError.Message)
);
If(
    IsBlank(psHireError),
    Collect(
        psEmployees,
        {
            ID: psNewHire.ID,
            FullName: Trim(txtPsHireName.Value),
            AddressCode: cmbPsHireDept.Selected.Value,
            EmployeeNo: "TBH FY" & cmbPsHireYear.Selected.Value,
            Kind: "Planned"
        }
    );
    Set(psSelected, LookUp(psEmployees, ID = psNewHire.ID));
    Set(psLocked, false);
    Set(psConfirmRemove, false);
    Clear(psStatus);
    Set(psFY, Value(cmbPsHireYear.Selected.Value));
    Set(psRecord, Blank());
    Set(psPrev, Blank());
    Set(psRegionalOverride, Blank());
    Set(psConfirmResign, false);
    Set(psShowHire, false);
    Notify("Planned hire created. Fill in FY" & psFY & " and press SAVE (or SAVE ALL for the later years).", NotificationType.Success),
    Notify("Could not create the planned hire: " & psHireError, NotificationType.Error)
)"""
panel = node("conPsHirePanel", GC, {"DropShadow": "DropShadow.Bold", "Fill": "uiBg", "FillPortions": "0", "Height": "420",
    "LayoutDirection": "LayoutDirection.Vertical", "LayoutGap": "10", "PaddingBottom": "24", "PaddingLeft": "28",
    "PaddingRight": "28", "PaddingTop": "24", "Width": "540"}, [
    node("lblPsHireTitle", LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiGold", "FillPortions": "0",
        "FontWeight": "FontWeight.Bold", "Height": "30", "Size": "16", "Text": '"ADD PLANNED HIRE"'}),
    node("lblPsHireHelp", LBL, {"AlignInContainer": "AlignInContainer.Stretch", "Color": "uiMuted", "FillPortions": "0",
        "Height": "40", "Size": "10", "Text": '"A placeholder for someone you plan to hire. After creating it, plan their years with the form and SAVE / SAVE ALL."'}),
    cap("lblPsHireNameCap", "NAME OR ROLE"),
    node("txtPsHireName", "TextInput@0.0.54", {"AccessibleLabel": '"Name or role"', "AlignInContainer": "AlignInContainer.Stretch",
        "FillPortions": "0", "Height": "36", "Placeholder": '"e.g. TBH - Senior Engineer"'}),
    cap("lblPsHireDeptCap", "DEPARTMENT (ADDRESS CODE)"),
    node("cmbPsHireDept", "ComboBox@0.0.51", {"AccessibleLabel": '"Department"', "AlignInContainer": "AlignInContainer.Stretch",
        "FillPortions": "0", "Height": "36", "Items": "Filter(Choices([@EmployeeTable].AddressCode), Value in psDepts.AddressCode)"}),
    cap("lblPsHireYearCap", "STARTS IN FISCAL YEAR"),
    node("cmbPsHireYear", "ComboBox@0.0.51", {"AccessibleLabel": '"Start year"', "AlignInContainer": "AlignInContainer.Stretch",
        "DefaultSelectedItems": "[Text(psFY)]", "FillPortions": "0", "Height": "36",
        "Items": "ForAll(psYears, Text(FY))"}),
    node("conPsHireButtons", GC, {"AlignInContainer": "AlignInContainer.Stretch", "DropShadow": "DropShadow.None",
        "FillPortions": "0", "Height": "56", "LayoutAlignItems": "LayoutAlignItems.End", "LayoutDirection": "LayoutDirection.Horizontal",
        "LayoutGap": "12", "LayoutJustifyContent": "LayoutJustifyContent.End", "LayoutMinHeight": "56"}, [
        btn("lblPsHireCancel", '"CANCEL"', "Set(psShowHire, false)"),
        btn("lblPsHireCreate", '"CREATE"', CREATE, primary=True, extra={"DisplayMode":
            "If(IsBlank(Trim(txtPsHireName.Value)) || IsBlank(cmbPsHireDept.Selected) || IsBlank(cmbPsHireYear.Selected), DisplayMode.Disabled, DisplayMode.Edit)"}),
    ], "AutoLayout"),
], "AutoLayout")
overlay = node("conPsHireOverlay", GC, {"DropShadow": "DropShadow.None", "Fill": "RGBA(0, 0, 0, 0.55)",
    "Height": "Parent.Height", "LayoutAlignItems": "LayoutAlignItems.Center", "LayoutDirection": "LayoutDirection.Vertical",
    "LayoutJustifyContent": "LayoutJustifyContent.Center", "Visible": "psShowHire", "Width": "Parent.Width",
    "X": "0", "Y": "0"}, [panel], "AutoLayout")
write("07e-part", [overlay], "PlanningScreen")

# ---------------- piece 8: overview matrix ----------------
NAME_W = 280
def cellx(n): return f"{NAME_W} + {n - 1} * ((Parent.TemplateWidth - {NAME_W}) / 5)"
CELLW = f"(Parent.TemplateWidth - {NAME_W}) / 5 - 6"
def cell(n):
    rec = f"LookUp(psAllStatus, Employee.Id = ThisItem.ID && Year(Date) = Index(psYears, {n}).FY)"
    text = ("With(\n    {r: " + rec + "},\n    If(\n        IsBlank(r), \"—\",\n"
            "        Substitute(r.RegionalGrade.Value, \"(MEA) \", \"\") &\n"
            "        If(r.Promotion, \"  P\", \"\") & If(r.Resignation, \"  R\", \"\") &\n"
            "        If(r.Mobility, \"  M\", \"\") & If(r.Succession, \"  S\", \"\")\n    )\n)")
    fill = ("With(\n    {r: " + rec + "},\n    If(\n        IsBlank(r), RGBA(0, 0, 0, 0.04),\n"
            "        DateDiff(r.'Last Updated', Today(), TimeUnit.Months) > psOutdatedMonths, RGBA(220, 70, 60, 0.16),\n"
            "        RGBA(90, 190, 110, 0.16)\n    )\n)")
    return node(f"lblPsOvC{n}", LBL, {"Align": "Align.Center", "Color": "uiInk", "Fill": fill, "FontWeight": "FontWeight.Semibold",
        "Height": "36", "OnSelect": f"Set(psOvPick, Index(psYears, {n}).FY);\nSelect(Parent)", "Size": "10", "Text": text,
        "Width": CELLW, "X": cellx(n), "Y": "4"})

OPEN_ROW = """Set(psSelected, LookUp(psEmployees, ID = ThisItem.ID));
Set(psLocked, psSelected.Kind = "Mobility" && psSelected.AddressCode <> "Outside");
Set(psConfirmRemove, false);
ClearCollect(psStatus, Filter(psAllStatus, Employee.Id = ThisItem.ID));
If(!IsBlank(psOvPick), Set(psFY, psOvPick));
Set(psRecord, LookUp(psStatus, Year(Date) = psFY));
Set(psPrev, LookUp(psStatus, Year(Date) = psFY - 1));
Set(psRegionalOverride, Blank());
Set(psConfirmResign, false);
Set(psShowOverview, false)"""
header_cells = [node(f"lblPsOvH{n}", LBL, {"Align": "Align.Center", "Color": "uiGold", "FillPortions": "1",
    "FontWeight": "FontWeight.Bold", "Height": "28", "Size": "10", "Text": f'"FY" & Index(psYears, {n}).FY'}) for n in range(1, 6)]
overview = node("conPsOverview", GC, {"DropShadow": "DropShadow.None", "Fill": "uiBg", "Height": "Parent.Height",
    "LayoutDirection": "LayoutDirection.Vertical", "LayoutGap": "10", "PaddingBottom": "20", "PaddingLeft": "28",
    "PaddingRight": "28", "PaddingTop": "20", "Visible": "psShowOverview", "Width": "Parent.Width", "X": "0", "Y": "0"}, [
    node("conPsOvTop", GC, {"AlignInContainer": "AlignInContainer.Stretch", "DropShadow": "DropShadow.None", "FillPortions": "0",
        "Height": "44", "LayoutAlignItems": "LayoutAlignItems.Center", "LayoutDirection": "LayoutDirection.Horizontal",
        "LayoutGap": "16", "LayoutMinHeight": "44"}, [
        node("lblPsOvTitle", LBL, {"Color": "uiGold", "FillPortions": "0", "FontWeight": "FontWeight.Bold", "Height": "40",
            "Size": "18", "Text": '"OVERVIEW"', "Width": "160"}),
        node("lblPsOvLegend", LBL, {"Color": "uiMuted", "FillPortions": "1", "Height": "40", "Size": "9", "Text":
            '"Regional grade per year  ·  P promotion  ·  R resignation  ·  M mobility  ·  S succession  ·  green up to date, red outdated, grey no data  ·  click a cell to open it"'}),
        btn("lblPsOvClose", '"CLOSE"', "Set(psShowOverview, false)"),
    ], "AutoLayout"),
    node("conPsOvHead", GC, {"AlignInContainer": "AlignInContainer.Stretch", "DropShadow": "DropShadow.None", "FillPortions": "0",
        "Height": "28", "LayoutDirection": "LayoutDirection.Horizontal", "LayoutGap": "6", "LayoutMinHeight": "28",
        "PaddingRight": "12"}, [
        node("lblPsOvHName", LBL, {"Color": "uiGold", "FillPortions": "0", "FontWeight": "FontWeight.Bold", "Height": "28",
            "Size": "10", "Text": '"EMPLOYEE"', "Width": str(NAME_W - 6)}),
    ] + header_cells, "AutoLayout"),
    node("galPsOverview", "Gallery@2.15.0", {"AlignInContainer": "AlignInContainer.Stretch", "BorderThickness": "0",
        "FillPortions": "1", "Items": 'Sort(psEmployees, Kind & "|" & FullName)', "OnSelect": OPEN_ROW,
        "TemplateFill": "If(ThisItem.ID = psSelected.ID, RGBA(212, 160, 23, 0.10), RGBA(0, 0, 0, 0))", "TemplateSize": "44"}, [
        node("lblPsOvName", LBL, {"Color": "uiInk", "FontWeight": "FontWeight.Semibold", "Height": "36",
            "OnSelect": "Set(psOvPick, Blank());\nSelect(Parent)", "Size": "11",
            "Text": 'ThisItem.FullName & If(ThisItem.Kind = "Planned", "  (planned)", If(ThisItem.Kind = "Mobility", "  (mobility)", ""))',
            "Width": str(NAME_W - 10), "X": "0", "Y": "4"}),
    ] + [cell(n) for n in range(1, 6)], "BrowseLayout_Vertical_ThreeTextVariant_ver5.0"),
], "AutoLayout")
write("08b-part", [overview], "PlanningScreen")
