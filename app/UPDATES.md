# Updates of CyTools_Storyboard

One stream: the application (this Tool has no engine and no model weights). Tab **Updates**,
code in `app/maintenance.py`.

No public repository exists for this Tool yet: enter one (`owner/name`) in the Updates tab.
A release must provide:

- `cytools-app.zip` — a zip whose top folder is `app/` (`tool.py`, `gui/main.py`,
  `storyboard/model.py`, `CyTool.json`, `release.json`...), no absolute paths, no `..`, no
  symbolic links, at most 256 MiB unpacked;
- `cytools-app.zip.sha256` — its SHA-256 (first word of the file).

`release.json` must carry the installed `runtime_abi` (`cp311-win_amd64`).

Flow: *Check* → *Download and verify* → staged in `runtime/updates/tool/<sha256>/` →
activated by `runtime/bootstrap.py` at the next start, under the runtime lock → previous
`app/` kept, *Restore the previous version* schedules it back. `data/` (your storyboards in
`data/projects`, settings, exports kept inside each project) is never part of an update.

Tested with fixtures only (no real GitHub release exists); see `app/tests/test_maintenance.py`.
