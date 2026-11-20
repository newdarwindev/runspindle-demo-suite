# Fourteen workspace interaction gate

Every child keeps its own existing brand palette, typography and visual idiom. The parent renderer adds a domain-specific editorial introduction, numbered workspace navigation, responsive tables, local record filtering with an explicit empty state and count, keyboard skip navigation and live status announcements. Irrelevant cell labels and source-link controls are hidden. Filtering never modifies fixture records or sends network requests.

`tools/check-workspaces.cjs` uses the running controlled fixture server to sign in to each app's authorized synthetic account, independently check identity, read records, filter to no matches and restore them, read the source again, navigate within the workspace and check mobile overflow. It records all fourteen apps, captures 28 desktop/mobile screenshots and asserts no browser errors. Existing seven business workflows, sixteen fault expectations and independent-observer checks remain separate gates.

CI runs this after the fixture server starts. It publishes `workspaces/workspace-tour.mp4` and `workspaces/verification.json` in the source-SHA-named Actions artifact; successful main runs also attach them to the existing release. The JSON records exact source commit, working-tree cleanliness, runner name, Actions run ID, UTC timestamps, measured test duration and measured video duration. Read the actual job outcome before claiming CI completion. Local recordings are preflight evidence, not CI evidence.

No upstream Runspindle dependency, external service, real credentials, persistent service, or unsandboxed browser is introduced.
