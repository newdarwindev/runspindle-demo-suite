# Runspindle demo suite: permanent independence boundary

This repository is a standalone fictional demo product. Keep this boundary in all future changes, including its app and workflow child repositories.

- Never introduce a runtime, build, test, CI, installation, bootstrap or code-generation dependency on Runspindle or any upstream Runspindle component repository/package/service.
- Do not import, link, fetch, clone, execute or require upstream Runspindle code, binaries, SDKs, containers, APIs, credentials or model keys for this suite to work. Do not add upstream repositories as submodules, dependencies, prerequisites or test fixtures.
- The suite's own `runspindle-demo-*` app/workflow children are allowed and must remain independently runnable with synthetic fixtures. Their naming does not authorize dependencies on upstream Runspindle components.
- Documentation may reference or link upstream specifications, issues and source as explanatory material. Such references must remain optional reading, never executable inputs or required network fetches.
- Any actual upstream integration, integration adapter that requires upstream software, or cross-project acceptance testing belongs in a separate integration repository. Do not add it here, even behind an optional feature flag or test profile.
- Verify bootstrap, build, tests, recordings and presentation assembly can operate without any Runspindle checkout, service, secret or installed component. Report fixture evidence honestly; never imply fixture success proves upstream integration.
- If a proposed change conflicts with this boundary, stop that change and explain that it belongs in a separate integration project. Preserve this guidance rather than weakening it to make the change fit.

# Runner and publication safety

Use the approved existing disposable local CI lane. Do not create or enable persistent demo runner services, schedules or agents. Fleet enrollment, image provisioning and network/security changes require the owner's applicable setup/approval. Keep browser sandboxing enabled, do not expose credentials in evidence, and keep untrusted PR code off the trusted local lane.
