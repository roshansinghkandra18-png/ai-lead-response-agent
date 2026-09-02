# Building Agents

Small, single-purpose AI agents built to be sold to clients (US-based small businesses and solo operators).

## Layout

```
/agents/<client-or-product-name>/    one agent per folder
CLAUDE.md                            how Claude Code should work in this repo
.gitignore                           blocks secrets and client data from git
```

## Every agent folder contains

| File | Purpose |
|------|---------|
| `README.md` | Written for the non-technical client: what it does, how to run it, what it costs |
| `example.env` | The keys the agent needs, with fake values |
| `.env` | The real keys. **Never committed.** |

## Status

No agents built yet.
