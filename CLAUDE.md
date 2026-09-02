# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: AI Agents for Client Sale

### What this project is

I build small, single-purpose AI agents and sell them to clients (mostly US-based small businesses and solo operators). Each agent lives in its own folder under `/agents/<client-or-product-name>/`.

The goal is a working, sellable product — not a learning exercise, not a demo. Every agent must be something a client can run without me babysitting it.

### Who you're working with

- I have no coding background. I learn by building.
- Explain WHY before you write code, in plain English. Skip the jargon or define it.
- When you introduce a new concept (env var, API key, webhook, deployment), give me one sentence on what it is and why we need it here.
- Do NOT dump 300 lines of code with no explanation. Small steps, explain, then move.
- If I ask for something that's a bad idea, tell me straight. Don't just build it.

### Tech stack

You choose the language and tools for each agent. Pick whatever actually fits the job — a scheduled backend script and a client-facing web app shouldn't be built the same way.

Rules around that choice:

- Before writing code, tell me what you picked and why, in one short paragraph. I want to learn the reasoning, not just get the result.
- Stick to mainstream, well-documented options. If I get stuck at 2am, I need to be able to google the error and find an answer.
- Once an agent is started in a language, stay in it. Don't rewrite it halfway.
- Prefer direct API calls over heavy frameworks. I need to understand what's happening more than I need abstraction.
- Don't add a dependency without telling me what it does.

Constant regardless of language:

- **Secrets:** always in a `.env` file, never hardcoded.
- **Deployment:** pick the simplest option that works for that agent, and tell me the monthly cost before we commit to it.

### Hard rules

- Never commit API keys, `.env` files, or client data. Check `.gitignore` covers them.
- Every agent gets a `README.md` written for a non-technical client — what it does, how to run it, what it costs to run.
- Every agent gets an `example.env` showing which keys are needed (with fake values).
- Handle API errors. A client seeing a raw Python traceback is a refund request.
- Log token usage per run so I can price the agent correctly.
- Keep each agent under ~300 lines of core logic. If it's growing past that, we're solving too many problems in one product.

### Client context (US market)

- Clients are US-based. Pricing in USD. Timezones matter for anything scheduled — default to US Eastern unless told otherwise.
- Date formats in client-facing output: MM/DD/YYYY.
- Client-facing copy: plain American English, no Indian-English phrasing ("do the needful", "revert back", "kindly"). Flag it if I write any.
- Assume the client is non-technical. Setup instructions should assume zero terminal experience — screenshots-level detail in the README.

### How I want you to work

My working rules live in my global CLAUDE.md and are already loaded every
session — finishing one thing at a time, following the written order, how to
explain a bug, what to do after every test run, and asking before deleting
anything. They are not repeated here.

The only project-specific parts:

- The test results file for each agent goes at
  `agents/<agent-name>/what-the-tests-checked/latest.txt`, overwritten each run.
- Start with the smallest version that actually works. Ship, then improve.
- Before building, restate what you think I asked for in one line. Catch mismatches early.
- After each working feature, tell me how to test it myself.
- If something will cost money to run (API calls, hosting), tell me roughly how much.
