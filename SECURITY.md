# Security

The reader listens only on `127.0.0.1`. It has no remote-management or web upload API. Content installation runs from the user's terminal. Do not expose this service with a port forward or public tunnel.

Pinned downloads must pass their expected SHA-256 and size before installation. Extractors select named files rather than trusting archive paths. Static files are confined to their configured roots. The runtime blocks remote subresources using a Content Security Policy, while explicitly opened publisher links can still leave the app.

For a security issue, use GitHub’s private vulnerability reporting if enabled. Otherwise contact the repository owner privately through their GitHub profile. Do not publish credentials or a working attack against another user's device in an issue.

Version 0.1.x is a community prototype. Only the latest released revision is maintained. Keep Ubuntu and the browser supported through the Switchroot project's documented update path.
