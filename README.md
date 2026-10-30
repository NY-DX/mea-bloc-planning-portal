# MEA Bloc Personnel Planning Portal (QA) - canvas app source

Tracks the readable source (`Src/*.pa.yaml`) of the canvas app, extracted from the `.msapp`.

## Workflow
1. Export the app from Power Apps Studio (Back > Save as > download a copy) and unzip it.
2. Copy `Src/*.pa.yaml` over this folder's `Src/` and commit, so every change shows as a diff.
3. New or changed controls are applied in Studio with right-click > Paste code, using YAML
   copied from Studio's own code view (control type names must match what Studio shows).
4. Always test in a sandbox copy of the app; do not publish from experiments.

## Not tracked (see .gitignore)
`Controls/`, `Assets/`, `References/`, `Properties.json`, `_EditorState.pa.yaml`:
derived or environment-specific, and `DataSources.json` contains tenant URLs.
