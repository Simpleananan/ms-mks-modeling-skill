# Privacy and local-data boundary

This public package is designed to preserve the modeling/retrieval behavior while excluding private research material and machine-specific configuration.

## Removed or generalized for public release

- private submission/manuscript identifiers and identifiable review-process benchmark cases;
- local knowledge-base folder names and direct local-document links;
- machine-specific paths, account identifiers, credentials, tokens, cookies, and private keys (none should be present in the release);
- any requirement that a particular private corpus exist.

Private benchmark examples were replaced with structure-preserving synthetic process cases so the `PROCESS_EVIDENCE` firewall and validation triggers remain testable without exposing the underlying submissions. Publicly published paper metadata/DOIs may remain because they are part of the literature evidence, not private user data.

## Runtime rules

- Local paper and review/response sources are optional and must be user-authorized.
- Source roots are read-only; the derived SQLite index must live outside them.
- Review-process materials remain `PROCESS_EVIDENCE` and never become formal truth merely because they come from an editor/reviewer/author response.
- Private local content, manuscript IDs, local paths, and nonpublic text must not be copied into web-search queries.
- Generated local indexes, caches, checkpoints, logs, `.env` files, and private corpora should remain untracked.
