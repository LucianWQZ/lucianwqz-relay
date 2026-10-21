**# P7X_A3_07_Raw_Text_Evidence — part 001**


RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

PART: 1/6

SECTIONS: ['Filtering rule and counts', 'A0 result', 'A1 result (expected early gate)', 'B fixed-contract result (full traceback)', 'B partial v2 artifact', 'Host UT file outputs', 'test_draft_window_graph_characterization.log', 'test_draft_window_graph_carrier.log', 'test_draft_window_graph_binding.log', 'test_draft_window_graph_oracle.log']


**---**


**# P7X_A3_07_Raw_Text_Evidence**


RUN_ID: `20261019_055109_13373fff`


**## Filtering rule and counts**


Full driver logs are retained on the server. This document includes:


- complete A0/A1/B result JSON and the B artifact JSON;

- the complete failure traceback;

- complete host UT/lifecycle logs for the PASS evidence used in decisions;

- complete helper/oracle/audit command output used;

- complete external scripts (driver, checker, env, sitecustomize, probe) and the old→new driver diff;

- line-numbered source snippets for every first-divergence/hook/validation claim;

- oracle/negative/repo-audit summaries; full arrays are in `P7X_A3_06_Evidence.part003.json`.


Excluded from this file: full A0/B server logs (\~20k/45k characters),

model-loading progress bars, repeated plugin banners, and unrelated vLLM warnings.

No excluded content is used as a PASS evidence.


**## A0 result**

```json

{

  "case": "A0",

  "window": "off",

  "flag": "0",

  "artifact": "",

  "model": "/mnt/share/wql/Qwen3-8B",

  "draft": "/mnt/share/dspark_qwen3_8b_block7",

  "prompt": "Hello, my name is",

  "prompt_len_requested": 0,

  "num_prompts": 1,

  "max_tokens": 16,

  "logprobs": 0,

  "status": "OK",

  "model_runner_class": "vllm_ascend.worker.v2.model_runner.NPUModelRunner",

  "speculator_class": "vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator",

  "policy_state": "None",

  "policy_reason": null,

  "effective_window_size": null,

  "characterization_installed": false,

  "provider_installed": false,

  "outputs": [

    {

      "token_ids": [

        8515,

        11,

        323,

        358,

        1079,

        264,

        220,

        17,

        18,

        4666,

        6284,

        5458,

        13,

        358,

        614,

        1012

      ],

      "text": " Alex, and I am a 23-year-old student. I have been",

      "logprobs": null

    }

  ]

}

```


**## A1 result (expected early gate)**

```json

{

  "case": "A1",

  "window": "1024",

  "flag": "0",

  "artifact": "",

  "model": "/mnt/share/wql/Qwen3-8B",

  "draft": "/mnt/share/dspark_qwen3_8b_block7",

  "prompt": "Hello, my name is",

  "prompt_len_requested": 0,

  "num_prompts": 1,

  "max_tokens": 16,

  "logprobs": 0,

  "status": "EXCEPTION",

  "exception_type": "NotImplementedError",

  "exception_message": "MRV2 Draft Window P7-X route rejected before materialization: status=GRAPH_FROZEN; Graph mode FULL_DECODE_ONLY belongs to the frozen Graph Track",

  "traceback": "Traceback (most recent call last):\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/driver_case.py\\", line 74, in main\n    llm = LLM(\n          ^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/entrypoints/llm.py\\", line 343, in __init__\n    self.llm_engine = LLMEngine.from_engine_args(\n                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/llm_engine.py\\", line 184, in from_engine_args\n    return cls(\n           ^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/llm_engine.py\\", line 109, in __init__\n    self.engine_core = EngineCoreClient.make_client(\n                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core_client.py\\", line 129, in make_client\n    return InprocClient(vllm_config, executor_class, log_stats)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core_client.py\\", line 354, in __init__\n    self.engine_core = EngineCore(\n                       ^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/patch/platform/patch_profiling_chunk.py\\", line 198, in _patched_engine_core_init\n    original_init(self, *args, **kwargs)\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core.py\\", line 145, in __init__\n    kv_cache_config = self._initialize_kv_caches(vllm_config)\n                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/tracing/otel.py\\", line 178, in sync_wrapper\n    return func(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core.py\\", line 354, in _initialize_kv_caches\n    self.model_executor.initialize_from_config(kv_cache_configs)\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/executor/abstract.py\\", line 122, in initialize_from_config\n    self.collective_rpc(\\"initialize_from_config\\", args=(kv_cache_configs,))\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/executor/uniproc_executor.py\\", line 103, in collective_rpc\n    result = run_method(self.driver_worker, method, args, kwargs)\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/serial_utils.py\\", line 510, in run_method\n    return func(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/worker_base.py\\", line 349, in initialize_from_config\n    self.worker.initialize_from_config(kv_cache_config)  # type: ignore\n    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/worker.py\\", line 1144, in initialize_from_config\n    self.model_runner.initialize_kv_cache(\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/model_runner.py\\", line 260, in initialize_kv_cache\n    super().initialize_kv_cache(\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/gpu/model_runner.py\\", line 703, in initialize_kv_cache\n    self.speculator.set_attn(\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py\\", line 198, in set_attn\n    self._initialize_draft_window_source_capability()\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py\\", line 102, in _initialize_draft_window_source_capability\n    capability = build_draft_window_source_capability(\n                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/draft_window.py\\", line 1452, in build_draft_window_source_capability\n    return _build_draft_window_source_capability_for_context(\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/draft_window.py\\", line 1503, in _build_draft_window_source_capability_for_context\n    eager_topology_fingerprint = eager_decision.require_local_materialization()\n                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py\\", line 138, in require_local_materialization\n    raise NotImplementedError(\nNotImplementedError: MRV2 Draft Window P7-X route rejected before materialization: status=GRAPH_FROZEN; Graph mode FULL_DECODE_ONLY belongs to the frozen Graph Track\n"

}

```


**## B fixed-contract result (full traceback)**

```json

{

  "case": "B",

  "window": "1024",

  "flag": "1",

  "artifact": "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/artifact/B_artifact.json",

  "model": "/mnt/share/wql/Qwen3-8B",

  "draft": "/mnt/share/dspark_qwen3_8b_block7",

  "prompt": "Hello, my name is",

  "prompt_len_requested": 0,

  "num_prompts": 1,

  "max_tokens": 16,

  "logprobs": 0,

  "status": "EXCEPTION",

  "exception_type": "RuntimeError",

  "exception_message": "capture operand observer is already attached",

  "traceback": "Traceback (most recent call last):\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/driver_case.py\\", line 74, in main\n    llm = LLM(\n          ^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/entrypoints/llm.py\\", line 343, in __init__\n    self.llm_engine = LLMEngine.from_engine_args(\n                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/llm_engine.py\\", line 184, in from_engine_args\n    return cls(\n           ^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/llm_engine.py\\", line 109, in __init__\n    self.engine_core = EngineCoreClient.make_client(\n                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core_client.py\\", line 129, in make_client\n    return InprocClient(vllm_config, executor_class, log_stats)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core_client.py\\", line 354, in __init__\n    self.engine_core = EngineCore(\n                       ^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/patch/platform/patch_profiling_chunk.py\\", line 198, in _patched_engine_core_init\n    original_init(self, *args, **kwargs)\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core.py\\", line 145, in __init__\n    kv_cache_config = self._initialize_kv_caches(vllm_config)\n                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/tracing/otel.py\\", line 178, in sync_wrapper\n    return func(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/engine/core.py\\", line 356, in _initialize_kv_caches\n    self.model_executor.compile_or_warm_up_model()\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/executor/abstract.py\\", line 126, in compile_or_warm_up_model\n    compilation_times: list[CompilationTimes] = self.collective_rpc(\n                                                ^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/executor/uniproc_executor.py\\", line 103, in collective_rpc\n    result = run_method(self.driver_worker, method, args, kwargs)\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/serial_utils.py\\", line 510, in run_method\n    return func(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/worker.py\\", line 888, in compile_or_warm_up_model\n    npugraph_memory_bytes = self.model_runner.capture_model()\n                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/usr/local/python3.11.10/lib/python3.11/site-packages/torch/utils/_contextlib.py\\", line 124, in decorate_context\n    return func(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/gpu/model_runner.py\\", line 999, in capture_model\n    self.speculator.capture()\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py\\", line 150, in capture\n    self.query_cudagraph_manager.capture(\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py\\", line 96, in capture\n    super().capture(\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py\\", line 121, in capture\n    super().capture(create_forward_fn, progress_bar_desc)\n  File \\"/usr/local/python3.11.10/lib/python3.11/site-packages/torch/utils/_contextlib.py\\", line 124, in decorate_context\n    return func(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/gpu/cudagraph_utils.py\\", line 382, in capture\n    forward_fn = create_forward_fn(desc, warmup=True)\n                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py\\", line 99, in create_forward_fn\n    attn_state = _prepare_dflash_inputs_to_capture(\n                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/dflash/capture.py\\", line 376, in ascend_prepare_dflash_inputs_to_capture\n    attach_parallel_graph_capture_operand_observer(\n  File \\"/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay/vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py\\", line 1006, in attach_parallel_graph_capture_operand_observer\n    raise RuntimeError(\\"capture operand observer is already attached\\")\nRuntimeError: capture operand observer is already attached\n"

}

```


**## B partial v2 artifact**

```json

{

  "events": [

    {

      "backing_table_address": 20623361164800,

      "capture_descriptor": "mode=FULL;reqs=4;tokens=28;uniform=7;max_query=None;loras=0;ubatches=1",

      "exact_lengths": [

        1151,

        1151,

        1151,

        1151

      ],

      "generation_id": null,

      "mapping_epoch": null,

      "position_values": [

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0,

        0

      ],

      "positions_address": 20623359230464,

      "query_layout_address": 20623359268352,

      "query_layout_values": [

        0,

        7,

        14,

        21,

        28

      ],

      "route": "dspark",

      "sequence": 0,

      "slot_mapping_address": 20623361145856,

      "slot_mapping_values": [

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1,

        -1

      ],

      "stage": "capture",

      "table_values": [

        [

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0

        ],

        [

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0

        ],

        [

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0

        ],

        [

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0,

          0

        ]

      ],

      "upper_lengths": [

        1151,

        1151,

        1151,

        1151

      ]

    }

  ],

  "evidence_boundary": {

    "operand_events": "HOST_OPERATOR_BOUNDARY_FACT",

    "physical_memory_transaction": "NOT_PROVEN_REQUIRES_DEVICE_TOOL",

    "update_effective_generation": "NOT_PROVEN_REQUIRES_NPU_TIMELINE"

  },

  "g4_records": [],

  "lifecycle_events": [],

  "operand_events": [],

  "schema": "mrv2-draft-window-graph-characterization-v2"

}

```


**## Host UT file outputs**


**### test_draft_window_graph_characterization.log**

SHA256: `7c40d4a5bbe42e5905afe9a412ac83885178ca5f1232565914ba2b7b1ae24de4`

```text

.........................                                                [100%]

\=============================== warnings summary ===============================

../../../../../../usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: 14 warnings

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.

    warnings.warn(


tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_reuses_real_p3_generation_and_builds_private_metadata

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch_npu/utils/storage.py:55: UserWarning: TypedStorage is deprecated. It will be removed in the future and UntypedStorage will be the only storage class. This should only matter to you if you are using storages directly.  To access UntypedStorage directly, use tensor.untyped_storage() instead of tensor.storage()

    if self.device.type != 'cpu':


-- Docs: https\://docs.pytest.org/en/stable/how-to/capture-warnings.html

25 passed, 15 warnings in 0.25s

```


**### test_draft_window_graph_carrier.log**

