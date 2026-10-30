# MEA Bloc Personnel Planning Portal: functional specification (as built)

Source: Power Apps canvas app, unpacked YAML in `Src/`. This document describes what the current source does. It does not describe intended behaviour. Where the source is ambiguous, the text says so. It is the baseline for rebuilding `EmployeePlanningStatus` and later merging `PlanRecruitmentScreen` into it.

File abbreviations used in references (`file:line`):

| Abbrev | File |
|---|---|
| App | `App.pa.yaml` |
| HS | `HomeScreen.pa.yaml` |
| EPS | `EmployeePlanningStatus.pa.yaml` |
| PRS | `PlanRecruitmentScreen.pa.yaml` |

`EPS:1562` is the Save button's `OnSelect`. It is one quoted string on a single physical line, so rules inside it are cited as `EPS:1562 (step n)`, using the step order given in section 4.9.

Supplementary evidence: `AppCheckerResult.sarif` in the same package (referred to below as "app checker").

---

## 1. Purpose and users

**Purpose.** General Managers (GMs) propose, for each of their employees, the planned status for each of the next five fiscal years (1 April dates): grades, HR code, Biz/Corp, address code, HQ employment, promotion, resignation, mobility/transfer, succession, remark and final submission. A second screen records planned recruitment (headcount) per department and year. Header text: "Welcome to the MEA Bloc Personnel Planning Portal – your one-stop hub for managing and forecasting workforce changes" (HS:152).

**Navigation.** `HomeScreen` has two tiles:
- "Plan Employee Status " (`FeatureItemButton31`) navigates to `EmployeePlanningStatus` (HS:255, 265).
- "Plan Recruitment" (`FeatureItemButton41`) navigates to `PlanRecruitmentScreen` (HS:365, 375).

Each of the two screens has a "Main Menu" button that navigates back to `HomeScreen` (EPS:1571-1573 `btnCancel`; PRS:685-686 `btnCancel1`). `HomeScreen.OnVisible` rebuilds every employee and status collection each time the screen is shown (HS:13-113).

**Who sees what.**

| User / population | Rule | Ref |
|---|---|---|
| Current user | `varCurrentUserEmail = Lower(User().Email)` | App:12 |
| General Manager | The user is a GM of every `DepartmentTable` row where `Lower(GeneralManager.Email) = varCurrentUserEmail`. These rows go into `colManagerDepts`. | HS:17-23 |
| Direct employees | `EmployeeTable` rows whose `AddressCode.Value` equals the `AddressCode` of one of the GM's departments | HS:28-35 |
| Mobility (incoming) employees | Employees not in the direct set who have at least one `EmployeeStatusTable` row, in any year, whose `MobilityAC.Value` equals one of the GM's department address codes | HS:52-82 |
| Employee list shown | Direct employees followed by mobility employees (`colManagerEmployees`) | HS:99-100 |
| Non-GM user | `colManagerDepts` is empty, so the list is empty. There is no access gate, error message or admin view. `varIsGM` is computed but never used. | App:13-21 |
| Mobility employee, editability | Read-only when `varIsOnMobility && varSelectedEmployee.AddressCode.Value <> "Outside"` (section 4.4). An incoming mobility employee whose home address code is `"Outside"` is fully editable. | EPS:277 and every card's DisplayMode |
| Recruitment screen | Lists only the departments where the user is GM, using `User().Email` directly, not `varCurrentUserEmail` | PRS:32-36 |

The Office365Users connector is not referenced in any formula.

---

## 2. Fiscal-year model

| Item | Rule | Ref |
|---|---|---|
| `varFiscalYearBase` | `If(Month(Today()) >= 4, Year(Today()), Year(Today()) - 1)`. This is the calendar year in which the current fiscal year started (fiscal year starts 1 April). | App:24-27 |
| Record date convention | Every status and recruitment record carries `Date = Date(Y, 4, 1)`. Y is the planning year. | EPS:43, 190, 201, 1562 (step 4); PRS:676 |
| `colPlanningDates` | 5 rows, for `Value` = 0..4: `{DateValue: Date(varFiscalYearBase + Value + 1, 4, 1), DisplayYear: Text(varFiscalYearBase + Value + 1), IsSelected: Value = 0}` | App:29-39 |
| Selectable years | `varFiscalYearBase+1` to `varFiscalYearBase+5`. Example: on 2026-10-30 the base is 2026 and the selectable years are 2027-2031. | App:32-34 |
| Default year | The first entry, `varFiscalYearBase+1` | EPS:1580-1586; PRS:136-142 |
| Base (current) year | Not selectable. It is shown read-only in the "View <base> Data" modal (EPS:1811-1888). It also acts as the "previous year" that pre-fills the first planning year. | EPS:1821, 314 |
| Unused columns | `DisplayYear` and `IsSelected` of `colPlanningDates` are never read. Gallery `IsSelected` references are the gallery's built-in property, not this column. | — |

The year radio buttons' `Items` are `ForAll(colPlanningDates, Text(DateValue, "yyyy"))` (EPS:1591-1595). `Selected.Value` is therefore a **text** such as `"2027"`. The app converts it back to a number in two different ways:
- `Value(radPlanningDate.Selected.Value)`, e.g. EPS:43, 201, 314, 1599.
- `Year(radPlanningDate.Selected.Value)`, e.g. EPS:190, 998, 1636, 1650, 1747, and EPS:1562 in every date computation. PRS:177, 697 and 715 do the same.

Whether `Year("2027")` reliably returns 2027 is **unclear**: it depends on the implicit conversion of text to a date. `PRS:690-700` is a hidden debug label that prints both conversions, which suggests the developer was investigating this. The rebuild should use numeric years throughout.

---

## 3. Global variables and collections

### 3.1 App.OnStart (App:11-39)

| Name | Kind | Value | Used? |
|---|---|---|---|
| `varCurrentUserEmail` | global | `Lower(User().Email)` | Yes: HS, EPS:57 |
| `varIsGM` | global | true if the user is GM of at least one `DepartmentTable` row | **No.** Flagged by the app checker. |
| `varFiscalYearBase` | global | See section 2 | Yes |
| `colPlanningDates` | collection | See section 2 | Yes |

