import sys
sys.path.insert(0, sys.argv[1])
from pa_render import node, render
out = sys.argv[2]
LBL = "Label@2.5.1"
VAR = "BrowseLayout_Vertical_ThreeTextVariant_ver5.0"
NAME_W = 280
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
REC = "LookUp(psAllStatus, Employee.Id = ThisItem.EmpId && Year(Date) = ThisItem.FY)"
cell = node("lblPsOvCell", LBL, {
    "Align": "Align.Center", "Color": "uiInk", "FontWeight": "FontWeight.Semibold", "Height": "Parent.TemplateHeight",
    "OnSelect": "Select(Parent)", "Size": "10", "Width": "Parent.TemplateWidth", "X": "0", "Y": "0",
    "Fill": "With(\n    {r: " + REC + "},\n    If(\n        IsBlank(r), RGBA(0, 0, 0, 0.04),\n"
            "        DateDiff(r.'Last Updated', Today(), TimeUnit.Months) > psOutdatedMonths, RGBA(220, 70, 60, 0.16),\n"
            "        RGBA(90, 190, 110, 0.16)\n    )\n)",
    "Text": "With(\n    {r: " + REC + "},\n    If(\n        IsBlank(r), \"—\",\n"
            "        Substitute(r.RegionalGrade.Value, \"(MEA) \", \"\") &\n"
            "        If(r.Promotion, \"  P\", \"\") & If(r.Resignation, \"  R\", \"\") &\n"
            "        If(r.Mobility, \"  M\", \"\") & If(r.Succession, \"  S\", \"\")\n    )\n)"})
cells = node("galPsOvCells", "Gallery@2.15.0", {
    "BorderThickness": "0", "Height": "Parent.TemplateHeight", "Items": "ForAll(psYears As y, {FY: y.FY, EmpId: ThisItem.ID})",
    "OnSelect": "Set(psOvPick, ThisItem.FY);\nSelect(Parent)", "TemplatePadding": "3", "TemplateSize": "Parent.TemplateHeight - 6",
    "Width": f"Parent.TemplateWidth - {NAME_W}", "WrapCount": "5", "X": str(NAME_W), "Y": "0"}, [cell], VAR)
name = node("lblPsOvName", LBL, {"Color": "uiInk", "FontWeight": "FontWeight.Semibold", "Height": "Parent.TemplateHeight",
    "OnSelect": "Set(psOvPick, Blank());\nSelect(Parent)", "Size": "11",
    "Text": 'ThisItem.FullName & Switch(ThisItem.Kind, "Planned", "  (planned)", "Mobility", "  (mobility)", "")',
    "Width": str(NAME_W - 10), "X": "0", "Y": "0"})
gal = node("galPsOverview", "Gallery@2.15.0", {"AlignInContainer": "AlignInContainer.Stretch", "BorderThickness": "0",
    "FillPortions": "1", "Items": 'Sort(psEmployees, Kind & "|" & FullName)', "OnSelect": OPEN_ROW,
    "TemplateFill": "If(ThisItem.ID = psSelected.ID, RGBA(212, 160, 23, 0.10), RGBA(0, 0, 0, 0))", "TemplateSize": "46"},
    [name, cells], VAR)
lines = render(gal)
open(f"{out}/08c-into-conPsOverview.paste.yaml", "w").write("\n".join(lines) + "\n")
print(len(lines), "lines")