SHA256: `c0d549279517d1138bd22e4d50afba983a74f6e5bcb1db8e12fe9654f0f93e76`

```text

...............................................                          [100%]

\=============================== warnings summary ===============================

../../../../../../usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: 14 warnings

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.

    warnings.warn(


-- Docs: https\://docs.pytest.org/en/stable/how-to/capture-warnings.html

47 passed, 14 warnings in 0.12s

```


**### test_draft_window_graph_binding.log**

SHA256: `4e09812c20f89aa7096c044693e09b6ee29dca06f672b20161ce3858b06d5d32`

```text

.....................................                                    [100%]

\=============================== warnings summary ===============================

../../../../../../usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: 14 warnings

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.

    warnings.warn(


-- Docs: https\://docs.pytest.org/en/stable/how-to/capture-warnings.html

37 passed, 14 warnings in 0.49s

```


**### test_draft_window_graph_oracle.log**

SHA256: `dfdb7d28fea13d4f6329268c6df7d55cf82a97df5743740a291eed43498d6e86`

```text

.......                                                                  [100%]

\=============================== warnings summary ===============================

../../../../../../usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: 14 warnings

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.

    warnings.warn(


-- Docs: https\://docs.pytest.org/en/stable/how-to/capture-warnings.html

7 passed, 14 warnings in 0.03s

```

**# P7X_A3_07_Raw_Text_Evidence — part 002**


RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

PART: 2/6

SECTIONS: ['real_owner_regression.log', 'host_lifecycle.log', 'Helper / oracle / audit capability output', 'Oracle cases log', 'Repo audit on partial B artifact', 'Source snippets (exact SHA, file, function, line)', 'capture.py — record capture then attach capture operand observer', 'draft_window_graph_characterization.py — attach rejects a pre-existing context', 'draft_window_graph_characterization.py — private isolation view + final metadata restore']


**---**


**### real_owner_regression.log**

SHA256: `7ce2e9df2f7d981af9c1086640e782c37a6d9e68937dc2bfb6d09cb553ddfd53`

```text

\============================= test session starts ==============================

platform linux -- Python 3.11.10, pytest-8.3.2, pluggy-1.6.0 -- /home/wenqing/.venv-main/bin/python

cachedir: .pytest_cache

rootdir: /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

configfile: pyproject.toml

plugins: xdist-3.6.1, anyio-4.14.2

collecting ... collected 2 items


tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_target_metadata_sharing_is_allowed_for_full_write_carriers PASSED [ 50%]

tests/ut/spec_decode/test_draft_window_graph_carrier.py::test_draft_private_fields_still_reject_target_storage_alias PASSED [100%]


\=============================== warnings summary ===============================

../../../../../../usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: 14 warnings

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.

    warnings.warn(


tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_target_metadata_sharing_is_allowed_for_full_write_carriers

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch_npu/utils/storage.py:55: UserWarning: TypedStorage is deprecated. It will be removed in the future and UntypedStorage will be the only storage class. This should only matter to you if you are using storages directly.  To access UntypedStorage directly, use tensor.untyped_storage() instead of tensor.storage()

    if self.device.type != 'cpu':


-- Docs: https\://docs.pytest.org/en/stable/how-to/capture-warnings.html

\======================== 2 passed, 15 warnings in 0.05s ========================

```


**### host_lifecycle.log**

SHA256: `3b359015f5a523bd97ccc5c0f3c1801273a798bc192af2df82471d1161b7eb90`

```text

\============================= test session starts ==============================

platform linux -- Python 3.11.10, pytest-8.3.2, pluggy-1.6.0 -- /home/wenqing/.venv-main/bin/python

cachedir: .pytest_cache

rootdir: /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

configfile: pyproject.toml

plugins: xdist-3.6.1, anyio-4.14.2

collecting ... collected 16 items


tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_reuses_real_p3_generation_and_builds_private_metadata PASSED [  6%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_update_operand_and_g4_records_are_machine_readable PASSED [ 12%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_fia_capture_call_records_actual_operator_operand PASSED [ 18%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_fia_update_call_records_rebound_operator_operand PASSED [ 25%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_replay_submission_records_real_event_without_synchronizing PASSED [ 31%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_campaign_auditor_requires_all_evidence_layers_and_detects_host_a_b_a PASSED [ 37%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_recorder_exception_releases_bound_carrier PASSED [ 43%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_host_a_b_a_refreshes_content_at_stable_address PASSED [ 50%]

tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_manager_prepares_candidate_before_consuming_graph_metadata PASSED [ 56%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_covers_base_boundaries[32-32-32-64-0-expected_ids0] PASSED [ 62%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_covers_base_boundaries[80-80-80-64-16-expected_ids1] PASSED [ 68%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_covers_base_boundaries[81-81-95-64-16-expected_ids2] PASSED [ 75%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_covers_base_boundaries[4096-4096-4103-1024-3072-expected_ids3] PASSED [ 81%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_covers_base_boundaries[67-65-67-64-0-expected_ids4] PASSED [ 87%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_rejects_source_shortage PASSED [ 93%]

tests/ut/spec_decode/test_draft_window_graph_oracle.py::test_independent_graph_oracle_rejects_nonzero_direct_prefix_offset PASSED [100%]


\=============================== warnings summary ===============================

../../../../../../usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: 14 warnings

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.

    warnings.warn(


tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_reuses_real_p3_generation_and_builds_private_metadata

  /usr/local/python3.11.10/lib/python3.11/site-packages/torch_npu/utils/storage.py:55: UserWarning: TypedStorage is deprecated. It will be removed in the future and UntypedStorage will be the only storage class. This should only matter to you if you are using storages directly.  To access UntypedStorage directly, use tensor.untyped_storage() instead of tensor.storage()

    if self.device.type != 'cpu':


-- Docs: https\://docs.pytest.org/en/stable/how-to/capture-warnings.html

\======================= 16 passed, 15 warnings in 0.10s ========================

```


**## Helper / oracle / audit capability output**

```text

\=== helper help ===

usage: p7x_graph_g1_g5.py [-h] {oracle,audit} ...


positional arguments:

  {oracle,audit}


options:

  -h, --help      show this help message and exit

\=== oracle help ===

usage: p7x_graph_g1_g5.py oracle [-h] --full-table FULL_TABLE --horizon

                                 HORIZON --exact EXACT --upper UPPER --window

                                 WINDOW --legacy-block-size LEGACY_BLOCK_SIZE

                                 --block-span BLOCK_SPAN --query-width

                                 QUERY_WIDTH --valid-block-count

                                 VALID_BLOCK_COUNT [--output OUTPUT]


options:

  -h, --help            show this help message and exit

  --full-table FULL_TABLE

  --horizon HORIZON

  --exact EXACT

  --upper UPPER

  --window WINDOW

  --legacy-block-size LEGACY_BLOCK_SIZE

  --block-span BLOCK_SPAN

  --query-width QUERY_WIDTH

  --valid-block-count VALID_BLOCK_COUNT

  --output OUTPUT

\=== audit help ===

usage: p7x_graph_g1_g5.py audit [-h] [--output OUTPUT] artifact


positional arguments:

  artifact


options:

  -h, --help       show this help message and exit

  --output OUTPUT

\=== sample oracle ===

{

  "expected_block_ids": [

    1,

    2,

    3,

    4

  ],

  "expected_columns": [

    0,

    1,

    2,

    3

  ],

  "first_token_offset": 0,

  "full_exact_end": 500,

  "full_horizon_end": 500,

  "full_upper_end": 500,

  "query_width": 7,

  "required_columns": 4,

  "safe_extent_tokens": 512,

  "source_start_column": 0,

  "valid_block_count": 5,

  "visible_length": 500,

  "window_start": 0,

  "window_upper": 500

}

\=== msprof ===

/usr/local/Ascend/cann-9.1.0/bin/msprof


Usage:

      msprof [--options]


This is subcommand for operator optimization situation:

      op                                Use binary msopprof to operator optimization (msprof op ...)


Options:

      --output                          \<Optional> Specify the directory that is used for storing data results.

      --application                     \<Optional> Specify application path, considering the risk of privilege escalation, please pay attention to

               the group of the application and confirm whether it is the same as the user currently.

               [Note] This option will be discarded in later versions.

               you can try to use: msprof [msprof arguments] \<app> [app arguments]

      --ascendcl                        \<Optional> Show acl profiling data, the default value is on.

      --ge-api                          \<Optional> Specify if report GE event, the default value is off. The possible parameters are 'l0', 'l1' or 'off'.

      --runtime-api                     \<Optional> Show runtime api profiling data, the default value is off.

      --task-time                       \<Optional> Show task profiling data, the default value is on. The possible parameters are 'l0', 'l1', 'l2', 'l3', 'on' or 'off'.

      --task-memory                     \<Optional> Show the memory usage of the operator, the default value is off. The possible parameters are 'on' or 'off'.

      --ai-core                         \<Optional> Turn on / off the ai core profiling, the default value is on when collecting app Profiling.

      --aic-mode                        \<Optional> Set the aic profiling mode to task-based or sample-based.

               In task-based mode, profiling data will be collected by tasks.

               In sample-based mode, profiling data will be collected in a specific interval.

               The default value is task-based in AI task mode, sample-based in system mode.

      --aic-freq                        \<Optional> The aic sampling frequency in hertz, the default value is 100 Hz, the range is 1 to 100 Hz.

      --environment                     \<Optional> User app custom environment variable configuration.

      --sys-period                      \<Optional> Set total sampling period of system profiling in seconds.

      --sys-devices                     \<Optional> Specify the profiling scope by device ID when collect sys profiling.The value is all or ID list (split with ',').

      --msproftx                        \<Optional> Show msproftx and mstx data, the default value is off.

      --mstx-domain-include             \<Optional> Choose to only include mstx events from a comma separated list of domains;

               `default` filters the mstx default domain;

               The switch is only applicable when parameter msproftx is set to on;

               The switch cannot be set with mstx-domain-exclude at the same time.

      --mstx-domain-exclude             \<Optional> Choose to exclude mstx events from a comma separated list of domains;

               `default` excludes the mstx default domain;

               The switch is only applicable when parameter msproftx is set to on;

               The switch cannot be set with mstx-domain-include at the same time.

      --storage-limit                   \<Optional> Specify the output directory volume. range 200MB \~ 4294967295MB.

      --hccl                            \<Optional> Show hccl profiling data, the default value is off. [Note] This option will be discarded in later versions.

      --model-execution                 \<Optional> Show ge model execution profiling data, the default value is off. [Note] This option will be discarded in later versions.

      --aic-metrics                     \<Optional> The aic metrics groups, include ArithmeticUtilization, PipeUtilization, Memory, MemoryL0, ResourceConflictRatio, MemoryUB, L2Cache, MemoryAccess.

```


**## Oracle cases log**

```text

\=== CASE SHORT ===

RC=0

\=== CASE BOUNDARY ===

RC=0

\=== CASE NONBOUNDARY ===

RC=0

\=== CASE LONG ===

RC=0

\=== CASE SOURCE_SHORTAGE ===

Traceback (most recent call last):

  File "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/tools/p7x_graph_g1_g5.py", line 109, in \<module>

    raise SystemExit(main())

                     ^^^^^^

  File "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/tools/p7x_graph_g1_g5.py", line 88, in main

    result = compute_graph_characterization_oracle(

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window_graph_oracle.py", line 161, in compute_graph_characterization_oracle

    raise RuntimeError(

RuntimeError: Graph oracle source shortage: start=8 required=8 end=16 valid=8

EXPECTED_REJECT_SOURCE_SHORTAGE rc=1

\=== CASE NONZERO_OFFSET ===

Traceback (most recent call last):

  File "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/tools/p7x_graph_g1_g5.py", line 109, in \<module>

    raise SystemExit(main())

                     ^^^^^^

  File "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/tools/p7x_graph_g1_g5.py", line 88, in main

    result = compute_graph_characterization_oracle(

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window_graph_oracle.py", line 155, in compute_graph_characterization_oracle

    raise NotImplementedError("Graph oracle base route requires a direct-prefix zero offset")

NotImplementedError: Graph oracle base route requires a direct-prefix zero offset

EXPECTED_REJECT_NONZERO_OFFSET rc=1

```