### 3.2 HomeScreen.OnVisible (HS:13-113). Runs on every visit to Home.

| Step | Name | Content | Ref |
|---|---|---|---|
| 1 | `colManagerDepts` | `DepartmentTable` rows where `Lower(GeneralManager.Email) = varCurrentUserEmail` (full records) | HS:17-23 |
| 2 | `colDirectEmployees` | For each department: `Filter(EmployeeTable, AddressCode.Value = dept.AddressCode)` | HS:28-35 |
| 3 | `colDirectStatus` | For each direct employee: `Filter(EmployeeStatusTable, Employee.Id = emp.ID)` (all years) | HS:40-47 |
| 4 | `colMobilityAssignments` | For each department: `Filter(EmployeeStatusTable, MobilityAC.Value = dept.AddressCode)` | HS:52-59 |
| 5 | `colMobilityEmployeeIds` | `Distinct(colMobilityAssignments, Employee.Id)`, excluding IDs already in `colDirectEmployees.ID` | HS:64-70 |
| 6 | `colMobilityEmployees` | For each ID: `LookUp(EmployeeTable, ID = mobId.Value)` | HS:75-82 |
| 7 | `colMobilityStatus` | For each mobility employee: all of their status rows (all years, every department) | HS:87-94 |
| 8 | `colManagerEmployees` | `colDirectEmployees` followed by `colMobilityEmployees`. This is the gallery source. | HS:99-100 |
| 8 | `colEmployeeStatus` | `colDirectStatus` followed by `colMobilityStatus`. This is the form source. | HS:102-103 |
| debug | `varDebugDirect`, `varDebugMobility`, `varDebugDirectStatus`, `varDebugMobilityStatus`, `varDebugTotalEmployees`, `varDebugTotalStatus` | `CountRows` of the collections above. Comment: "remove after testing". | HS:108-113 |

`DepartmentTable.AddressCode` is compared with `EmployeeTable.AddressCode.Value` and `EmployeeStatusTable.MobilityAC.Value`. It is therefore a plain text value in `DepartmentTable` (inferred).

### 3.3 EmployeePlanningStatus variables

| Name | Scope | Set where | Holds | Read where |
|---|---|---|---|---|
| `varSelectedEmployee` | global | OnVisible, only if blank: `First(galPlanningEmployees.AllItems)` (EPS:14-20). Gallery OnSelect: `ThisItem` (EPS:37). | Selected `EmployeeTable` record | Form DefaultMode, Save, Status dots, card lock condition, gallery highlight |
| `varTriggerRefresh` | global | Toggled in gallery OnSelect (EPS:38) | bool | Never read |
| `varCurrentYearRecord` | **context** (EPS:39-46) and **global** (Save, EPS:1562 step 7) | Gallery OnSelect: `LookUp(EmployeeStatusTable, Employee.Id = ThisItem.ID And Date = Date(Value(year),4,1))` | Status row for the selected year, fetched from the data source | Defaults of HQ, Promotion, Resignation, Mobility, Succession; HQ warnings. The global copy is flagged unused by the app checker. |
| `varPromotedGrade` | context | Blank on gallery select (EPS:45). Set by `tglPromotion` OnCheck/OnUncheck (EPS:809-841). | Regional grade one step up or down | `DataCardValue1` default |
| `varHQToggleChanged` / `varHQToggleState` | context | Gallery select: false / the record's HQ value or false (EPS:48-51). `tglHQ` OnCheck/OnUncheck: true / true or false (EPS:729-738). | Whether the user touched HQ, and its value | `warningHQTrue`, `warningHQFalse` |
| `varManagerDepts` | global | Gallery select: `Filter(DepartmentTable, Lower(GeneralManager.Email) = Lower(varCurrentUserEmail)).AddressCode` (EPS:54-59) | Single-column table of the GM's address codes | `varIsOnMobility` |
| `varIsOnMobility` | global | Gallery select (EPS:61-70); see section 4.4 | bool | Lock rule, Save DisplayMode |
| `varResignationYear` | global | `tglResignation` OnCheck: `Value(year)`. OnUncheck: Blank. (EPS:911-912) | number | `warningResigned` |
| `varMobilityYear` | global | `tglMobility` OnCheck: `Year(year text)`. OnUncheck: Blank. (EPS:998-999) | number | `warningMobility` |
| `varLastValidYear` | global | Radio OnChange (EPS:1599) | number | Never read (app checker) |
| `varRecordExists` | global | Radio OnChange (EPS:1601-1610) | bool | Never read (app checker) |
| `varHistoricalRecord` | global | `ButtonCanvas1` (EPS:1816-1823) | Base-year row | Never read. The modal form performs its own LookUp. |
| `varShowHistoricalModal` | global | `ButtonCanvas1` sets true (EPS:1824). `ButtonCanvas4` sets false (EPS:1862). | bool | `Container1.Visible` (EPS:1835) |
| `varExistingRecord` | global | Save step 1 | Row for the selected year, from `colEmployeeStatus` | Save |
| `varExpectedBizCorp`, `varHasDiscrepancy` | global | Save steps 2-3; also PRS Submit | Biz/Corp derived from HR code; mismatch flag | **Never read** (app checker flags `varHasDiscrepancy`) |
| `varIsEditingResignation` | global | Save, set false | — | Never read |
| `varResignationActive` | context | Save, set false | — | Never read |
| `varStoredRegionalGrade`, `varBaseRegionalGrade` | context | Save, both = `varCurrentYearRecord.RegionalGrade.Value` | text | Fallbacks for the `DataCardValue8` (Global Grade) default (EPS:391-395) |

### 3.4 PlanRecruitmentScreen variables

| Name | Set where | Holds |
|---|---|---|
| `varSelectedDepartment` | OnVisible: the first department where the user is GM (PRS:13-21). Gallery OnSelect: `ThisItem` (PRS:37). | `DepartmentTable` record |
| `varSelectedDeptID`, `varSelectedDeptCode` | Submit | `.ID` and `.AddressCode` of the selected department |
| `colYearsToSave` | Submit; cleared at the end | `{Year}` rows to insert |
| `varExpectedBizCorp`, `varHasDiscrepancy` | Submit | Unused (the Patch line is commented out) |

