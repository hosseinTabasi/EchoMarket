# QLoRA recipe (journalist-only; not executed on this machine)

Author: Hossein Tabasi.

**State: not run.** This box has no 7B-class GPU and no adapter weights. Do not read this file as evidence that an adapter was trained. v1 remains the prompt-only multi-agent loop (`src/generate.py` templates + slot fill).

## Scope (hard)

- **Journalist role only.** No retail_panic, no red team, no whale, no bot.
- **DEV news restatements only** (E01–E08). Never E09, never E10.
- Targets are human-sourced news sentences / headlines already on the fact card, not social panic.
- Numeric claims in targets must already appear on the matching card.

## Objective

Turn DEV journalist-style restatements of fact cards into a few hundred instruction pairs for a fact-card-conditioned decoder that emits the EchoMarket JSON schema.

## Base models (pick one)

- Qwen2.5-7B-Instruct
- Llama-3.1-8B-Instruct

Train with **Unsloth** (or PEFT + bitsandbytes 4-bit if Unsloth is unavailable).

## Pair construction (DEV, journalist, news)

```
system: contents of prompts/journalist.txt
user:   fact card FC-E0k + event row + "emit JSON only"
target: a critic-legal journalist restatement (human headline or DEV generated news that passed the critic)
```

Augment without leaving the card: function-word synonyms; sentence-order swaps that keep the lead fact first. Do **not** add numerals, dates, quotes, or hashes.

Split pairs 90/10 **by event** if possible. Never leak TEST.

## Hyperparameters

| Name | Value |
|------|-------|
| Method | QLoRA via Unsloth |
| r | 16 |
| lora_alpha | 32 |
| lora_dropout | 0.05 |
| target_modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| epochs | 2–3 |
| learning_rate | 2e-4 |
| max_seq_len | 1024 |
| batch / grad_accum | 2 / 8 (adjust to VRAM) |
| lr_scheduler | cosine, warmup 3% |
| packing | off (fact cards must stay aligned) |

## Example commands (illustrative; not a log of this box)

```bash
python3 scripts/make_pairs.py --role journalist --modality news --split dev --exclude E09,E10 --out data/pairs_journalist_dev.jsonl

python3 train_qlora.py \
  --base Qwen2.5-7B-Instruct \
  --data data/pairs_journalist_dev.jsonl \
  --r 16 --alpha 32 --epochs 3 --lr 2e-4 --max-len 1024 \
  --out adapters/echomarket-journalist-r16

ECHOMARKET_LORA_PATH=adapters/echomarket-journalist-r16 python3 src/run.py --event E01 --condition C
```

After a real GPU run, replace RESULTS.md tables from the new JSON. Until then, Chapter 7 / RESULTS.md stay TO RUN for the adapter, and v1 numbers (when they exist) are prompt-only.

## What would change after a real run

- Journalist Distinct-2 might rise if the adapter leaves template lock without leaving the card.
- Hallucination rate is the number to watch: adapters invent billions. The critic stays mandatory.
- Retail and red-team posts would still come from the prompt-only decoder unless a later protocol amendment says otherwise.