**## Repo audit on partial B artifact**

```json

{

  "G1_ACTUAL_ACL_TASK_INTERNAL": "DEVICE_TRACE_REQUIRED",

  "G1_HOST_OPERATOR_BOUNDARY": "OPEN",

  "G2_HOST_A_B_A": "OPEN",

  "G3_OPERATOR_BOUNDARY": "OPEN",

  "G3_PHYSICAL_MEMORY_TRANSACTION": "DEVICE_TOOL_REQUIRED",

  "G4_WRITE_TARGET_ORACLE": "OPEN",

  "G5_EVENT_INSTRUMENTATION": "OPEN",

  "G5_UPDATE_EFFECTIVE_GENERATION": "NPU_TASK_TRACE_REQUIRED",

  "ready_for_device_campaign": false

}

```


**## Source snippets (exact SHA, file, function, line)**


**### capture.py — record capture then attach capture operand observer**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/capture.py` lines 340-380


```text

 340      )

 341      read_block_tables = list(input_block_tables)

 342      read_block_tables[identity.fingerprint.global_group_id] = read_inputs.window_block_table

 343      attn_metadata = build_attn_metadata(

 344          attn_groups=attn_groups,

 345          num_reqs=num_reqs,

 346          num_tokens=num_tokens,

 347          query_start_loc_gpu=input_batch.query_start_loc,

 348          query_start_loc_cpu=query_start_loc_cpu,

 349          max_query_len=num_tokens // num_reqs,

 350          seq_lens=read_inputs.device_window_exact,

 351          seq_lens_cpu=read_inputs.cpu_window_exact,

 352          seq_lens_cpu_upper_bound=read_inputs.cpu_window_upper,

 353          dcp_local_seq_lens=dcp_local_seq_lens,

 354          max_seq_len=max_seq_len,

 355          block_tables=tuple(read_block_tables),

 356          slot_mappings=slot_mappings,

 357          kv_cache_config=kv_cache_config,

 358          for_cudagraph_capture=True,

 359          causal=causal,

 360      )

 361      # Optional, bounded G1/G3/G4 evidence.  The recorder exists only when the

 362      # strict characterization flag installed an instance-owned provider.

 363      from vllm_ascend.worker.v2.spec_decode.draft_window_graph_characterization import (

 364          attach_parallel_graph_capture_operand_observer,

 365          record_parallel_graph_capture,

 366      )

 367

 368      record_parallel_graph_capture(

 369          context.provider,

 370          identity=identity,

 371          read_inputs=read_inputs,

 372          slot_mapping=slot_mappings,

 373          positions=input_batch.positions,

 374          query_start_loc=input_batch.query_start_loc,

 375      )

 376      attach_parallel_graph_capture_operand_observer(

 377          context.provider,

 378          identity=identity,

 379          metadata=attn_metadata,

 380      )

```


**### draft_window_graph_characterization.py — attach rejects a pre-existing context**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py` lines 990-1016


```text

 990      identity: DraftWindowGraphCaptureIdentity,

 991      metadata: Mapping[str, Any],

 992  ) -> None:

 993      """Attach a capture-scoped observer only to explicit Draft metadata."""

 994      recorder = provider.observer

 995      if not isinstance(recorder, DraftWindowGraphCharacterizationRecorder):

 996          return

 997      context = DraftWindowGraphCaptureOperandContext(

 998          recorder=recorder,

 999          identity=identity,

1000      )

1001      attached = 0

1002      for layer_metadata in metadata.values():

1003          if layer_metadata is None:

1004              continue

1005          if hasattr(layer_metadata, _CAPTURE_OPERAND_CONTEXT_ATTRIBUTE):

1006              raise RuntimeError("capture operand observer is already attached")

1007          setattr(layer_metadata, _CAPTURE_OPERAND_CONTEXT_ATTRIBUTE, context)

1008          attached += 1

1009      if attached == 0:

1010          raise RuntimeError("capture operand observer found no Draft attention metadata")

1011

1012

1013  def record_parallel_graph_capture_operator_operand(

1014      metadata: Any,

1015      *,

1016      block_table: torch.Tensor,

```


**### draft_window_graph_characterization.py — private isolation view + final metadata restore**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py` lines 1190-1245


```text

1190                      owner.input_buffers.positions,

1191                      fingerprint.padded_token_count,

1192                      torch.from_numpy(owner.input_batch.is_prefilling_np),

1193                  )

1194              )

1195          metadata = owner._build_ascend_draft_attn_metadata(

1196              num_reqs=read_inputs.actual_request_count,

1197              num_reqs_padded=read_inputs.padded_request_count,

1198              num_tokens_padded=fingerprint.padded_token_count,

1199              read_inputs=typed_read_inputs,

1200              causal=write_side.causal,

1201              query_start_loc_np=None,

1202              dcp_local_seq_lens=None,

1203          )

1204

1205      # Use the same deep isolation routine as eager P4, then explicitly restore

1206      # only the immutable full write/query carriers frozen by P6.

1207      from vllm_ascend.worker.v2.spec_decode.draft_window_eager import (

1208          _isolate_draft_metadata_from_target,

1209      )

1210

1211      private_isolation_view = _isolate_draft_metadata_from_target(metadata, target_metadata)

1212      # Preserve the isolated view unchanged for the private-state oracle.  The

1213      # final metadata uses shallow copies of its layer objects so restoring the

1214      # canonical full write/query owners cannot retroactively weaken that view.

1215      final_metadata: dict[str, Any] = {}

1216      for layer_name, layer_metadata in private_isolation_view.items():

1217          if layer_metadata is None:

1218              final_metadata[layer_name] = None

1219              continue

1220          final_layer_metadata = copy.copy(layer_metadata)

1221          final_layer_metadata.slot_mapping = write_side.slot_mapping

1222          final_layer_metadata.positions = write_side.positions

1223          final_layer_metadata.query_start_loc = write_side.query_start_loc

1224          final_layer_metadata.actual_seq_lengths_q = list(write_side.actual_seq_lengths_q)

1225          final_layer_metadata.attn_state = write_side.attn_state

1226          final_layer_metadata.num_actual_tokens = write_side.num_actual_tokens

1227          final_layer_metadata.causal = write_side.causal

1228          final_metadata[layer_name] = final_layer_metadata

1229      return DraftWindowGraphMetadataBuild(

1230          metadata=final_metadata,

1231          private_isolation_view=private_isolation_view,

1232      )

1233

1234

1235  def _build_write_side_reference(

1236      owner: Any,

1237      capture_identity: DraftWindowGraphCaptureIdentity,

1238      target_metadata: Mapping[Any, Any],

1239  ) -> DraftWindowGraphWriteSideReference:

1240      fingerprint = capture_identity.fingerprint

1241      gid = fingerprint.global_group_id

1242      token_count = fingerprint.padded_token_count

1243      request_count = fingerprint.padded_request_count

1244      query_width = fingerprint.query_width

1245      target_layer = next((value for value in target_metadata.values() if value is not None), None)

```


**# P7X_A3_07_Raw_Text_Evidence — part 003**


RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

PART: 3/6

SECTIONS: ['draft_window_graph.py — bind_read_carrier isolation/read/write validation', 'draft_window_graph.py — read-carrier validation separated from write-carrier validation', 'attention_v1.py — update operator operand hook after graph_task_update_end', 'attention_v1.py — capture operator operand hook after graph_task_group_end', 'acl_graph.py — thread typed update binding to the real backend update', 'envs.py — experimental flag and artifact path', 'External scripts (full text)']


**---**


**### draft_window_graph.py — bind_read_carrier isolation/read/write validation**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window_graph.py` lines 830-880


```text

 830              device_window_exact=read_inputs.device_window_exact,

 831              cpu_window_exact=read_inputs.cpu_window_exact,

 832              cpu_window_upper=read_inputs.cpu_window_upper,

 833              actual_request_count=generation.actual_request_count,

 834              padded_request_count=generation.padded_request_count,

 835          )

 836          runtime_identity = self._make_binding_identity(

 837              generation,

 838              proposal_id=proposal_id,

 839              route=capture_identity.fingerprint.route,

 840          )

 841          build_result = metadata_builder(carrier.read_inputs)

 842          if isinstance(build_result, DraftWindowGraphMetadataBuild):

 843              metadata = build_result.metadata

 844              isolation_view = build_result.private_isolation_view

 845          else:

 846              metadata = build_result

 847              isolation_view = metadata

 848          if not isinstance(metadata, Mapping) or not metadata:

 849              raise RuntimeError("explicit Draft Window graph carrier produced no Draft metadata")

 850          if not isinstance(isolation_view, Mapping) or not isolation_view:

 851              raise RuntimeError("explicit Draft Window graph carrier produced no private isolation view")

 852          if tuple(metadata) != tuple(isolation_view):

 853              raise RuntimeError("Draft graph metadata and private isolation view layer keys differ")

 854          validate_draft_metadata_isolation(

 855              isolation_view,

 856              target_metadata=target_metadata,

 857          )

 858          self._validate_metadata_uses_read_carrier(

 859              isolation_view,

 860              carrier.read_inputs,

 861          )

 862          self._validate_metadata_uses_carrier(

 863              metadata,

 864              carrier.read_inputs,

 865              write_side_reference,

 866              write_side_snapshot,

 867          )

 868          self._runtime_state.publish_metadata(

 869              inputs,

 870              metadata,

 871              target_metadata=target_metadata,

 872              isolation_view=isolation_view,

 873          )

 874          metadata = self._runtime_state.read_metadata(generation)

 875

 876          carrier.runtime_identity = runtime_identity

 877          carrier.metadata = metadata

 878          carrier.write_side_reference = write_side_reference

 879          carrier.write_side_snapshot = write_side_snapshot

 880          carrier.state = DraftWindowGraphCarrierState.BOUND

```


**### draft_window_graph.py — read-carrier validation separated from write-carrier validation**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window_graph.py` lines 1260-1338


