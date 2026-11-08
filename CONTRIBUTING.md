# Contributing

Keep the app understandable and useful without a network connection.

- Make one focused change per pull request and explain the user-visible result.
- Test empty-library setup as well as a filled library.
- Check a 1280 × 720 viewport and large touch targets.
- Do not add analytics, remote fonts, CDN scripts or automatic content updates.
- Keep downloads explicit, resumable where possible and within the user's space budget.
- Preserve original publication text. New navigation labels must not quietly rewrite instructions.
- For a new guide, provide its official publisher URL, author, edition, scope, rights notes, original hash and verified section/page mapping. Do not commit the PDF.
- Do not call an identification reference a safe-foraging key unless it actually contains the needed identification and preparation material and its scope supports the claim.
- Never commit device identifiers, SSH keys, NAND files, credentials or private screenshots.

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/audit_release.py`. Browser checks are described in `docs/TESTING.md`.

By submitting code or original documentation, you agree to its inclusion under the project’s MIT licence. Third-party content must retain its original terms and attribution.
