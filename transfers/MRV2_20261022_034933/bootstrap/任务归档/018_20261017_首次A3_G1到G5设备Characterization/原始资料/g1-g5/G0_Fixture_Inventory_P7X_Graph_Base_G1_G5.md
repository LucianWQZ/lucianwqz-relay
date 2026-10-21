# G0 Fixture Inventory — P7-X Graph Base G1–G5

Date: 2026-10-17  
Host: node-39-101 (Ascend A3, 16 logical dies, CANN 9.1.0, driver 26.0.rc1)

## Selected runtime fixture

| Item | Value |
|---|---|
| Main model | `/mnt/share/wql/Qwen3-8B` (bf16, complete 5-shard safetensors) |
| Draft model | `/mnt/share/dspark_qwen3_8b_block7` (DSpark, `Qwen3DSparkModel`) |
| Method | `dspark` |
| K / num_speculative_tokens | 7 |
| Draft query width | 7 (`sample_from_anchor=True` default) |
| Main architecture | Qwen3ForCausalLM, 36 layers, hidden 4096, 32 heads / 8 KV heads (dense GQA 4:1), head_dim 128 |
| Draft architecture | 5 layers, hidden 4096, 32/8 heads, target layers `[1, 9, 17, 25, 33]` |
| Backend | `AscendAttentionBackendImpl` / STANDARD, single dense FIA group |
| Graph mode | `FULL_DECODE_ONLY` (decode descriptors are `FULL`) |
| Window W | 1024; block size 128; capacity 1151 tokens |
| Capture sizes | `[7, 14, 28]` → buckets `(1,7)`, `(2,14)`, `(4,28)` |
| Topology | TP1 DP1 PP1 PCP1 DCP1, SP OFF, DSA-CP OFF, FlashComm OFF, async OFF, prefix OFF |
| NPU count | 1 logical die |
| A3 compatibility | Yes (validated at runtime; PCI `19e5:d803`) |
| Availability | Weights complete and loadable |
| Verdict | **ACCEPT_SELECTED** |

### Selected fixture hashes

| File | SHA256 |
|---|---|
| main `config.json` | `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30` |
| main `model.safetensors.index.json` | `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc` |
| main `tokenizer.json` | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| draft `config.json` | `e470e70a553616f0dce8f783f42cfd25b7bd7dfdcd57ead680a0623040725611` |
| draft `model.safetensors` | `5c922d1f96c8d18dbdf005c40ea99878d9133d70eaa3be4bd1077ee5f2afc1e5` |

Main shard hashes are in `manifests/fixture_hashes.txt`.

## Candidate matrix

| Candidate | Method | Verdict | Reason |
|---|---|---|---|
| `/mnt/share/wql/Qwen3-8B` + `/mnt/share/dspark_qwen3_8b_block7` | dspark | **ACCEPT_SELECTED** | Exact TP1 e2e fixture; dense GQA; complete weights; policy `ELIGIBLE_ON`; runtime identity verified |
| `Qwen3-8B` + `z-lab/Qwen3-8B-DFlash-b16` | dflash | REJECT | Draft directory contains config/code only — no `model.safetensors`; runtime load failed with `Cannot find any model weights` |
| `Qwen3.5-9B` + `/mnt/share/weight/Qwen3.5-9B-DFlash-full` | dflash | REJECT | Target is hybrid linear/full attention (`Qwen3_5ForConditionalGeneration`), not dense GQA direct-prefix; base characterization requires `DENSE_GQA_DIRECT_PREFIX` |
| `Qwen3.8-27B` + `Qwen3.8-27B-DFlash2` | dflash2 | REJECT | `dflash2` is outside the base route set `{dflash, dspark}`; policy rejects unknown methods |
| GLM-5.2 + GLM-5.2-speculator.dspark | dspark | REJECT | TP16 campaign fixture; base characterization requires TP=DP=PP=PCP=DCP=1 |

## Fixture verdict

```text
BASE_G1_G5_FIXTURE = QWEN3_8B + DSPARK_QWEN3_8B_BLOCK7 (TP1)
FIXTURE_RUNTIME_AVAILABLE = YES
FIXTURE_WEIGHTS_COMPLETE = YES
FIXTURE_POLICY = ELIGIBLE_ON
```

The fixture is valid. The positive characterization run failed inside the candidate
code, not because of fixture discovery or weight availability.

Evidence:

- `manifests/fixture.json`
- `manifests/fixture_hashes.txt`
- `negative/B/result.json`
- `negative/B_dflash/result.json`