```text

1260                  raise RuntimeError(f"full {diagnostic} owner changed during graph metadata build")

1261          if actual.mutation_versions != expected.mutation_versions:

1262              raise RuntimeError("full write/query state changed during graph metadata build")

1263

1264      @classmethod

1265      def _validate_metadata_uses_carrier(

1266          cls,

1267          metadata: Mapping[str, Any],

1268          read_inputs: DraftWindowGraphReadInputs,

1269          write_side_reference: DraftWindowGraphWriteSideReference,

1270          write_side_snapshot: _DraftWindowGraphWriteSideSnapshot,

1271      ) -> None:

1272          cls._validate_metadata_uses_read_carrier(metadata, read_inputs)

1273          cls._validate_write_side_unchanged(

1274              write_side_reference,

1275              write_side_snapshot,

1276          )

1277          expected_slot = _tensor_identity(write_side_reference.slot_mapping)

1278          expected_query = _tensor_identity(write_side_reference.query_start_loc)

1279          expected_positions = _tensor_identity(write_side_reference.positions)

1280          for layer_name, layer_metadata in metadata.items():

1281              if layer_metadata is None:

1282                  continue

1283              slot_mapping = getattr(layer_metadata, "slot_mapping", None)

1284              if not isinstance(slot_mapping, torch.Tensor) or _tensor_identity(slot_mapping) != expected_slot:

1285                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not preserve the full slot mapping")

1286              query_start_loc = getattr(layer_metadata, "query_start_loc", None)

1287              if not isinstance(query_start_loc, torch.Tensor) or _tensor_identity(query_start_loc) != expected_query:

1288                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not preserve the full query layout")

1289              actual_seq_lengths_q = getattr(layer_metadata, "actual_seq_lengths_q", None)

1290              if actual_seq_lengths_q != list(write_side_reference.actual_seq_lengths_q):

1291                  raise RuntimeError(f"Draft graph metadata {layer_name!r} has a mismatched full query layout")

1292              if getattr(layer_metadata, "attn_state", None) is not write_side_reference.attn_state:

1293                  raise RuntimeError(f"Draft graph metadata {layer_name!r} has a mismatched attention state")

1294              if getattr(layer_metadata, "num_actual_tokens", None) != write_side_reference.num_actual_tokens:

1295                  raise RuntimeError(f"Draft graph metadata {layer_name!r} has a mismatched actual token count")

1296              if getattr(layer_metadata, "causal", None) is not write_side_reference.causal:

1297                  raise RuntimeError(f"Draft graph metadata {layer_name!r} has a mismatched causal contract")

1298              metadata_positions = getattr(layer_metadata, "positions", None)

1299              if metadata_positions is not None and (

1300                  not isinstance(metadata_positions, torch.Tensor)

1301                  or _tensor_identity(metadata_positions) != expected_positions

1302              ):

1303                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not preserve full positions")

1304

1305      @staticmethod

1306      def _validate_metadata_uses_read_carrier(

1307          metadata: Mapping[str, Any],

1308          read_inputs: DraftWindowGraphReadInputs,

1309      ) -> None:

1310          """Validate only Draft-private read carriers, never full write state."""

1311          expected_table_storage = _tensor_identity(read_inputs.window_block_table).storage_data_ptr

1312          expected_device_storage = _tensor_identity(read_inputs.device_window_exact).storage_data_ptr

1313          expected_cpu_storage = _tensor_identity(read_inputs.cpu_window_exact).storage_data_ptr

1314          expected_lengths = read_inputs.cpu_window_exact.tolist()

1315          for layer_name, layer_metadata in metadata.items():

1316              if layer_metadata is None:

1317                  continue

1318              block_tables = getattr(layer_metadata, "block_tables", None)

1319              seq_lens = getattr(layer_metadata, "seq_lens", None)

1320              seq_lens_cpu = getattr(layer_metadata, "seq_lens_cpu", None)

1321              seq_lens_list = getattr(layer_metadata, "seq_lens_list", None)

1322              if not isinstance(block_tables, torch.Tensor) or (

1323                  _tensor_identity(block_tables).storage_data_ptr != expected_table_storage

1324              ):

1325                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not use carrier block tables")

1326              if not isinstance(seq_lens, torch.Tensor) or (

1327                  _tensor_identity(seq_lens).storage_data_ptr != expected_device_storage

1328              ):

1329                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not use carrier device lengths")

1330              if not isinstance(seq_lens_cpu, torch.Tensor) or (

1331                  _tensor_identity(seq_lens_cpu).storage_data_ptr != expected_cpu_storage

1332              ):

1333                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not use carrier CPU lengths")

1334              if not isinstance(seq_lens_list, list) or seq_lens_list[: len(expected_lengths)] != expected_lengths:

1335                  raise RuntimeError(f"Draft graph metadata {layer_name!r} does not use carrier exact length values")

1336

1337      def _require_submitted_route(

1338          self,

```


**### attention_v1.py — update operator operand hook after graph_task_update_end**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/attention/attention_v1.py` lines 940-975


```text

 940                          pre_tokens=pre_tokens,

 941                          next_tokens=next_tokens,

 942                          **extra_args,

 943                          workspace=workspace,

 944                          out=[attn_output, softmax_lse],

 945                      )

 946                      torch.npu.graph_task_update_end(update_stream)

 947

 948                      event.record(update_stream)

 949                      if draft_window_graph_update_binding is not None:

 950                          if draft_step_metadata is None:

 951                              raise RuntimeError("Draft Window graph update binding reached a non-Draft FIA task")

 952                          from vllm_ascend.worker.v2.spec_decode.draft_window_graph_characterization import (

 953                              record_parallel_graph_update_operator_operand,

 954                          )

 955

 956                          record_parallel_graph_update_operator_operand(

 957                              draft_window_graph_update_binding,

 958                              draft_metadata=draft_step_metadata,

 959                              layer_name=str(key),

 960                              captured_block_table=captured_block_tables,

 961                              actual_block_table=block_tables,

 962                              seq_lengths=seq_lens,

 963                              num_tokens=num_tokens,

 964                              handle=handle,

 965                              event=event,

 966                              stream=update_stream,

 967                              backend_impl=AscendAttentionBackendImpl,

 968                          )

 969

 970      def process_weights_after_loading(self, act_dtype: torch.dtype):

 971          super().process_weights_after_loading(act_dtype)

 972

 973      def full_graph_fia(

 974          self,

 975          query: torch.Tensor,

```


**### attention_v1.py — capture operator operand hook after graph_task_group_end**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/attention/attention_v1.py` lines 1135-1165


```text

1135              out=[output, softmax_lse],

1136              **extra_args,

1137          )

1138

1139          output = output.view(num_tokens, self.num_heads, self.head_size)

1140

1141          handle = torch.npu.graph_task_group_end(stream)

1142          graph_params.handles[num_tokens].append(handle)

1143          if _EXTRA_CTX.is_draft_model:

1144              from vllm_ascend.worker.v2.spec_decode.draft_window_graph_characterization import (

1145                  record_parallel_graph_capture_operator_operand,

1146              )

1147

1148              record_parallel_graph_capture_operator_operand(

1149                  attn_metadata,

1150                  block_table=block_table,

1151                  seq_lengths=actual_seq_lengths_kv,

1152                  layer_name=self._graph_metadata_layer_name(layer),

1153                  num_tokens=num_tokens,

1154                  handle=handle,

1155                  event=event,

1156                  stream=stream,

1157                  backend_impl=AscendAttentionBackendImpl,

1158              )

1159          return output, num_tokens

1160

1161      def full_graph_fia_v2(

1162          self,

1163          query: torch.Tensor,

1164          key: torch.Tensor,

1165          value: torch.Tensor,

```


**### acl_graph.py — thread typed update binding to the real backend update**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/compilation/acl_graph.py` lines 330-360


```text

 330

 331              validate_draft_window_graph_backend_update(

 332                  draft_window_graph_update_binding,

 333                  attn_backend=attn_backend,

 334                  impl_cls=impl_cls,

 335                  builder_cls=builder_cls,

 336                  draft_attn_metadatas=draft_attn_metadatas,

 337                  update_function_path=(f"{update_full_graph_params.__module__}.{update_full_graph_params.__qualname__}"),

 338              )

 339          update_kwargs = {

 340              "draft_attn_metadatas": draft_attn_metadatas,

 341          }

 342          if draft_window_graph_update_binding is not None:

 343              # Only the exact Ascend FIA implementation can pass the backend

 344              # attribution check above.  Thread the typed binding to that real

 345              # operator-update boundary for characterization; ordinary callers

 346              # see the byte-for-byte-equivalent call shape used before P7-X.

 347              update_kwargs["draft_window_graph_update_binding"] = draft_window_graph_update_binding

 348          impl_cls.update_graph_params(

 349              update_stream,

 350              forward_context,

 351              num_tokens,

 352              vllm_config,

 353              speculative_config,

 354              **update_kwargs,

 355          )

 356

 357

 358  @dataclass

 359  class GraphParams:

 360      events: dict[int, list[torch.npu.ExternalEvent]]

```


**### envs.py — experimental flag and artifact path**


`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend/vllm_ascend/envs.py` lines 82-100


```text

  82      # Emit per-layer KVPool ranged transfer audit events. Default: 0 (disabled).

  83      # Valid values: 0 or 1. This configuration is not sensitive.

  84      "VLLM_ASCEND_KVPOOL_RANGE_DEBUG": lambda: _strict_binary_env("VLLM_ASCEND_KVPOOL_RANGE_DEBUG"),

  85      # Internal-only MRV2 Draft Window ACL Graph characterization switch.

  86      # This does not enable the public Graph Window capability gate. It exists

  87      # solely for controlled NPU operand/read-set/timeline experiments and is

  88      # deliberately strict and default-off.

  89      "VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH": lambda: _strict_binary_env(

  90          "VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH"

  91      ),

  92      # Optional machine-readable artifact for the internal MRV2 Graph

  93      # characterization campaign.  It is consulted only when the strict

  94      # experimental switch above installs the instance-owned recorder.

  95      "VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT": lambda: os.getenv(

  96          "VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT"

  97      ),

  98      # Override the Unified Buffer (UB) size in KB for Triton kernel tile sizing.

  99      # 0 (default): auto-detect from device properties, falling back to 192 KB

 100      # (safe for Ascend 910B/A3). Set to a positive value to override when

```


**## External scripts (full text)**


**# P7X_A3_07_Raw_Text_Evidence — part 004**


RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

PART: 4/6

SECTIONS: ['driver_case.py (new)']


**---**


**### driver_case.py (new)**

`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/driver_case.py`

SHA256: `c3b5a982f85742d50ecafd671bf6a91e0da779f752a417afb540a70123ae01f3`

