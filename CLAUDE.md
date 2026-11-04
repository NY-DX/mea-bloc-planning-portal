# MEA Bloc Personnel Planning Portal: working notes

Canvas app (Power Apps) on SharePoint lists: EmployeeTable, EmployeeStatusTable,
DepartmentTable, DepartmentStatusTable. `docs/SPEC.md` describes the old screens'
business rules and known problems. `Src/` is the readable source exported from the
.msapp (for review and diffs only; Studio does not load it, see below).

## How changes reach the app
- Studio "Paste code" (right-click a screen or container) accepts control YAML.
  **It processes only about 100 lines per paste**; anything after that is silently
  dropped, including the rest of a long formula. Keep each paste at or under 85 lines.
  `tools/pa_render.py` renders a control tree and `split_bfs` splits it into pastes,
  each naming the container to paste into (see `tools/piece4_form.py`).
- Long formulas go in by hand: select the control, choose the property, paste into
  the formula bar (no line limit there).
- Pasted controls are appended at the end of the target container.
- Importing a repacked .msapp works, but Studio loads `Controls/*.json`, not
  `Src/*.pa.yaml`; edits to Src alone are ignored.

## Rules learned the hard way
- Use only control types and properties the app already uses (check `Src/`).
  Known good: GroupContainer@1.5.0 (Variant AutoLayout), Label@2.5.1 (classic, has
  Color/Fill/Border*), ComboBox@0.0.51, Toggle@1.1.5, TextInput@0.0.54,
  Gallery@2.15.0 (Variant BrowseLayout_Vertical_ThreeTextVariant_ver5.0).
- `Tooltip` is not valid on Button@0.0.45. Pasting a classic button gets it upgraded
  to ModernButton and drops properties; buttons are styled Labels with OnSelect.
- In auto-layout containers, set `FillPortions: =0` on anything with a fixed
  Height/Width, otherwise it stretches.
- In Patch, write record literals inline. Building the change record in a variable or
  `With` and passing it to Patch was rejected ("invalid arguments").
- For Choice/Lookup columns, write the combo box's `.Selected` record (it comes from
  `Choices(...)`, so the type matches).

## New screen (PlanningScreen)
Built piece by piece from `rebuild/` (numbered files). Everything it creates is
prefixed `ps` (variables, collections) and it does not depend on the old screens.
Theme and shared tables are named formulas in App.Formulas (`ui*`, `gradeLadder`).
Repo: commit every piece; the old screens stay until PlanningScreen replaces them.