---

## 4. EmployeePlanningStatus (main screen)

### 4.1 Screen OnVisible (EPS:13-20)
If `varSelectedEmployee` is blank, it is set to `First(galPlanningEmployees.AllItems)`. The gallery's OnSelect logic does **not** run here, so `varCurrentYearRecord`, `varIsOnMobility` and the HQ context variables are not initialised until the user clicks an employee or changes the year.

### 4.2 Employee list

| Aspect | Rule | Ref |
|---|---|---|
| Control | `galPlanningEmployees` | EPS:30 |
| Items | `colManagerEmployees`, unfiltered and **unsorted**. Order is direct employees in department-then-list order, then mobility employees. | EPS:35 |
| Search box | `txtSearchPlanning`, placeholder "Search employee". **Not wired**: no formula references it. | EPS:22-29 |
| Row line 1 (`Title3`) | `'FirstName ' & " " & 'MiddleName ' & " " & 'LastName '`. Gives a double space when there is no middle name. | EPS:94-95 |
| Row line 2 (`Subtitle2`) | `ThisItem.AddressCode.Value` | EPS:113 |
| Row line 3 (`TextCanvas9`) | `ThisItem.'Employee ID'` | EPS:174 |
| `Body1` | Empty text | EPS:131 |
| Highlight | `TemplateFill` is light blue when `ThisItem.ID = varSelectedEmployee.ID` (EPS:71-76). `Rectangle3` is visible when `ThisItem.IsSelected`, i.e. the gallery's own selection (EPS:169). The two can disagree. | |
| Child controls | Every child's OnSelect is `Select(Parent)` | EPS:88, 107, 125, 144, 159, 168 |

**What selecting an employee does (gallery OnSelect, EPS:36-70), in order:**
1. `varSelectedEmployee = ThisItem`; `varTriggerRefresh` is toggled.
2. Context variable `varCurrentYearRecord` = the row in `EmployeeStatusTable` (data source, not the collection) where `Employee.Id = ThisItem.ID` and `Date = 1 April` of the selected year. `varPromotedGrade` is set to Blank.
3. `varHQToggleChanged = false`; `varHQToggleState` = the record's `HQEmployment`, or false when there is no record.
4. `varManagerDepts` = the GM's department address codes, re-queried from `DepartmentTable`.
5. `varIsOnMobility` is computed (section 4.4).

### 4.3 Year selector and status banner

| Control | Rule | Ref |
|---|---|---|
| `TextCanvas1` | Caption "Planning Date (Select one)" | EPS:1622 |
| `radPlanningDate` | Horizontal radio. Items are the 5 planning-year strings (section 2). Default is the first. Always editable. | EPS:1577-1596 |
| `radPlanningDate.OnChange` | Sets `varLastValidYear` (unused). Sets `varRecordExists` (unused) from a LookUp on the data source. Then `Select(galPlanningEmployees, galPlanningEmployees.Selected, Rectangle3)` to re-run the gallery OnSelect for the new year. | EPS:1597-1612 |
| `TextCanvas2` (record banner) | If there is no `EmployeeStatusTable` row for the selected gallery employee and `Date(Year(year), 4, 1)`, the text is "⚠️ No planning record exists for " & `'LastName '` & " - " & year, and the border colour is OrangeRed. Otherwise the text is "✅ Viewing existing record for " & `'LastName '` & " - " & year, and the border is Green. | EPS:1627-1655 |

### 4.4 Mobility detection and field locking

`varIsOnMobility` (EPS:61-70) is true when both of these hold:
- `ThisItem.AddressCode.Value` is **not** in `varManagerDepts`, i.e. the employee's home address code is not one of the GM's departments.
- At least one row in `EmployeeStatusTable` matches `Employee.Value = ThisItem.'LastName '` **and** `MobilityAC.Value in varManagerDepts`. The year is not considered.

The employee is matched by **last name text**, not by ID. Which `EmployeeTable` column the `Employee` lookup actually displays is not visible in the source, so whether this match ever succeeds is **unclear** (see P5).