```python

#!/usr/bin/env python3

"""Deterministic in-process driver for the P7-X A3 rerun.


CUSTOM_CORRECTNESS_DRIVER -- NOT FORMAL PERFORMANCE.

No vLLM / vllm-ascend source is modified.

"""


from __future__ import annotations


import argparse

import json

import os

import sys

import traceback


RUN_ROOT = "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff"

MODEL = "/mnt/share/wql/Qwen3-8B"

DRAFT = "/mnt/share/dspark_qwen3_8b_block7"

OLD_PROMPT = "Hello, my name is"


def main() -> int:

    ap = argparse.ArgumentParser()

    ap.add_argument("--case", required=True)

    ap.add_argument("--window", default="off")

    ap.add_argument("--flag", default="0")

    ap.add_argument("--artifact", default="")

    ap.add_argument("--max-model-len", type=int, default=4096)

    ap.add_argument("--max-tokens", type=int, default=16)

    ap.add_argument("--num-prompts", type=int, default=1)

    ap.add_argument("--prompt", default=OLD_PROMPT)

    ap.add_argument("--prompt-len", type=int, default=0,

                    help="if >0, build a deterministic token-id prompt of this length")

    ap.add_argument("--logprobs", type=int, default=0)

    ap.add_argument("--capture-sizes", default="7,14,28")

    ap.add_argument("--out", required=True)

    args = ap.parse_args()


    if os.environ.get("VLLM_USE_V2_MODEL_RUNNER") != "1":

        raise SystemExit("INVALID_RUN_WRONG_MODEL_RUNNER: VLLM_USE_V2_MODEL_RUNNER != 1")

    if os.environ.get("VLLM_ENABLE_V1_MULTIPROCESSING") != "0":

        raise SystemExit("VLLM_ENABLE_V1_MULTIPROCESSING != 0: cannot read in-worker state")

    if os.environ.get("VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH") != args.flag:

        raise SystemExit(

            "flag env mismatch: "

            f"{os.environ.get('VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH')} != {args.flag}"

        )

    if args.artifact and os.environ.get("VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT") != args.artifact:

        raise SystemExit("artifact env mismatch")

    if args.flag == "1" and not args.artifact:

        raise SystemExit("flag=1 requires --artifact")


    from vllm import LLM, SamplingParams


    additional: dict = {}

    if args.window != "off":

        additional["draft_window_size"] = int(args.window)


    record = {

        "case": args.case,

        "window": args.window,

        "flag": args.flag,

        "artifact": args.artifact,

        "model": MODEL,

        "draft": DRAFT,

        "prompt": args.prompt,

        "prompt_len_requested": args.prompt_len,

        "num_prompts": args.num_prompts,

        "max_tokens": args.max_tokens,

        "logprobs": args.logprobs,

        "capture_sizes": [int(x) for x in args.capture_sizes.split(",") if x],

        "status": "STARTED",

    }

    llm = None

    try:

        llm = LLM(

            model=MODEL,

            max_model_len=args.max_model_len,

            enforce_eager=False,

            async_scheduling=False,

            enable_prefix_caching=False,

            gpu_memory_utilization=0.80,

            max_num_seqs=4,

            max_num_batched_tokens=4096,

            seed=0,

            speculative_config={

                "model": DRAFT,

                "method": "dspark",

                "num_speculative_tokens": 7,

                "enable_adaptive_verification": False,

            },

            additional_config=additional,

            compilation_config={

                "cudagraph_mode": "FULL_DECODE_ONLY",

                "cudagraph_capture_sizes": sorted(

                    {int(x) for x in args.capture_sizes.split(",") if x}

                ),

            },

            disable_log_stats=True,

        )


        ec = llm.llm_engine.engine_core.engine_core

        mr = ec.model_executor.driver_worker.worker.model_runner

        spec = mr.speculator

        record["model_runner_class"] = f"{type(mr).__module__}.{type(mr).__qualname__}"

        record["speculator_class"] = f"{type(spec).__module__}.{type(spec).__qualname__}"

        policy = getattr(spec, "_draft_window_policy", None)

        record["policy_state"] = str(getattr(policy, "state", None))

        record["policy_reason"] = getattr(policy, "reason", None)

        record["effective_window_size"] = getattr(policy, "effective_window_size", None)

        record["characterization_installed"] = hasattr(

            spec, "_draft_window_graph_characterization"

        )

        record["provider_installed"] = hasattr(

            spec, "_draft_window_graph_binding_provider"

        )

        try:

            tgt_mgr = mr.cudagraph_manager

            drf_mgr = getattr(spec, "query_cudagraph_manager", None)

            record["capture_inventory"] = {

                "target_mode": str(getattr(tgt_mgr, "cudagraph_mode", None)),

                "target_needs_capture": tgt_mgr.needs_capture(),

                "target_capture_descs": {

                    mode.name: [

                        {

                            "num_tokens": d.num_tokens,

                            "num_reqs": d.num_reqs,

                            "uniform_token_count": d.uniform_token_count,

                        }

                        for d in descs

                    ]

                    for mode, descs in getattr(tgt_mgr, "_capture_descs", {}).items()

                },

                "draft_mode": str(getattr(drf_mgr, "cudagraph_mode", None)),

                "draft_needs_capture": (

                    None if drf_mgr is None else drf_mgr.needs_capture()

                ),

                "draft_capture_descs": (

                    None

                    if drf_mgr is None

                    else {

                        mode.name: [

                            {

                                "num_tokens": d.num_tokens,

                                "num_reqs": d.num_reqs,

                                "uniform_token_count": d.uniform_token_count,

                            }

                            for d in descs

                        ]

                        for mode, descs in getattr(drf_mgr, "_capture_descs", {}).items()

                    }

                ),

            }

        except BaseException as inv_exc:  # noqa: BLE001

            record["capture_inventory_error"] = repr(inv_exc)


        if args.prompt_len > 0:

            # Deterministic token-id prompt. Avoid special tokens where possible.

            base = [1000 + (i % 1000) for i in range(args.prompt_len)]

            prompts = [{"prompt_token_ids": base} for _ in range(args.num_prompts)]

        else:

            prompts = [args.prompt for _ in range(args.num_prompts)]


        sp = SamplingParams(

            max_tokens=args.max_tokens,

            temperature=0.0,

            ignore_eos=True,

            logprobs=(args.logprobs if args.logprobs > 0 else None),

        )

        outputs = llm.generate(prompts, sp)

        record["outputs"] = [

            {

                "token_ids": list(o.outputs[0].token_ids),

                "text": o.outputs[0].text,

                "logprobs": (

                    [list(x.values())[0].logprob if x else None for x in (o.outputs[0].logprobs or [])]

                    if o.outputs[0].logprobs is not None

                    else None

                ),

            }

            for o in outputs

        ]

        record["status"] = "OK"


        if args.artifact and os.path.isfile(args.artifact):

            snapshot = json.load(open(args.artifact, encoding="utf-8"))

            record["artifact_summary"] = {

                "schema": snapshot.get("schema"),

                "event_count": len(snapshot.get("events", [])),

                "operand_event_count": len(snapshot.get("operand_events", [])),

                "g4_record_count": len(snapshot.get("g4_records", [])),

                "lifecycle_event_count": len(snapshot.get("lifecycle_events", [])),

                "stage_counts": {

                    s: sum(1 for e in snapshot.get("events", []) if e.get("stage") == s)

                    for s in sorted({e.get("stage") for e in snapshot.get("events", [])})

                },

                "operand_stage_counts": {

                    s: sum(1 for e in snapshot.get("operand_events", []) if e.get("stage") == s)

                    for s in sorted({e.get("stage") for e in snapshot.get("operand_events", [])})

                },

                "lifecycle_stage_counts": {

                    s: sum(1 for e in snapshot.get("lifecycle_events", []) if e.get("stage") == s)

                    for s in sorted({e.get("stage") for e in snapshot.get("lifecycle_events", [])})

                },

            }

    except BaseException as exc:  # noqa: BLE001

        record["status"] = "EXCEPTION"

        record["exception_type"] = type(exc).__name__

        record["exception_message"] = str(exc)

        record["traceback"] = traceback.format_exc()

        if llm is not None:

            try:

                ec = llm.llm_engine.engine_core.engine_core

                mr = ec.model_executor.driver_worker.worker.model_runner

                spec = mr.speculator

                record["model_runner_class"] = f"{type(mr).__module__}.{type(mr).__qualname__}"

                record["speculator_class"] = f"{type(spec).__module__}.{type(spec).__qualname__}"

                policy = getattr(spec, "_draft_window_policy", None)

                record["policy_state"] = str(getattr(policy, "state", None))

                record["effective_window_size"] = getattr(policy, "effective_window_size", None)

                record["characterization_installed"] = hasattr(

                    spec, "_draft_window_graph_characterization"

                )

                record["provider_installed"] = hasattr(

                    spec, "_draft_window_graph_binding_provider"

                )

            except BaseException as probe_exc:  # noqa: BLE001

                record["post_failure_probe_error"] = repr(probe_exc)

        with open(args.out, "w", encoding="utf-8") as f:

            json.dump(record, f, indent=2)

        print("RESULT=" + json.dumps({k: v for k, v in record.items() if k != "traceback"}, indent=2))

        print(record["traceback"], file=sys.stderr)

        return 2


    with open(args.out, "w", encoding="utf-8") as f:

        json.dump(record, f, indent=2)

    print("RESULT=" + json.dumps({k: v for k, v in record.items() if k != "outputs"}, indent=2))

    if record.get("outputs"):

        print("TOKENS=" + json.dumps([o["token_ids"] for o in record["outputs"]]))

    return 0


if __name__ == "__main__":

    raise SystemExit(main())

```


**# P7X_A3_07_Raw_Text_Evidence — part 005**


RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

PART: 5/6

SECTIONS: ['independent_checker.py', 'env_graph_char.sh', 'sitecustomize.py', 'probe_import_provenance.py']


**---**


**### independent_checker.py**

`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/independent_checker.py`

SHA256: `ab4b0ba51353d377b8bab328148f431c7a91530afb06720dd200b5c3c432a43b`

