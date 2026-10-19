# Local deployment and publication
Default examples bind the browser/API to localhost. Put remote access behind an
authenticated HTTPS gateway. Never publish .env, tokens, model caches, personal
recordings, private prompts or host-specific inventory. Run
`python scripts/check_public_secrets.py --history` before publication; its
bounded checks are not a guarantee that every credential or private datum is found.
Use your GitHub no-reply identity for commits. Models retain their own licenses.
Do not report credentials or private recordings in a public issue.
