# xDAN JEV Plugin — research preview

Installable Python deployment plugin for **one frozen Qwen3.5-9B backbone**, five internal route depths, and a 1,048,576-parameter candidate head. Supports `mode=auto|jev|llm` and `effort=minimal|low|medium|high|max` (depth 3/6/10/13/16). Auto routing is computed inside the model runtime; no routing HTTP header is required.

**Research preview, not production quality:** the current candidate head scores **182/500**, versus **327/500** for the original LM candidate projection on the exposed JEV regression panel. These are not independent held-out results. The software works; this head has not passed the answer-quality gate. Natural-language candidate recovery and native vLLM integration remain incomplete. Do not equate an OpenAI-style API with vLLM engine support.

## Install from GitHub

```bash
git clone https://github.com/cryptoSUN2049/xDAN-JEV-Plugin.git
cd xDAN-JEV-Plugin
python3 -m venv .venv
source .venv/bin/activate
pip install .
xdan-jev --help
```

CLI/client: Python 3.10+. GPU serving: Linux CUDA; verified reference environment is Python 3.12.3, PyTorch 2.8.0+cu128, Transformers 5.16.1 and an RTX PRO 6000. Other GPUs and minimum VRAM have not been benchmarked. Plan for at least 48GB free disk for the HF cache plus assembled ~19GB model, and sufficient GPU memory for weights and input activations. CPU inference is not supported by the server command.

```bash
# On the CUDA server; torch wheels must match your CUDA/driver environment.
pip install '.[serve]'
xdan-jev prepare --output models/research-r1
xdan-jev verify --model-dir models/research-r1
xdan-jev serve --model-dir models/research-r1 --port 18183
```

`prepare` downloads the base from the **public official Qwen repository at immutable revision** `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. No private xDAN HF access or API key is required. The bundled ~5.3MB compressed overlay supplies the trained heads, config and exact research runtime. All 46 final assets are SHA256 checked before use. The 9B weights are not retrained or duplicated inside a serving process.

If the pinned base is already on disk:

```bash
xdan-jev prepare --output models/research-r1 --base-dir /path/to/pinned/base
```

Run one preparation process per output directory. Interrupted downloads use the HF cache; rerun the same command to resume staged verified files. Hash mismatches fail explicitly; inspect/remove only the named corrupt staged file before retrying. Existing complete output is verified without overwriting it. Disk copies are used, so the model remains independent of cache cleanup.

## Make a real request

Wait for the server log to print `"event": "ready"` (initial hash verification and model loading take time). Then, in a second terminal:

```bash
source .venv/bin/activate
xdan-jev chat --request examples/llm.json
xdan-jev chat --request examples/auto.json
xdan-jev chat --request examples/jev.json
```

Examples are newly authored, not benchmark records. `auto.json` and `jev.json` demonstrate the currently supported canonical prompt.v2 task format. The trained head may return an incorrect candidate; inspect the response's `xdan` execution metadata as well as its answer. Unsupported natural input in auto falls back to LLM; forced JEV rejects unsupported contracts.

```bash
curl http://127.0.0.1:18183/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary @examples/auto.json
```

Request fields: `messages`, optional `model`, `mode`, `effort`, `route_depth`, `max_tokens` (1–1024), `temperature=0`, `stream=false`. Effort and explicit depth must agree if both supplied. Default effort is max. Forced LLM bypasses routing and candidate recovery. `GET /health` and `GET /v1/models` are available. The API is a subset: no streaming, continuous batching, tool calls or multimodal inputs. Server serializes requests and has no authentication; default bind is loopback. For remote use keep it on loopback and use an SSH tunnel or an authenticated reverse proxy.

## Evidence and limitations

- Original complete bundle: 44 real GPU HTTP calls / 203 engineering checks passed, including depth mapping, head execution, prefix continuation and forced-LLM parity on a small sample.
- Exposed 500+500 regression: JEV route recall 495–497/500; LLM source sent to JEV 0/500. This is format-sensitive exposed regression, not proof of natural routing accuracy.
- The candidate head quality gate failed (182 vs 327 /500); 75 examples overlap head selection data. No claim of general SFT preservation: the earlier 500-LLM baseline had 311 truncated outputs.
- Native JEV candidate execution shares the backbone prefix. LLM fallback can recompute the prefix. No deployment-wide latency/speedup claim.
- No native vLLM integration. Use this Transformers research runtime to reproduce behavior.
- Plugin-specific GPU test: **15/15 requests passed**, covering three modes × five efforts through the installed CLI. Unit tests: **11 passed, 92.48% package coverage**.
- Plugin-specific installation/GPU evidence is recorded under `docs/plugin-github-release/`.

## Development

```bash
pip install '.[dev]'
ruff check .
ruff format --check .
pytest -q
python -m build
```

Apache-2.0. See LICENSE and NOTICE. Qwen base license is retained inside the model overlay. Model outputs and generated datasets are not distributed in this repository.