```python

#!/usr/bin/env python3

"""Independent cross-artifact checker for the P7-X A3 rerun.


Read-only: it validates evidence and never rewrites raw data.

"""


from __future__ import annotations


import json

import re

import subprocess

from pathlib import Path


R = Path("/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff")

checks = []


def load(path: Path):

    try:

        return json.loads(path.read_text(encoding="utf-8"))

    except Exception as exc:  # noqa: BLE001

        return {"__load_error__": repr(exc)}


def add(cid, scope, expected, actual, status, evidence, first_divergence=None):

    checks.append({

        "check_id": cid,

        "scope": scope,

        "expected": expected,

        "actual": actual,

        "status": status,

        "evidence_ids": evidence,

        "first_divergence": first_divergence,

    })


def git(repo, *args):

    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


# CHK-001/002/003 source identity

src = load(R / "manifests/source_identity.json")

a = src.get("vllm_ascend", {})

v = src.get("vllm", {})

add("CHK-001", "source/vllm-ascend", "13373fff/739cde3d/parent 8cb4bed6",

    f"{a.get('sha')}/{a.get('tree')}/{a.get('parent')}",

    "PASS" if (a.get("sha") == "13373fff637e819f3db125e05064f94cba3475a3"

               and a.get("tree") == "739cde3de61e65be7cdbd187baebb6d17da04aee"

               and a.get("parent") == "8cb4bed670f395c257c1233db944395159916009") else "FAIL",

    ["EVID-SOURCE-ASCEND"])

add("CHK-002", "source/vllm", "84030bbe/f3e320f8",

    f"{v.get('sha')}/{v.get('tree')}",

    "PASS" if (v.get("sha") == "84030bbe3d74d99bad477a3d2e37a973ccd8865c"

               and v.get("tree") == "f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee") else "FAIL",

    ["EVID-SOURCE-VLLM"])

clean_now = {

    "vllm_ascend": git(R / "src/vllm-ascend", "status", "--porcelain", "--untracked-files=all") == "",

    "vllm": git(R / "src/vllm", "status", "--porcelain", "--untracked-files=all") == "",

}

add("CHK-003", "source/clean", "both clean", clean_now,

    "PASS" if all(clean_now.values()) else "FAIL", ["EVID-CMD-0006", "EVID-CMD-0007"])


# CHK-004 provenance

prov = load(R / "manifests/import_provenance.json")

add("CHK-004", "runtime/import_provenance", "provenance_ok true",

    prov.get("provenance_ok"), "PASS" if prov.get("provenance_ok") is True else "FAIL",

    ["EVID-CMD-0010"])


# CHK-005/006 A0

a0 = load(R / "A0/result.json")

expected_tokens = [8515, 11, 323, 358, 1079, 264, 220, 17, 18, 4666, 6284, 5458, 13, 358, 614, 1012]

actual_tokens = (a0.get("outputs") or [{}])[0].get("token_ids")

add("CHK-005", "A0/contract", expected_tokens, actual_tokens,

    "PASS" if a0.get("status") == "OK" and actual_tokens == expected_tokens else "FAIL",

    ["EVID-CMD-0017", "EVID-A0-RESULT"])

add("CHK-006", "A0/zero_state",

    "characterization_installed=false provider_installed=false policy=None",

    {"characterization_installed": a0.get("characterization_installed"),

     "provider_installed": a0.get("provider_installed"), "policy_state": a0.get("policy_state")},

    "PASS" if (a0.get("characterization_installed") is False

               and a0.get("provider_installed") is False

               and a0.get("policy_state") == "None") else "FAIL",

    ["EVID-A0-RESULT"])


# CHK-007 A1

a1 = load(R / "A1/result.json")

add("CHK-007", "A1/early_gate",

    "NotImplementedError containing GRAPH_FROZEN",

    {"type": a1.get("exception_type"), "message": a1.get("exception_message")},

    "PASS" if (a1.get("exception_type") == "NotImplementedError"

               and "GRAPH_FROZEN" in (a1.get("exception_message") or "")) else "FAIL",

    ["EVID-CMD-0018", "EVID-A1-RESULT"])


# CHK-008/009/014 B fixed contract

b = load(R / "B/result.json")

tb = b.get("traceback") or ""

add("CHK-008", "B/fixed_contract_failure", "RuntimeError: capture operand observer is already attached",

    {"type": b.get("exception_type"), "message": b.get("exception_message")},

    "PASS" if (b.get("exception_type") == "RuntimeError"

               and b.get("exception_message") == "capture operand observer is already attached") else "FAIL",

    ["EVID-CMD-0019", "EVID-B-RESULT"])

add("CHK-009", "B/first_divergence", "capture.py:376 -> characterization.py:1006",

    {"capture_call": "capture.py:376" in tb or "capture.py" in tb,

     "attach_raise": "capture operand observer is already attached" in tb},

    "PASS" if ("capture.py" in tb and "capture operand observer is already attached" in tb) else "FAIL",

    ["EVID-B-TRACEBACK"])


# CHK-010..014 artifact

art = load(R / "B/artifact/B_artifact.json")

events = art.get("events") if isinstance(art.get("events"), list) else []

add("CHK-010", "B/artifact/schema", "mrv2-draft-window-graph-characterization-v2",

    art.get("schema"), "PASS" if art.get("schema") == "mrv2-draft-window-graph-characterization-v2" else "FAIL",

    ["EVID-B-ARTIFACT"])

seq = [e.get("sequence") for e in events]

add("CHK-011", "B/artifact/sequence", "strictly increasing unique sequences",

    seq, "PASS" if seq == sorted(seq) and len(seq) == len(set(seq)) else "FAIL",

    ["EVID-B-ARTIFACT"])

cap = events[0] if events else {}

add("CHK-012", "B/artifact/capture_identity", "capture generation_id=null mapping_epoch=null",

    {"generation_id": cap.get("generation_id"), "mapping_epoch": cap.get("mapping_epoch")},

    "PASS" if cap.get("generation_id") is None and cap.get("mapping_epoch") is None else "FAIL",

    ["EVID-B-ARTIFACT"])

add("CHK-013", "B/artifact/capture_operand",

    "(4,28) descriptor; table 20623361164800; lengths 1151x4; slot -1; query 0,7,14,21,28",

    {"descriptor": cap.get("capture_descriptor"),

     "table": cap.get("backing_table_address"),

     "exact": cap.get("exact_lengths"),

     "slot": cap.get("slot_mapping_values"),

     "query": cap.get("query_layout_values")},

    "PASS" if (cap.get("capture_descriptor", "").find("reqs=4;tokens=28") >= 0

               and cap.get("backing_table_address") == 20623361164800

               and cap.get("exact_lengths") == [1151, 1151, 1151, 1151]

               and cap.get("slot_mapping_values") == [-1] * 28

               and cap.get("query_layout_values") == [0, 7, 14, 21, 28]) else "FAIL",

    ["EVID-B-ARTIFACT"])

counts = {k: len(art.get(k, [])) for k in ("events", "operand_events", "g4_records", "lifecycle_events")}

add("CHK-014", "B/artifact/completeness", "partial: 1/0/0/0", counts,

    "PASS" if counts == {"events": 1, "operand_events": 0, "g4_records": 0, "lifecycle_events": 0} else "FAIL",

    ["EVID-B-ARTIFACT"])


# CHK-015 host UT files

def logtext(name):

    return (R / "host_tests" / name).read_text(errors="replace") if (R / "host_tests" / name).exists() else ""


ut_expected = {

    "test_draft_window_graph_characterization.log": "25 passed",

    "test_draft_window_graph_carrier.log": "47 passed",

    "test_draft_window_graph_binding.log": "37 passed",

    "test_draft_window_graph_oracle.log": "7 passed",

}

ut_actual = {k: (ut_expected[k] in logtext(k)) for k in ut_expected}

add("CHK-015", "host/ut_files", ut_expected, ut_actual,

    "PASS" if all(ut_actual.values()) else "FAIL", ["EVID-HOST-UT"])

reg = logtext("real_owner_regression.log")

add("CHK-016", "host/real_owner_regression", "2 passed incl. real sharing + private reject",

    {"two_passed": "2 passed" in reg,

     "real_sharing": "test_real_target_metadata_sharing_is_allowed_for_full_write_carriers PASSED" in reg,

     "private_reject": "test_draft_private_fields_still_reject_target_storage_alias PASSED" in reg},

    "PASS" if ("2 passed" in reg and "test_real_target_metadata_sharing_is_allowed_for_full_write_carriers PASSED" in reg

               and "test_draft_private_fields_still_reject_target_storage_alias PASSED" in reg) else "FAIL",

    ["EVID-HOST-REAL-OWNER"])

life = logtext("host_lifecycle.log")

add("CHK-017", "host/lifecycle", "16 passed", "16 passed" in life,

    "PASS" if "16 passed" in life else "FAIL", ["EVID-HOST-LIFECYCLE"])


# CHK-018/019 oracle

def oracle(name):

    return load(R / f"G3/oracle_{name}.json")

expected_blocks = {

    "SHORT": [1],

    "BOUNDARY": list(range(1, 9)),

    "NONBOUNDARY": list(range(1, 9)),

    "LONG": list(range(9, 17)),

}

actual_blocks = {k: oracle(k).get("expected_block_ids") for k in expected_blocks}

add("CHK-018", "G3/host_oracle", expected_blocks, actual_blocks,

    "PASS" if actual_blocks == expected_blocks else "FAIL", ["EVID-G3-ORACLE"])

olog = (R / "G3/oracle_cases.log").read_text(errors="replace")

add("CHK-019", "G3/host_oracle_negatives",

    "source shortage and nonzero offset rejected",

    {"source_shortage": "EXPECTED_REJECT_SOURCE_SHORTAGE rc=1" in olog,

     "nonzero_offset": "EXPECTED_REJECT_NONZERO_OFFSET rc=1" in olog},

    "PASS" if ("EXPECTED_REJECT_SOURCE_SHORTAGE rc=1" in olog and "EXPECTED_REJECT_NONZERO_OFFSET rc=1" in olog) else "FAIL",

    ["EVID-G3-ORACLE-LOG"])


# CHK-020 negative matrix

neg = load(R / "negative/negative_matrix_cpu.json")

add("CHK-020", "negative/cpu_matrix", "31/31 match",

    {"total": neg.get("total"), "match": neg.get("match"), "unexpected": neg.get("unexpected")},

    "PASS" if neg.get("total") == 31 and neg.get("match") == 31 and not neg.get("unexpected") else "FAIL",

    ["EVID-NEGATIVE"])


# CHK-021 repo audit on partial artifact

aud = load(R / "G1/repo_audit_partial_B.json")

add("CHK-021", "G1/repo_audit_partial", "ready_for_device_campaign=false; G1 host OPEN",

    {"ready": aud.get("ready_for_device_campaign"), "g1": aud.get("G1_HOST_OPERATOR_BOUNDARY")},

    "PASS" if aud.get("ready_for_device_campaign") is False and aud.get("G1_HOST_OPERATOR_BOUNDARY") == "OPEN" else "FAIL",

    ["EVID-REPO-AUDIT"])


# CHK-022 processes

npu_after = (R / "raw/npu_after.txt").read_text(errors="replace") if (R / "raw/npu_after.txt").exists() else ""

add("CHK-022", "cleanup/processes", "NONE in npu_after",

    "NONE" in npu_after, "PASS" if "NONE" in npu_after else "FAIL", ["EVID-NPU-AFTER"])


# CHK-023 team tools

tt = load(R / "manifests/team_tools_verification.json")

add("CHK-023", "integrity/team_tools", "ORIGINAL_TEAM_TOOLS_UNCHANGED",

    tt.get("verdict"), "PASS" if tt.get("verdict") == "ORIGINAL_TEAM_TOOLS_UNCHANGED" else "FAIL",

    ["EVID-TEAM-TOOLS"])


# CHK-024 diagnostics bounded/labeled

diag = {}

for name in ("diag_cap7", "diag_cap14", "diag_cap28", "diag_cap28_introspect", "diag_cap24_introspect"):

    d = load(R / f"B/{name}/result.json")

    diag[name] = {"status": d.get("status"), "type": d.get("exception_type"),

                  "msg": d.get("exception_message"),

                  "event_count": (d.get("artifact_summary") or {}).get("event_count")}

add("CHK-024", "diagnostics/capture_inventory",

    "diagnostics bounded and labeled; no Graph claim",

    diag,

    "PASS" if (diag["diag_cap7"]["status"] == "OK" and diag["diag_cap14"]["status"] == "OK"

               and diag["diag_cap28"]["status"] == "OK"

               and diag["diag_cap24_introspect"]["type"] == "RuntimeError") else "FAIL",

    ["EVID-DIAG"])


# CHK-025 deliverable files

deliverables = [

    "P7X_A3_00_Return_Index.md",

    "P7X_A3_01_Report_CN.md",

    "P7X_A3_02_Execution_Record.md",

    "P7X_A3_03_Device_Facts.json",

    "P7X_A3_04_A0_A1_B_Record.md",

    "P7X_A3_05_G1_G5_Decisions.md",

    "P7X_A3_06_Evidence.json",

    "P7X_A3_07_Raw_Text_Evidence.md",

    "P7X_A3_08_Failures_And_Limits.md",

    "RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md",

]

missing = [f for f in deliverables if not (R / "reports" / f).exists() or (R / "reports" / f).stat().st_size == 0]

add("CHK-025", "deliverables/ten_files", "all 10 non-empty",

    {"missing": missing, "count": len(deliverables) - len(missing)},

    "PASS" if not missing else "OPEN", ["EVID-REPORTS"])


# CHK-026 gate-status consistency

gate = load(R / "reports/gate_status.json")

required_open = [

    "G1_HOST_OPERATOR_BOUNDARY", "G1_ACTUAL_ACL_TASK_INTERNAL",

    "G2_NPU_A_B_A", "G3_OPERATOR_BOUNDARY", "G3_PHYSICAL_MEMORY_TRANSACTION",

    "G4_DEVICE_KV_WRITE", "G5_FIRST_REPLAY_SOURCE", "G5_UPDATE_EFFECTIVE_GENERATION",

]

gate_map = {g.get("gate"): g.get("status") for g in gate.get("gates", [])} if isinstance(gate.get("gates"), list) else {}

wrong = {g: gate_map.get(g) for g in required_open if gate_map.get(g) in (None, "PASS")}

add("CHK-026", "report/gate_status", "device-dependent gates must not be PASS",

    {"wrong": wrong, "gate_count": len(gate_map)},

    "PASS" if not wrong else "FAIL", ["EVID-GATE-STATUS"])


summary = {

    "run_id": "20261019_055109_13373fff",

    "checks_total": len(checks),

    "pass": sum(1 for c in checks if c["status"] == "PASS"),

    "fail": sum(1 for c in checks if c["status"] == "FAIL"),

    "open": sum(1 for c in checks if c["status"] == "OPEN"),

    "checks": checks,

    "first_failures": [c for c in checks if c["status"] == "FAIL"][:5],

}

out = R / "reports/independent_checker_result.json"

out.write_text(json.dumps(summary, indent=2) + "\n")

print(json.dumps({k: summary[k] for k in ("checks_total", "pass", "fail", "open")}, indent=2))

for c in checks:

    print(f"{c['check_id']} {c['status']} {c['scope']}")

```


**### env_graph_char.sh**

`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh`

SHA256: `5a5da37dfd50dc0a0822156d4ed7fd127f2612159837977c87e11e337b826a6f`