**Lock rule** (identical on every editable card's DisplayMode, e.g. EPS:274-280): `If(varIsOnMobility && varSelectedEmployee.AddressCode.Value <> "Outside", DisplayMode.View, Parent.DisplayMode)`. The form itself has no DisplayMode override, so `Parent.DisplayMode` follows the form mode (New or Edit). Both are editable.

### 4.5 Form `frmPlanningForm` (EPS:177-1555)

- DataSource: `EmployeeStatusTable`.
- DefaultMode: `FormMode.New` if `colEmployeeStatus` has no row for `varSelectedEmployee.ID` and `Date(Year(year),4,1)`; otherwise `FormMode.Edit` (EPS:183-195).
- Item: the `colEmployeeStatus` row for `galPlanningEmployees.Selected.ID` and `Date(Value(year),4,1)` (EPS:197-202).

DefaultMode is keyed on `varSelectedEmployee`, while Item is keyed on `galPlanningEmployees.Selected`.

The form is never submitted with `SubmitForm`. Cards serve only as inputs, and Save writes with `Patch` (4.9).

**"Previous-year pre-fill"** below means a LookUp in the data source with `Employee.Id = galPlanningEmployees.Selected.ID And Date = Date(Value(year) - 1, 4, 1)`. For the first planning year, the previous year is the base (current) year.

| # | Label shown | Column | Card / input control | Default / prefill | Editable | Required / validation | Ref |
|---|---|---|---|---|---|---|---|
| 1 | (hidden) | Employee | `Employee_DataCard1` / `DataCardValue5` | `ThisItem.Employee` | Card `Visible=false` | none | EPS:207-264 |
| 2 | "Biz/Corp" | EmploymentType (DataField `"BizCorp"`) | `EmploymentType_DataCard1` / `drpEmpType` (not searchable) | Saved value if present, else previous-year `EmploymentType`, else blank | Lock rule | Save disabled if blank | EPS:267-328 |
| 3 | "Global Grade" | GlobalGrade | `GlobalGrade_DataCard3` / `DataCardValue8` | **Always derived; the saved value is never shown.** `Switch(Coalesce(DataCardValue1.Selected.Value, varBaseRegionalGrade, varStoredRegionalGrade), …)` using the table in 4.6. Fallback "GG5". | Lock rule; the user can override manually | No check. The card has no `Update`. | EPS:352-411 |
| 4 | Regional Grade (display name) | RegionalGrade | `RegionalGrade_DataCard1` / `DataCardValue1` | `varPromotedGrade` if set; else saved value; else previous-year `RegionalGrade`; else blank | Lock rule | Save disabled if blank | EPS:415-479 |
| 5 | "HR Code" | Division | `Division_DataCard1` / `DataCardValue7` | Saved value; else previous-year `Division`; else blank | Lock rule | Card `Required=true`; Save disabled if blank | EPS:503-559 |
| 6 | "Address Code" | AddressCode (lookup) | `AddressCode_DataCard1` / `drpAddressCode` | Saved value; else previous-year `AddressCode`; else blank. Items are `Choices(EmployeeStatusTable.AddressCode)`. | Card has the lock rule, but **`drpAddressCode` has no DisplayMode property**, so the combo itself is always editable | Save disabled if blank | EPS:583-668 |
| 7 | "HQ Employment" | HQEmployment | `HQEmployment_DataCard1` / `tglHQ` | `varCurrentYearRecord.HQEmployment` if a record exists; else previous-year `HQEmployment`; else false | Lock rule | — | EPS:669-738 |
| 8 | Promotion | Promotion | `Promotion_DataCard1` / `tglPromotion` | `varCurrentYearRecord.Promotion`, else false. **No previous-year pre-fill.** | Lock rule | — | EPS:762-841 |
| 9 | Resignation | Resignation | `Resignation_DataCard1` / `tglResignation` | `varCurrentYearRecord.Resignation`, else false | Lock rule | — | EPS:865-912 |
| 10 | "Mobility/Transfer" (with a trailing newline) | Mobility | `Mobility_DataCard1` / `tglMobility` | `varCurrentYearRecord.Mobility`; else previous-year `Mobility`; else false | Lock rule | — | EPS:936-999 |
| 11 | Succession | Succession | `Succession_DataCard1` / `tglSuccession` | `varCurrentYearRecord.Succession`, else false. **No previous-year pre-fill.** | Lock rule | — | EPS:1023-1068 |
| 12 | "Mobility Region" | MobilityRegion (choice) | `MobilityRegion_DataCard1` / `DataCardValue10` | Blank if `tglMobility` is off; else saved value; else previous-year `MobilityRegion`; else blank | Lock rule; card **visible only if `tglMobility.Checked`** | **Not required** even when Mobility is on | EPS:1092-1167 |
| 13 | "Mobility Address Code" | MobilityAC (lookup) | `MobilityAC_DataCard1` / `DataCardValue22` | Same pattern as Mobility Region | Lock rule; visible only if `tglMobility.Checked` | **Not required** | EPS:1191-1265 |
| 14 | (hidden) | Title | `Title_DataCard2` / `DataCardValue6` | `ThisItem.Title` | `Visible=false` | `Required=true`, but irrelevant (no SubmitForm) | EPS:1299-1356 |
| 15 | Remark | Remark | `Remark_DataCard1` / `txtRemarks` (single line) | Saved value | Lock rule | MaxLength from the data source | EPS:1359-1402 |
| 16 | Last Updated | LastUpdated | `Last Updated_DataCard1` / `DataCardValue13` (date picker, 1900-01-01 to Today+100y) | Saved value | Lock rule. **The user's edit is ignored**: Save writes `Now()`. | — | EPS:1426-1467 |
| 17 | "Final Submission" | FinalSubmission | `FinalSubmission_DataCard1` / `DataCardValue23` (toggle) | Saved value | Lock rule | — | EPS:1491-1533 |

`ROO_Confirmation` is not on the editable form. It appears only in the historical modal (4.8).

Default sources are mixed. Choice and lookup fields default from `ThisItem`, which comes from `colEmployeeStatus`. Toggles default from `varCurrentYearRecord`, which comes from the live data source.

### 4.6 Grade rules

**Regional to Global grade mapping.** Main form, `DataCardValue8` (EPS:389-408):

| Regional grade | Global grade |
|---|---|
| (MEA) E | N/A |
| (MEA) G1, G1+, G2, G2+ | GG5 |
| (MEA) G3, G3+ | GG4 |
| (MEA) G4M / G4P | GG3 |
| (MEA) M2/G5, M2+/G6 | GG2 |
| (MEA) M1/G7 | GG1 |
| anything else, including blank | GG5 |

The recruitment form (PRS:446-459) uses the same table **without the "(MEA) E" row**, so "(MEA) E" maps to GG5 there. Whether "N/A" is a valid `GlobalGrade` choice is unknown.

**Promotion toggle grade step.**

`tglPromotion` OnCheck (EPS:808-824) sets `varPromotedGrade` to the next grade up from the current `DataCardValue1` value and runs `Reset(DataCardValue1)`. The ladder is:

G1 → G1+ → G2 → G2+ → G3 → G3+ → G4M / G4P → M2/G5 → M2+/G6 → M1/G7

M1/G7 and any value not in the ladder (including "(MEA) E") stay unchanged.

OnUncheck (EPS:825-841) applies the exact reverse step.

Global grade then re-derives through the mapping above. The step applies only to the year being edited. A later year picks up the promoted grade only through the previous-year pre-fill, and only after this year is saved.

### 4.7 Status dots and legend

**`Status` (HtmlViewer, EPS:1760-1794).** One dot per row of `colPlanningDates`. For each year, `recordStatus = LookUp(EmployeeStatusTable, Employee.Id = varSelectedEmployee.ID && Year(Date) = Year(DateValue))`, using the first match in that calendar year.

| Condition | Dot |
|---|---|
| No record | ⚫ |
| `DateDiff(recordStatus.'Last Updated', Today(), Months) > 10` | 🔴 |
| Otherwise | 🟢 |

Each dot has the year (`yyyy`) below it.

**`StatusLegend`** is static HTML: "🟢 Up to date", "🔴 Outdated", "⚫ No data" (EPS:1798-1808).

**`warningOutdated`** is a label for the selected year. It is always visible and uses a **different threshold** from the dots (EPS:1676-1700):
- `'Last Updated_DataCard1'.Default` blank: "❌ No record exists".
- `DateDiff(LastUpdated, Today(), Months) > 8`: "⚠️ Outdated - Last updated N months ago".
- Otherwise: "✅ Up to date".

### 4.8 "View <base year> Data" modal

| Control | Rule | Ref |
|---|---|---|
| `ButtonCanvas1` | Text `"View " & varFiscalYearBase & " Data"`. OnSelect sets `varHistoricalRecord` (unused) and `varShowHistoricalModal = true`. | EPS:1811-1825 |
| `Container1` | Semi-transparent overlay, `Visible = varShowHistoricalModal` | EPS:1829-1835 |
| `TextCanvas4` | Title: `galPlanningEmployees.Selected.'LastName ' & " - " & varFiscalYearBase & " Data"` | EPS:1855 |
| `ButtonCanvas4` | "Close": sets `varShowHistoricalModal = false` | EPS:1859-1863 |
| `Form2` | Item: `LookUp(EmployeeStatusTable, Employee.Id = galPlanningEmployees.Selected.ID And Date = Date(varFiscalYearBase,4,1))`. DefaultMode: `If(IsBlank(...), FormMode.New)`, with no else branch. | EPS:1866-1888 |
| Cards (all `DisplayMode.View`) | Address Code (`DataCardValue4`), Division (`DataCardValue9`), Succession (`DataCardValue11`), ROO (`ROO_DataCard2`, DataField `ROO_Confirmation` but `Default = ThisItem.ROO`; whether `ROO` resolves is unclear), Resignation (`DataCardValue14`), Promotion (`DataCardValue16`), HQ Employment (`DataCardValue19`), Regional Grade (`DataCardValue15`), Global Grade (`DataCardValue20`), Biz/Corp (`DataCardValue21`), Mobility (`DataCardValue18`), Mobility Region (`DataCardValue17`) | EPS:1892-2591 |

The modal shows only the base year. Remark, LastUpdated, MobilityAC and FinalSubmission are not shown.

### 4.9 Warning labels (exact conditions and texts)

| Control | Visible when | Text (verbatim) | Ref |
|---|---|---|---|
| `warningResigned` | `!IsBlank(varResignationYear) && tglResignation.Checked`. Only after the user has checked the toggle at some point, since `varResignationYear` is global and is not reset when the employee changes. | "⚠️ Consecutive Years will be DELETED due to planned Resignation.⏎⚠️ Does this position require a replacement?⏎If yes, please use the ‘Recruitment’ page to add new staff." | EPS:1659-1672 |
| `warningPromotion` | `tglPromotion.Checked`, including when loaded from a saved record | "⚠️ Does this position require a successor?” if yes, please select the ‘’ Succession’’ and provide further information in ‘’ remark’’ section" | EPS:1704-1714 |
| `warningMobility` | `!IsBlank(varMobilityYear) && tglMobility.Checked`. Same global-variable caveat as `warningResigned`. | "⚠️ Does this position require a successor?” if yes, please select the ‘’ Succession’’ and provide further information in ‘’Remark’’ section." | EPS:1718-1728 |
| `warningHR` | A saved `EmployeeStatusTable` row exists for the selected employee and year, **and** `DataCardValue7` differs from that row's `Division.Value`, **and** `DataCardValue7` is not blank. It never shows for a new record whose HR code differs from the previous year. | "⚠️ Are you sure the HR code will be changed permanently, and has approval from both the current and new HR code owners been obtained?" | EPS:1732-1756 |
| `warningHQTrue` | `varHQToggleChanged` and `varHQToggleState = true` and baseline = false. Baseline is `Coalesce(varCurrentYearRecord.HQEmployment, previous-year HQEmployment, false)`. | "Are you sure the relevant staff is HQ employment staff?" | EPS:2594-2610 |
| `warningHQFalse` | `varHQToggleChanged` and `varHQToggleState = false` and baseline = true (same baseline) | "Please input the non-HQ staff in the remarks section and specify who will be the successor" | EPS:2614-2630 |
| `TextCanvas2` | Always visible | See 4.3 | EPS:1627-1655 |
| `warningOutdated` | Always visible | See 4.7 | EPS:1676-1700 |

The warnings are informational only. None of them blocks Save.

### 4.10 Save button `ButtonCanvas5` (EPS:1557-1563)

**Enabled rule (EPS:1560).** The button is disabled if any of these holds:
- `drpEmpType` (Biz/Corp) is blank.
- `DataCardValue1` (Regional Grade) is blank.
- `DataCardValue7` (HR Code) is blank.
- `drpAddressCode` is blank.
- `varIsOnMobility && varSelectedEmployee.AddressCode.Value <> "Outside"` (locked mobility employee).

Nothing else is validated. Global Grade, Mobility Region and Mobility AC are not required even when Mobility is on, and the Biz/Corp consistency check is not enforced.

**OnSelect (EPS:1562), in order:**

1. **Find the existing record.** `varExistingRecord = LookUp(colEmployeeStatus, Employee.Id = varSelectedEmployee.ID && Date = Date(Year(year),4,1))`. The local collection is used, not the data source.

2. **Biz/Corp expected from HR Code.** `varExpectedBizCorp = Switch(DataCardValue7.Selected.Value, …)`, using this full mapping table:

   | HR Code (Division) | Expected Biz/Corp |
   |---|---|
   | Iron & Steel Products | Business |
   | Mineral & Metal Resources | Business |
   | Energy I | Business |
   | Energy II | Business |
   | Energy Solution | Business |
   | Infrastructure Projects | Business |
   | Mobility I | Business |
   | Mobility II | Business |
   | Basic Materials | Business |
   | Performance Materials | Business |
   | Nutrition & Agriculture | Business |
   | Food | Business |
   | Retail | Business |
   | Wellness | Business |
   | IT & Communication | Business |
   | Corporate Development | Business |
   | DX | GCS |
   | CFO | GCS |
   | Legal | GCS |
   | Human Resources & General Affairs | Non-GCS |
   | Regional CSO | Non-GCS |
   | any other | "" (blank) |

3. **Discrepancy flag.** `varHasDiscrepancy = !IsBlank(expected) && !IsBlank(drpEmpType) && expected <> drpEmpType`. **This flag is never used.** It does not block Save, is not shown and is not stored. The same block is duplicated in PRS:676.

4. **Insert or update.**
   - If `varExistingRecord` is blank, the app runs `Patch(EmployeeStatusTable, Defaults(...), {...})`. The record contains:
     - `Employee`: SP lookup reference with `Id = varSelectedEmployee.ID` and `Value = 'FirstName ' & " " & 'LastName '`.
     - `Date = Date(Year(year),4,1)`.
     - `Title = GUID()`.
     - The common fields listed below, plus `'Last Updated' = Now()`.
   - Otherwise the app runs `Patch(EmployeeStatusTable, varExistingRecord, {...})` with `'Last Updated' = Now()` and the common fields.

   Common fields:
   - `GlobalGrade = {Value: DataCardValue8}`
   - `RegionalGrade = {Value: DataCardValue1}`
   - `Division = {Value: DataCardValue7}`
   - `HQEmployment = tglHQ`
   - `EmploymentType = {Value: drpEmpType}`
   - `Promotion = tglPromotion`
   - `Mobility = tglMobility`
   - `MobilityRegion = If(tglMobility, {Value: DataCardValue10}, {'@odata.type': SPListExpandedReference, Id: -1, Value: ""})`
   - `MobilityAC = If(tglMobility, {SPListExpandedReference, Id: DataCardValue22.Selected.Id, Value: DataCardValue22.Selected.Value}, {…Id: -1, Value: ""})`
   - `Resignation = tglResignation`
   - `Succession = tglSuccession`
   - `AddressCode = drpAddressCode.Selected`
   - `Remark = txtRemarks.Value`
   - `FinalSubmission = DataCardValue23`

   `ROO_Confirmation` is never written. There is no `IfError` or `Notify`: the user gets no success or failure message.

5. **Resignation cascade.** If `tglResignation.Checked`: `ForAll(Filter(EmployeeStatusTable, Employee.Id = varSelectedEmployee.ID && Date > Date(Year(year),4,1)), Remove(EmployeeStatusTable, ThisRecord))`. This deletes **every later-year record** of that employee, without confirmation, and runs even if step 4 failed. Unchecking Resignation later does not restore anything.

6. **Refresh.**
   - Rebuild `colDirectStatus` from `colDirectEmployees` and `colMobilityStatus` from `colMobilityEmployees`, one query per employee.
   - `colEmployeeStatus` = direct status followed by mobility status.
   - The employee lists, mobility detection, departments and debug counters are **not** refreshed.

7. **Reset state.**
   - `ResetForm(frmPlanningForm)`.
   - `Set(varCurrentYearRecord, LookUp(colEmployeeStatus, …))`. This is a global variable with the same name as the context variable, and nothing reads it (app checker).
   - `Set(varIsEditingResignation, false)`.
   - `UpdateContext({varStoredRegionalGrade, varBaseRegionalGrade})`, both set from the global `varCurrentYearRecord`.
   - `UpdateContext({varResignationActive: false})`.

8. **Reload.** `Select(galPlanningEmployees, galPlanningEmployees.Selected, Rectangle3)` re-runs the gallery OnSelect. This reloads `varCurrentYearRecord` (context), resets `varPromotedGrade` and the HQ flags, and recomputes `varIsOnMobility`.

### 4.11 Counters / debug label
`lblDebug` (EPS:2634-2644) is always visible at the bottom. Its text is:

`"Direct Emp: " & varDebugDirect & " | Mobility Emp: " & varDebugMobility & " | Total Emp: " & varDebugTotalEmployees & " | Direct Status: " & varDebugDirectStatus & " | Mobility Status: " & varDebugMobilityStatus & " | Total Status: " & varDebugTotalStatus`

The values are set only in `HomeScreen.OnVisible` (HS:108-113) and are not updated after Save. These are the only counters on the screen.

---

## 5. PlanRecruitmentScreen

**What it records.** Each Submit inserts one `DepartmentStatusTable` row per selected year with:
- `AddressCode`: lookup reference with `Id = varSelectedDepartment.ID` and `Value = varSelectedDepartment.AddressCode`. The lookup targets `DepartmentTable` (inferred from the Id).
- `Date = Date(Year,4,1)`
- `Recruitment = txtRecruitment.Value`
- `GlobalGrade = drpGradeP`
- `RegionalGrade = DataCardValue2`
- `HQEmployment = tglHQP`
- `Mobility = tglMobility.Checked` (see P20)
- `EmploymentType = drpEmpTypeP`
- `Division = drpDivisionP`
- `Title = GUID()`
- `'Last Updated' = Now()`

Ref: PRS:676 (Step 3).

| Element | Rule | Ref |
|---|---|---|
| Department list `galPlanningRecrutment` | `Filter(DepartmentTable, Lower(GeneralManager.Email) = Lower(User().Email))`. Shows `AddressCode`; other labels are empty. OnSelect sets `varSelectedDepartment = ThisItem`. | PRS:25-131 |
| OnVisible | `varSelectedDepartment` = the first of the GM's departments, on every visit | PRS:13-21 |
| Year radio `radPlanningDateP` | Same items and default as the main screen. No OnChange. | PRS:133-150 |
| `Form1` | DataSource `DepartmentStatusTable`. **DefaultMode always New**, so the Item LookUp (PRS:173-178) has no effect and existing rows cannot be edited. | PRS:165-178 |
| Recruitment (`txtRecruitment`) | NumberInput, Default 1, Min 1, card `Required=true` | PRS:183-217 |
| "HR Code" (`drpDivisionP`) | Division choices, default `ThisItem.Division` | PRS:241-274 |
| "Biz/Corp" (`drpEmpTypeP`) | EmploymentType choices | PRS:299-332 |
| Regional Grade (`DataCardValue2`) | RegionalGrade choices | PRS:357-390 |
| Global Grade (`drpGradeP`) | Derived from Regional Grade (table in 4.6, without "(MEA) E"). `DisplayMode.View`, not editable. | PRS:415-462 |
| HQ Employment (`tglHQP`) | Toggle | PRS:487-521 |
| Remark (`DataCardValue3`) | Text input. **Not saved**: not in the Patch. | PRS:545-581 |
| Mobility (`DataCardValue24`) | Toggle. **Not saved**: the Patch uses `tglMobility` from the other screen. | PRS:605-639 |
| Submit `btnSubmit` enabled | Disabled if HR Code, Regional Grade or Biz/Corp is blank. Recruitment is not checked. | PRS:666-674 |
| Submit OnSelect | Biz/Corp mapping and discrepancy flag (unused, duplicate of 4.10). Builds `colYearsToSave`, then patches one row per year. `Notify("Successfully created N record(s) for years: y1, y2…", Success, 4000)`. Resets `chkYear1`-`chkYear4`. Clears the collection. The form is not reset. There is no duplicate check, so every Submit inserts new rows. | PRS:676 |

**Multi-year checkboxes (PRS:880-913).** Let `Y = Value(radPlanningDateP.Selected.Value)` and `B = varFiscalYearBase`. `colYearsToSave` always contains `{Year: Y}`, plus checkbox *i*'s year if that checkbox is visible and checked.

| Checkbox | Year saved | Visible when | Label shown |
|---|---|---|---|
| `chkYear1` | B+2 | B+1 ≤ Y < B+2 | `Text(Year(Now()) + 1)` |
| `chkYear2` | B+3 | B+1 ≤ Y < B+3 | `Text(Year(Now()) + 2)` |
| `chkYear3` | B+4 | B+1 ≤ Y < B+4 | `Text(Year(Now()) + 3)` |
| `chkYear4` | B+5 | B+1 ≤ Y < B+5 | `Text(Year(Now()) + 4)` |

Net effect: only years after the selected year are offered, and none are offered when Y = B+5. From April to December, `Year(Now()) = B`, so every label is one year lower than the year actually saved (see P18).

**Recruitment list `galRecruitmentList` (PRS:704-829).**
- Items: `Filter(DepartmentStatusTable, AddressCode.Id = varSelectedDepartment.ID && Year(Date) = Year(radPlanningDateP.Selected.Value))`.
- Each row shows Division, AddressCode, "Recruitment:" plus count, "Last Updated:" plus timestamp, EmploymentType and GlobalGrade.
- Row OnSelect is commented out, so rows cannot be edited.
- The trash icon `Icon1` runs `Remove(DepartmentStatusTable, ThisItem)` immediately, with no confirmation.
- Heading labels: "Existing Records" (`TextCanvas1_2`) and "Department" (`TextCanvas1_3`).

**Dead UI.** `Label1` (all formula text commented out, PRS:832-843). `ButtonCanvas3` "Clear" (`Visible=false`, PRS:847-856). `TextCanvas3` debug label (`Visible=false`, PRS:690-700).

---

## 6. Observed problems and risks

| # | Problem | Ref | Status |
|---|---|---|---|
| P1 | Biz/Corp vs HR Code check is computed (`varHasDiscrepancy`) but never used. There is no warning and no block. Duplicated in two screens. | EPS:1562 (steps 2-3); PRS:676 | certain |
| P2 | Two different "outdated" thresholds: the dots use > 10 months, the label uses > 8 months | EPS:1783 vs EPS:1691 | certain |
| P3 | Resignation deletes all later-year records on Save, with no confirmation, no undo and no error check. It runs even if the Patch failed. `ForAll(...Remove...)` row by row (app checker `ForAllWithMutation`) instead of `RemoveIf`. | EPS:1562 (step 5) | certain |
| P4 | `MobilityRegion` is a **Choice** column but is cleared with a lookup-style `{'@odata.type': SPListExpandedReference, Id: -1, Value: ""}`. Whether SharePoint accepts this, ignores it or errors is unclear. `MobilityAC` (a lookup) is cleared the same way with `Id: -1`, which is an undocumented hack. | EPS:1108-1117, 1207-1216, 1562 (step 4) | suspected |
| P5 | Mobility detection matches `Employee.Value = ThisItem.'LastName '`, i.e. by name rather than ID. This breaks on duplicate last names. It may never match, depending on the lookup's display column; Insert writes "First Last" as Value, but SharePoint ignores Value on write. If it never matches, mobility employees are editable. | EPS:66 | suspected |
| P6 | Form state is keyed on two different "selected employee" sources: `varSelectedEmployee` (DefaultMode, Save, dots, lock) and `galPlanningEmployees.Selected` (Item, defaults, warnings, banner). OnVisible keeps the old `varSelectedEmployee` while the gallery's Selected can differ, so the app could display one employee and save to another. | EPS:14-20, 189 vs 200 | suspected |
| P7 | OnVisible does not run the gallery OnSelect logic, so `varIsOnMobility`, `varCurrentYearRecord` and the HQ flags are stale or blank on first entry. Locking and toggle defaults can be wrong until the user clicks. | EPS:13-20 | certain |
| P8 | `varCurrentYearRecord` is both a context variable (UpdateContext) and a global (Set in Save). The global is never read (app checker: unused). Save's "refresh current year record" step does nothing. | EPS:39-46, 1562 (step 7) | certain |
| P9 | Mixed data sources for the same record. The form Item and DefaultMode use `colEmployeeStatus`. Toggle defaults, the banner, warnings, dots, prefills and the modal query `EmployeeStatusTable` live. They can disagree; for example, a record created elsewhere is not in the collection, so Save inserts a duplicate. | EPS:183-202 vs 40-44, 1632-1650 | suspected |
| P10 | No duplicate protection on Insert. Uniqueness of (Employee, Date) relies on the local collection lookup only. | EPS:1562 (steps 1, 4) | certain |
| P11 | `Year(<text>)` is applied to the radio's text value in many places, while `Value(<text>)` is used elsewhere. The result of `Year("2027")` is unclear. | EPS:190, 998, 1562; PRS:177, 697, 715 | suspected |
| P12 | `Select(galPlanningEmployees, galPlanningEmployees.Selected, Rectangle3)` passes a record where `Select` expects a row number. The `Select()` chains (radio, then gallery, then Rectangle3, then `Select(Parent)`) are fragile and run after the current formula completes. | EPS:1562 (step 8), 1612, 168 | suspected |
| P13 | Global Grade never shows the saved value. It is always recomputed from Regional Grade, so a manually saved GG is overwritten on the next open/save unless the user re-edits it. The "(MEA) E" → "N/A" mapping is not present in the recruitment screen. | EPS:388-408; PRS:446-459 | certain |
| P14 | Last Updated date picker is editable, but its value is ignored; Save always writes `Now()`. | EPS:1442, 1562 (step 4) | certain |
| P15 | `drpAddressCode` has no DisplayMode, so it stays editable for locked mobility employees. Save is disabled for them, so the impact is cosmetic. | EPS:635-655 | certain |
| P16 | `warningResigned` and `warningMobility` depend on global variables that are never reset on employee or year change. Warnings can carry over to other employees, and do not show for records loaded with the flag already true. Whether OnCheck/OnUncheck also fire when Default changes is unclear. | EPS:911-912, 998-999, 1672, 1728 | suspected |
| P17 | Promotion step-up/down operates on whatever grade is displayed. Unchecking a saved Promotion steps the saved (already promoted) grade down. Toggling repeatedly accumulates steps if the user re-checks after the grade has been reset. "(MEA) E" is not in the ladder. | EPS:808-841 | suspected |
| P18 | Recruitment checkbox labels use `Year(Now())+i`, but the saved years are `varFiscalYearBase+1+i`. From April to December the labels are off by one year; for example, the box labelled 2027 saves 2028. | PRS:883, 892, 901, 910 vs 676 | certain |
| P19 | Recruitment Remark input is never saved | PRS:556, 676 | certain |
| P20 | Recruitment Mobility saves `tglMobility.Checked` from the **EmployeePlanningStatus** screen (app checker: `CrossScreenEventDependencies`). The screen's own toggle `DataCardValue24` is ignored. | PRS:676 | certain |
| P21 | Recruitment Submit always inserts. There is no duplicate check or edit path; Item is ignored because DefaultMode is New. Success Notify is shown even if a Patch failed. | PRS:171, 676 | certain |
| P22 | Trash icon deletes a recruitment row immediately, with no confirmation and no error handling | PRS:829 | certain |
| P23 | Search box `txtSearchPlanning` does nothing. The list has no sorting. | EPS:22-35 | certain |
| P24 | Non-delegable or expensive queries (app checker `SuggestRemoteExecutionHint` / `OpNotSupportedByColumn`): <br>• `Lower(GeneralManager.Email) = …` on `DepartmentTable` (App:18, HS:21, EPS:57, PRS:18, 35) <br>• `Year(Date) = …` (EPS:1774, PRS:715) <br>• `in varManagerDepts` (EPS:67) <br>• Many per-control LookUps on `EmployeeStatusTable`: at least 8 previous-year lookups in DefaultSelectedItems/Default, plus the banner, `warningHR` (2), HQ warnings and the Status HTML (5 lookups). <br>• Per-employee `ForAll(Collect(Filter))` loops (N+1 queries) on Home and after every Save. <br>Silent truncation is possible above the delegation limit. | as listed | certain (warnings) / suspected (impact) |
| P25 | Unused variables: `varIsGM`, `varTriggerRefresh`, `varLastValidYear`, `varRecordExists`, `varHistoricalRecord`, `varIsEditingResignation`, `varResignationActive`, `varHasDiscrepancy`, global `varCurrentYearRecord`. `colPlanningDates.DisplayYear` and `IsSelected` are also unused. | App checker; see 3.x | certain |
| P26 | Non-GM users get an empty screen with no explanation. `varIsGM` is computed but unused. | App:13-21 | certain |
| P27 | Debug/test artifacts in production: `lblDebug` (visible), the `varDebug*` counters, `DescriptionText41_Test` "Propose future Recruitment for your team (TEST)" visible on Home, hidden `TextCanvas3`, empty `Body1`/`Subtitle3`/`Body2` labels, `Screen1` sample screen | EPS:2634; HS:108-113, 396-411; PRS:690-700 | certain |
| P28 | The Save refresh does not rebuild the employee lists or mobility assignments. A newly set MobilityAC pointing to a GM's department appears only after returning to Home. Debug counters go stale. | EPS:1562 (step 6) | certain |
| P29 | The status dot looks up any record in that calendar year (`Year(Date) = Year(DateValue)`), not exactly 1 April. It is also keyed on `varSelectedEmployee`, not the gallery selection. | EPS:1771-1775 | certain |
| P30 | `warningHR` compares only with a saved record of the same year. It never fires for a new year whose pre-filled HR code is changed. | EPS:1742-1756 | certain |
| P31 | When Mobility is on, Mobility Region and Mobility AC are not required. A blank `DataCardValue22.Selected.Id` is patched into the lookup. | EPS:1166, 1264, 1560 | certain |
| P32 | Inconsistent defaulting: Promotion and Succession do not inherit from the previous year, while HQ, Mobility, grades, HR code, Biz/Corp and Address Code do. Whether this is intentional is unclear. | EPS:768-773, 1029-1034 | certain (behaviour) / unclear (intent) |
| P33 | Historical modal: `Form2.DefaultMode` has no else branch; `ROO_DataCard2` uses `ThisItem.ROO`, while the DataField is `ROO_Confirmation` (unclear if this resolves). `ROO_Confirmation` is never editable or written anywhere. | EPS:1872-1882, 2073-2076 | suspected |
| P34 | The gallery name `Title3` uses `'MiddleName '` unconditionally, which gives a double space when there is no middle name. Lookup `Value` written on insert is "First Last" (no middle name). | EPS:95, 1562 (step 4) | certain (cosmetic) |
| P35 | Gallery OnSelect re-queries `DepartmentTable` to build `varManagerDepts` on every click, even though `colManagerDepts` already holds the same data | EPS:54-59 vs HS:17-23 | certain |
