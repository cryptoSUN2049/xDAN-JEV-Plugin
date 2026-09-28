# v0.1.0 research preview

Public installable Python/Transformers JEV deployment plugin. Includes verified router/candidate-head overlay, pinned official base download, full asset verification, localhost server and JSON CLI client.

Verified: anonymous GitHub clone and clean environment install; 13 public base assets accessible; 3 small assets anonymously downloaded/hash checked; complete 46-file GPU model assembly from existing verified base; 15 real GPU requests across 3 modes and 5 efforts. 11 unit/HTTP tests, 92.48% package coverage. Large weights were not cold-downloaded again.

Known quality failure: candidate head182/500 vs original LM327/500 on exposed regression. Research only. Native vLLM, natural-language candidate recovery, independent quality/SFT retention and production API features are not complete. Read README before GPU deployment.

Install from source with pip install .; use pip install '.[serve]' on a CUDA server. A wheel is attached. The archive inside the wheel contains the exact hash-bound runtime and small trained weights; the 9B base downloads separately from the pinned public official source.