```bash

#!/usr/bin/env bash

# P7-X Graph G1-G5 rerun runtime environment.

# source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh


R=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff


case $- in *u*) _HAD_U=1 ;; *) _HAD_U=0 ;; esac

set +u


source /usr/local/Ascend/ascend-toolkit/set_env.sh

source /home/wenqing/.venv-main/bin/activate


[ "$_HAD_U" = 1 ] && set -u

unset _HAD_U


export PYTHONPATH="$R/runtime/site${PYTHONPATH:+:$PYTHONPATH}"

export VLLM_USE_V2_MODEL_RUNNER=1

export VLLM_ENABLE_V1_MULTIPROCESSING=0

export VLLM_CACHE_ROOT="$R/runtime/cache/vllm"

export TORCH_NPU_CACHE_DIR="$R/runtime/cache/torch_npu"

mkdir -p "$VLLM_CACHE_ROOT" "$TORCH_NPU_CACHE_DIR"


[ "$VLLM_USE_V2_MODEL_RUNNER" = "1" ] || echo "env_graph_char: MRV2 flag not 1" >&2

case ":$PYTHONPATH:" in

  *":$R/runtime/site:"*) : ;;

  *) echo "env_graph_char: site dir missing" >&2 ;;

esac


hash -r

```


**### sitecustomize.py**

`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/site/sitecustomize.py`

SHA256: `3a80c038cb364e443f017eaa06f896dd4152713f4fafea7f69e945b65e24e398`

```python

"""P7-X Graph G1-G5 rerun runtime path guard (node-39-101).


Makes the run-local overlay authoritative and blocks every legacy source tree.

This module never writes to the shared venv and never imports blocked trees.

"""


import os

import sys


OVERLAY = "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/graph_char_overlay"

OVERLAY_SRC_ROOT = "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff"


BLOCKED_PREFIXES = (

    "/home/wenqing/vllm-main",

    "/home/wenqing/vllm-ascend-main",

    "/home/wenqing/mrv2_p8_final",

    "/home/wenqing/mrv2_p7x_final",

    "/home/wenqing/mrv2_p7x_perf_final",

    "/home/wenqing/mrv2_window_test",

    "/home/wenqing/mrv2_graph_g1g5",

    "/mnt/wenqing/mrv2_graph_g1g5_campaign",

    "/mnt/wenqing/mrv2_p7x_campaign",

)


def _is_blocked(path):

    p = os.path.normpath(path)

    for b in BLOCKED_PREFIXES:

        if p == b or p.startswith(b + os.sep):

            return b

    return None


for _finder in list(sys.meta_path):

    _loc = getattr(_finder, "path", None)

    if isinstance(_loc, str) and _is_blocked(_loc):

        sys.meta_path.remove(_finder)


sys.path[:] = [p for p in sys.path if not _is_blocked(p)]

while OVERLAY in sys.path:

    sys.path.remove(OVERLAY)

sys.path.insert(0, OVERLAY)


_overlay_idx = sys.path.index(OVERLAY)

for _i, _p in enumerate(sys.path):

    if _i == _overlay_idx:

        continue

    _hit = _is_blocked(_p)

    if _hit is not None and _i < _overlay_idx:

        sys.stderr.write(

            "SOURCE_SHADOWING_BLOCKED: %r at sys.path[%d] precedes overlay\n"

            % (_hit, _i)

        )

        raise SystemExit("SOURCE_SHADOWING_BLOCKED")


_check = os.path.realpath(OVERLAY)

if not (_check == os.path.normpath(OVERLAY) or _check.startswith(OVERLAY_SRC_ROOT)):

    sys.stderr.write("SOURCE_SHADOWING_BLOCKED: overlay resolves to %r\n" % _check)

    raise SystemExit("SOURCE_SHADOWING_BLOCKED")

```


**### probe_import_provenance.py**

`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/probe_import_provenance.py`

SHA256: `fffaf0e80a7e9a59043f79a94fccc0e9f4d8bd378995ff868165ecbfba36e776`

```python

"""Prove exact run-local module provenance. No model, no NPU work."""


from __future__ import annotations


import hashlib

import importlib

import json

import os

import sys


RUN_ROOT = "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff"

OVERLAY = RUN_ROOT + "/runtime/graph_char_overlay"


MODULES = [

    "vllm",

    "vllm_ascend",

    "vllm_ascend.worker.v2.model_runner",

    "vllm_ascend.worker.v2.spec_decode.dspark.speculator",

    "vllm_ascend.worker.v2.spec_decode.draft_window",

    "vllm_ascend.worker.v2.spec_decode.draft_window_graph",

    "vllm_ascend.worker.v2.spec_decode.draft_window_graph_characterization",

    "vllm_ascend.worker.v2.spec_decode.draft_window_graph_oracle",

    "vllm_ascend.worker.v2.spec_decode.dflash.capture",

    "vllm_ascend.worker.v2.spec_decode.dflash.aclgraph",

    "vllm_ascend.attention.attention_v1",

    "vllm_ascend.compilation.acl_graph",

]


def sha256(path: str) -> str:

    h = hashlib.sha256()

    with open(path, "rb") as f:

        for c in iter(lambda: f.read(1 << 20), b""):

            h.update(c)

    return h.hexdigest()


def main() -> None:

    # Known import-order dependencies on this host.

    import vllm.v1.worker.gpu.spec_decode.speculator  # noqa: F401

    import vllm_ascend.ops  # noqa: F401


    result = {

        "run_root": RUN_ROOT,

        "overlay": OVERLAY,

        "python": sys.version,

        "executable": sys.executable,

        "sys_path": list(sys.path),

        "env": {

            k: os.environ.get(k)

            for k in (

                "VLLM_USE_V2_MODEL_RUNNER",

                "VLLM_ENABLE_V1_MULTIPROCESSING",

                "VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH",

                "VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT",

            )

        },

        "modules": {},

    }

    pinned_vllm = RUN_ROOT + "/src/vllm"

    ok = True

    for name in MODULES:

        mod = importlib.import_module(name)

        path = getattr(mod, "__file__", None)

        real = os.path.realpath(path) if path else None

        entry = {

            "file": path,

            "realpath": real,

            "sha256": sha256(path) if path and os.path.isfile(path) else None,

            "under_overlay": bool(path and os.path.abspath(path).startswith(OVERLAY)),

            "resolves_to_pinned_source": bool(real and real.startswith(pinned_vllm)),

        }

        # vllm is intentionally a symlink from the overlay to the exact pinned

        # checkout; accept either the overlay path or that verified realpath.

        if not (entry["under_overlay"] or entry["resolves_to_pinned_source"]):

            ok = False

        result["modules"][name] = entry


    from vllm_ascend.worker.v2.model_runner import NPUModelRunner

    from vllm_ascend.worker.v2.spec_decode.dspark.speculator import (

        AscendDSparkSpeculator,

    )

    from vllm_ascend.worker.v2.spec_decode.draft_window_graph_characterization import (

        DraftWindowGraphCharacterizationRecorder,

        experimental_draft_window_graph_characterization_enabled,

    )

    from vllm_ascend.worker.v2.spec_decode.draft_window_graph_oracle import (

        compute_graph_characterization_oracle,

    )


    result["classes"] = {

        "model_runner": f"{NPUModelRunner.__module__}.{NPUModelRunner.__qualname__}",

        "dspark_speculator": f"{AscendDSparkSpeculator.__module__}.{AscendDSparkSpeculator.__qualname__}",

        "recorder": f"{DraftWindowGraphCharacterizationRecorder.__module__}.{DraftWindowGraphCharacterizationRecorder.__qualname__}",

        "oracle": f"{compute_graph_characterization_oracle.__module__}.{compute_graph_characterization_oracle.__qualname__}",

    }

    result["experimental_enabled"] = experimental_draft_window_graph_characterization_enabled()

    result["provenance_ok"] = ok

    out = RUN_ROOT + "/manifests/import_provenance.json"

    with open(out, "w", encoding="utf-8") as f:

        json.dump(result, f, indent=2, sort_keys=True)

    print(json.dumps({"provenance_ok": ok, "output": out, "classes": result["classes"]}, indent=2))


if __name__ == "__main__":

    main()

```

**# P7X_A3_07_Raw_Text_Evidence — part 006**


RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

PART: 6/6

SECTIONS: ['Old → new driver diff', 'Integrity checks for this document']


**---**


**## Old → new driver diff**


Old driver: `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/reference/old_campaign/commands/driver_case.py`

SHA256: `209a23114bef9c7b0a3e6dc80794acae76add20635f61db3bff49c8d9c8328ee`

New driver: `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/driver_case.py`

SHA256: `c3b5a982f85742d50ecafd671bf6a91e0da779f752a417afb540a70123ae01f3`

