# Public JEV plugin handoff

## TL;DR
- Public GitHub: https://github.com/cryptoSUN2049/xDAN-JEV-Plugin, default main.
- Worktree plugin-github-release; isolated from private model monorepo history.
- prepare/verify/serve/chat implemented; real GPU 15 requests passed.
- Research preview only: candidate answer quality fails; native vLLM unsupported.

## Deliverables
- `src/xdan_jev_plugin/bundle.py`: pinned-manifest model assembly and verification.
- `src/xdan_jev_plugin/cli.py`: public CLI, local server startup, JSON HTTP client.
- `src/xdan_jev_plugin/assets/research-r1.tgz`: 34 overlay files, ~5.3MB compressed; no base weights or private data.
- `README.md`, `LICENSE`, `NOTICE`, `examples/{auto,jev,llm}.json`: installation, limits, attribution, newly authored examples.
- `tests/test_bundle.py`, `tests/test_cli.py`: 11 tests, 92.48% package statement coverage.
- `scripts/smoke_gpu.py`: real installed CLI, 3 modes × 5 efforts.
- `docs/plugin-github-release/{design.md,public-base-access.json,public-hf-download.json,gpu-smoke.json}`: design and evidence.
- `.github/workflows/test.yml`: lint, format, coverage >=80%, build.

## Constraints
- Keep the fixed release-manifest SHA and exact vendored source hashes; do not reformat archived model source independently.
- Never claim native vLLM support or candidate quality approval.
- Public package includes no original datasets, credentials or private repository history.
- CLI serving binds loopback by default; no authentication or batching provided.

## Observed behavior
- Actual GPU reference Python 3.12.3, torch2.8.0+cu128, transformers5.16.1, safetensors0.8.0.
- Initial verification/loading takes roughly a minute on reference storage; await ready before chat. One early connection-refused attempt was retried after ready, without restarting the server.
- All 13 official base files anonymously accessible. Three small base assets anonymously downloaded and byte-hash checked. GPU assembly reused existing exact verified base; no fresh 19GB internet download claimed.
- Existing staged valid files resume; corrupt staged file fails explicitly. One prepare process per output directory.
- `gh repo create --source .` failed to recognize worktree; created repository explicitly, configured clean HTTPS remote and pushed explicit HEAD:main.
- Candidate head182/500 vs original LM327/500; exposed regression, 75 selection overlaps. Forced LLM route protection is engineering evidence, not broad SFT retention.

## Next milestone
- [ ] Natural candidate recovery and independently evaluated routing/answer quality.
- [ ] Improve or replace regressed candidate head without modifying frozen base SFT weights.
- [ ] Native vLLM implementation and benchmark, separately approved evidence.
- [ ] Broader GPU/platform/latency/memory matrix.

## Branch/deployment
- Source worktree branch plugin-github-release; public deployment branch main.
- Real research server launched through installed xdan-jev CLI; original services unchanged.
- Full lint gates must pass before every push. Release is prerelease, not production stable.

## Cold start
1. Read README and this handoff; inspect tasks/todo.md and public evidence.
2. git status/diff/stash/worktree check before editing.
3. Install .[dev], run ruff check/format and pytest coverage.
4. Use smoke_gpu.py only against a ready GPU service; do not assume CI provides GPU tests.
5. Preserve model/manifest identity or explicitly produce a separately versioned bundle.