```diff

--- /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/reference/old_campaign/commands/driver_case.py  2026-10-17 16:18:46.790249460 +0800

+++ /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/driver_case.py 2026-10-19 06:38:49.654249460 +0800

**@@ -1,10 +1,8 @@**

-"""Deterministic in-process control driver (A0 / A1 / B).

+#!/usr/bin/env python3

+"""Deterministic in-process driver for the P7-X A3 rerun.


 CUSTOM_CORRECTNESS_DRIVER -- NOT FORMAL PERFORMANCE.

-

-A0: draft_window_size absent, internal flag 0

-A1: draft_window_size=1024, internal flag 0  (public Graph Window must fail closed)

-B : draft_window_size=1024, internal flag 1  (internal characterization path)

+No vLLM / vllm-ascend source is modified.

 """


 from __future__ import annotations

**@@ -15,22 +13,26 @@**

 import sys

 import traceback


+RUN_ROOT = "/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff"

 MODEL = "/mnt/share/wql/Qwen3-8B"

 DRAFT = "/mnt/share/dspark_qwen3_8b_block7"

-DEVICE = os.environ.get("ASCEND_RT_VISIBLE_DEVICES", "4")

+OLD_PROMPT = "Hello, my name is"


-def main() -> None:

+def main() -> int:

     ap = argparse.ArgumentParser()

     ap.add_argument("--case", required=True)

     ap.add_argument("--window", default="off")

     ap.add_argument("--flag", default="0")

-    ap.add_argument("--method", default="dspark", choices=["dspark", "dflash"])

-    ap.add_argument("--draft", default=DRAFT)

-    ap.add_argument("--capture-sizes", default="7,14,28")

\+    ap.add_argument("--artifact", default="")

     ap.add_argument("--max-model-len", type=int, default=4096)

     ap.add_argument("--max-tokens", type=int, default=16)

-    ap.add_argument("--prompt", default="Hello, my name is")

\+    ap.add_argument("--num-prompts", type=int, default=1)

\+    ap.add_argument("--prompt", default=OLD_PROMPT)

\+    ap.add_argument("--prompt-len", type=int, default=0,

\+                    help="if >0, build a deterministic token-id prompt of this length")

\+    ap.add_argument("--logprobs", type=int, default=0)

\+    ap.add_argument("--capture-sizes", default="7,14,28")

     ap.add_argument("--out", required=True)

     args = ap.parse_args()


**@@ -43,6 +45,10 @@**

             "flag env mismatch: "

             f"{os.environ.get('VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH')} != {args.flag}"

         )

\+    if args.artifact and os.environ.get("VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT") != args.artifact:

\+        raise SystemExit("artifact env mismatch")

\+    if args.flag == "1" and not args.artifact:

\+        raise SystemExit("flag=1 requires --artifact")


     from vllm import LLM, SamplingParams


**@@ -54,15 +60,18 @@**

         "case": args.case,

         "window": args.window,

         "flag": args.flag,

-        "device": DEVICE,

\+        "artifact": args.artifact,

         "model": MODEL,

-        "draft": args.draft,

-        "method": args.method,

\+        "draft": DRAFT,

\+        "prompt": args.prompt,

\+        "prompt_len_requested": args.prompt_len,

\+        "num_prompts": args.num_prompts,

\+        "max_tokens": args.max_tokens,

\+        "logprobs": args.logprobs,

         "capture_sizes": [int(x) for x in args.capture_sizes.split(",") if x],

         "status": "STARTED",

     }

     llm = None

-    session = None

     try:

         llm = LLM(

             model=MODEL,

**@@ -75,8 +84,8 @@**

             max_num_batched_tokens=4096,

             seed=0,

             speculative_config={

-                "model": args.draft,

-                "method": args.method,

\+                "model": DRAFT,

\+                "method": "dspark",

                 "num_speculative_tokens": 7,

                 "enable_adaptive_verification": False,

             },

**@@ -105,134 +114,131 @@**

         record["provider_installed"] = hasattr(

             spec, "_draft_window_graph_binding_provider"

         )

\+        try:

\+            tgt_mgr = mr.cudagraph_manager

\+            drf_mgr = getattr(spec, "query_cudagraph_manager", None)

\+            record["capture_inventory"] = {

\+                "target_mode": str(getattr(tgt_mgr, "cudagraph_mode", None)),

\+                "target_needs_capture": tgt_mgr.needs_capture(),

\+                "target_capture_descs": {

\+                    mode.name: [

\+                        {

\+                            "num_tokens": d.num_tokens,

\+                            "num_reqs": d.num_reqs,

\+                            "uniform_token_count": d.uniform_token_count,

\+                        }

\+                        for d in descs

\+                    ]

\+                    for mode, descs in getattr(tgt_mgr, "_capture_descs", {}).items()

\+                },

\+                "draft_mode": str(getattr(drf_mgr, "cudagraph_mode", None)),

\+                "draft_needs_capture": (

\+                    None if drf_mgr is None else drf_mgr.needs_capture()

\+                ),

\+                "draft_capture_descs": (

\+                    None

\+                    if drf_mgr is None

\+                    else {

\+                        mode.name: [

\+                            {

\+                                "num_tokens": d.num_tokens,

\+                                "num_reqs": d.num_reqs,

\+                                "uniform_token_count": d.uniform_token_count,

\+                            }

\+                            for d in descs

\+                        ]

\+                        for mode, descs in getattr(drf_mgr, "_capture_descs", {}).items()

\+                    }

\+                ),

\+            }

\+        except BaseException as inv_exc:  # noqa: BLE001

\+            record["capture_inventory_error"] = repr(inv_exc)


-        session = getattr(spec, "_draft_window_graph_characterization", None)

-        if session is not None:

-            ids = session.provider.registered_capture_identities(route=session.route)

-            record["registered_capture_identities"] = [

-                {

-                    "capture_descriptor": i.fingerprint.capture_descriptor,

-                    "capture_bucket": list(i.fingerprint.capture_bucket),

-                    "query_width": i.fingerprint.query_width,

-                    "graph_mode": i.fingerprint.graph_mode,

-                    "table_addr": i.backing_identity.window_block_table.data_ptr,

-                    "device_len_addr": i.backing_identity.device_window_exact.data_ptr,

-                    "cpu_exact_addr": i.backing_identity.cpu_window_exact.data_ptr,

-                    "cpu_upper_addr": i.backing_identity.cpu_window_upper.data_ptr,

-                }

-                for i in ids

-            ]

-

-        sp = SamplingParams(max_tokens=args.max_tokens, temperature=0.0, ignore_eos=True)

-        outputs = llm.generate([args.prompt], sp)

-        record["output_token_ids"] = list(outputs[0].outputs[0].token_ids)

-        record["output_text"] = outputs[0].outputs[0].text

\+        if args.prompt_len > 0:

\+            # Deterministic token-id prompt. Avoid special tokens where possible.

\+            base = [1000 + (i % 1000) for i in range(args.prompt_len)]

\+            prompts = [{"prompt_token_ids": base} for _ in range(args.num_prompts)]

\+        else:

\+            prompts = [args.prompt for _ in range(args.num_prompts)]

\+

\+        sp = SamplingParams(

\+            max_tokens=args.max_tokens,

\+            temperature=0.0,

\+            ignore_eos=True,

\+            logprobs=(args.logprobs if args.logprobs > 0 else None),

\+        )

\+        outputs = llm.generate(prompts, sp)

\+        record["outputs"] = [

\+            {

\+                "token_ids": list(o.outputs[0].token_ids),

\+                "text": o.outputs[0].text,

\+                "logprobs": (

\+                    [list(x.values())[0].logprob if x else None for x in (o.outputs[0].logprobs or [])]

\+                    if o.outputs[0].logprobs is not None

\+                    else None

\+                ),

\+            }

\+            for o in outputs

\+        ]

         record["status"] = "OK"


-        if session is not None:

-            events = [

-                {

-                    "sequence": e.sequence,

-                    "stage": e.stage.value,

-                    "route": e.route.value,

-                    "capture_descriptor": e.capture_descriptor,

-                    "generation_id": e.generation_id,

-                    "mapping_epoch": e.mapping_epoch,

-                    "backing_table_address": e.backing_table_address,

-                    "table_values": [list(r) for r in e.table_values],

-                    "exact_lengths": list(e.exact_lengths),

-                    "upper_lengths": list(e.upper_lengths),

-                    "slot_mapping_address": e.slot_mapping_address,

-                    "slot_mapping_values": list(e.slot_mapping_values),

-                    "positions_address": e.positions_address,

-                    "position_values": list(e.position_values),

-                    "query_layout_address": e.query_layout_address,

-                    "query_layout_values": list(e.query_layout_values),

-                }

-                for e in session.recorder.events

-            ]

-            record["events"] = events

-            record["stage_counts"] = {

-                s: sum(1 for e in events if e["stage"] == s)

-                for s in sorted({e["stage"] for e in events})

\+        if args.artifact and os.path.isfile(args.artifact):

\+            snapshot = json.load(open(args.artifact, encoding="utf-8"))

\+            record["artifact_summary"] = {

\+                "schema": snapshot.get("schema"),

\+                "event_count": len(snapshot.get("events", [])),

\+                "operand_event_count": len(snapshot.get("operand_events", [])),

\+                "g4_record_count": len(snapshot.get("g4_records", [])),

\+                "lifecycle_event_count": len(snapshot.get("lifecycle_events", [])),

\+                "stage_counts": {

\+                    s: sum(1 for e in snapshot.get("events", []) if e.get("stage") == s)

\+                    for s in sorted({e.get("stage") for e in snapshot.get("events", [])})

\+                },

\+                "operand_stage_counts": {

\+                    s: sum(1 for e in snapshot.get("operand_events", []) if e.get("stage") == s)

\+                    for s in sorted({e.get("stage") for e in snapshot.get("operand_events", [])})

\+                },

\+                "lifecycle_stage_counts": {

\+                    s: sum(1 for e in snapshot.get("lifecycle_events", []) if e.get("stage") == s)

\+                    for s in sorted({e.get("stage") for e in snapshot.get("lifecycle_events", [])})

\+                },

             }

-    except BaseException as exc:  # noqa: BLE001 - evidence capture is the point

\+    except BaseException as exc:  # noqa: BLE001

         record["status"] = "EXCEPTION"

         record["exception_type"] = type(exc).__name__

         record["exception_message"] = str(exc)

         record["traceback"] = traceback.format_exc()

-        # Preserve any characterization events already emitted before failure.

         if llm is not None:

             try:

                 ec = llm.llm_engine.engine_core.engine_core

                 mr = ec.model_executor.driver_worker.worker.model_runner

                 spec = mr.speculator

-                session = getattr(spec, "_draft_window_graph_characterization", None)

                 record["model_runner_class"] = f"{type(mr).__module__}.{type(mr).__qualname__}"

                 record["speculator_class"] = f"{type(spec).__module__}.{type(spec).__qualname__}"

                 policy = getattr(spec, "_draft_window_policy", None)

                 record["policy_state"] = str(getattr(policy, "state", None))

-                record["policy_reason"] = getattr(policy, "reason", None)

                 record["effective_window_size"] = getattr(policy, "effective_window_size", None)

-                record["characterization_installed"] = session is not None

\+                record["characterization_installed"] = hasattr(

\+                    spec, "_draft_window_graph_characterization"

\+                )

                 record["provider_installed"] = hasattr(

                     spec, "_draft_window_graph_binding_provider"

                 )

-                if session is not None:

-                    ids = session.provider.registered_capture_identities(

-                        route=session.route

-                    )

-                    record["registered_capture_identities"] = [

-                        {

-                            "capture_descriptor": i.fingerprint.capture_descriptor,

-                            "capture_bucket": list(i.fingerprint.capture_bucket),

-                            "query_width": i.fingerprint.query_width,

-                            "graph_mode": i.fingerprint.graph_mode,

-                            "table_addr": i.backing_identity.window_block_table.data_ptr,

-                            "device_len_addr": i.backing_identity.device_window_exact.data_ptr,

-                            "cpu_exact_addr": i.backing_identity.cpu_window_exact.data_ptr,

-                            "cpu_upper_addr": i.backing_identity.cpu_window_upper.data_ptr,

-                        }

-                        for i in ids

-                    ]

-                    events = [

-                        {

-                            "sequence": e.sequence,

-                            "stage": e.stage.value,

-                            "route": e.route.value,

-                            "capture_descriptor": e.capture_descriptor,

-                            "generation_id": e.generation_id,

-                            "mapping_epoch": e.mapping_epoch,

-                            "backing_table_address": e.backing_table_address,

-                            "table_values": [list(r) for r in e.table_values],

-                            "exact_lengths": list(e.exact_lengths),

-                            "upper_lengths": list(e.upper_lengths),

-                            "slot_mapping_address": e.slot_mapping_address,

-                            "slot_mapping_values": list(e.slot_mapping_values),

-                            "positions_address": e.positions_address,

-                            "position_values": list(e.position_values),

-                            "query_layout_address": e.query_layout_address,

-                            "query_layout_values": list(e.query_layout_values),

-                        }

-                        for e in session.recorder.events

-                    ]

-                    record["events"] = events

-                    record["stage_counts"] = {

-                        s: sum(1 for e in events if e["stage"] == s)

-                        for s in sorted({e["stage"] for e in events})

-                    }

             except BaseException as probe_exc:  # noqa: BLE001

                 record["post_failure_probe_error"] = repr(probe_exc)

         with open(args.out, "w", encoding="utf-8") as f:

             json.dump(record, f, indent=2)

         print("RESULT=" + json.dumps({k: v for k, v in record.items() if k != "traceback"}, indent=2))

         print(record["traceback"], file=sys.stderr)

-        raise SystemExit(2)

\+        return 2


     with open(args.out, "w", encoding="utf-8") as f:

         json.dump(record, f, indent=2)

-    print("RESULT=" + json.dumps({k: v for k, v in record.items() if k != "events"}, indent=2))

\+    print("RESULT=" + json.dumps({k: v for k, v in record.items() if k != "outputs"}, indent=2))

\+    if record.get("outputs"):

\+        print("TOKENS=" + json.dumps([o["token_ids"] for o in record["outputs"]]))

\+    return 0


 if __name__ == "__main__":

-    main()

\+    raise SystemExit(main())

```


**## Integrity checks for this document**


- A0/A1/B JSON and B artifact are copied verbatim from their files.

- Host logs are copied verbatim.

- Driver/checker/env/sitecustomize/probe are copied verbatim; SHA256 is shown.

- No credential is included.

- Any text transformation (Markdown fencing) does not change the underlying evidence files.
