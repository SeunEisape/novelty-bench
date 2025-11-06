# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NoveltyBench is a benchmarking tool for evaluating the diversity and quality of language model outputs. It measures how well models can generate novel, high-quality responses rather than repeating similar patterns. The project includes tools for generating completions, partitioning similar responses, scoring response quality, and analyzing results.

## Key Commands

### Setup
```bash
pip install -e .
```

### Core Evaluation Pipeline

Run the full evaluation pipeline for a model:

1. **Generate responses** from language models:
```bash
python src/inference.py --mode <provider> --model <model-name> --data curated --eval-dir results/curated/<model> --num-generations 10
```
Provider options: `openai`, `together`, `anthropic`, `google`, `cohere`

2. **Partition responses** to group semantically similar outputs:
```bash
python src/partition.py --eval-dir results/curated/<model> --alg classifier
```
Algorithm options: `classifier` (DeBERTa-based), `rouge1`, `bertscore`, `bleu`, `gpt4o` (LLM-based)

3. **Score response quality** using reward model:
```bash
python src/score.py --eval-dir results/curated/<model> --patience 0.8
```

4. **Summarize results** and compute metrics:
```bash
python src/summarize.py --eval-dir results/curated/<model>
```

### Leaderboard Submission

For submitting to the NoveltyBench leaderboard, ensure your evaluation directory contains:
```
evaluation/<date>_<model-name>/
├── nb-curated/
│   ├── scores.jsonl
│   └── summary.json
└── nb-wildchat/
    ├── scores.jsonl
    └── summary.json
```

## Architecture

The evaluation pipeline consists of four main components:

1. **Inference Module** (`src/inference.py`): Interfaces with various LLM providers to generate multiple responses per prompt. Supports concurrent generation with rate limiting.

2. **Partitioning System** (`src/partition.py`): Groups semantically similar responses using multiple algorithms:
   - DeBERTa classifier fine-tuned for generation similarity
   - Traditional metrics (ROUGE, BLEU, BERTScore)
   - LLM-based similarity judgment

3. **Scoring Engine** (`src/score.py`): Evaluates response quality using reward models, with patience parameter to control quality thresholds.

4. **Analysis Tools** (`src/summarize.py`): Computes diversity metrics, quality distributions, and generates visualizations.

## API Key Management

The system expects API keys in text files at the project root:
- `openai-api-key`: For OpenAI models
- `together-api-key`: For Together AI models
- Additional keys follow the pattern `<provider>-api-key`

For Google Vertex AI (Anthropic), authentication uses default Google Cloud credentials.

## Data Organization

```
data/
├── curated.jsonl       # Hand-curated evaluation prompts
└── wildchat-1k.jsonl   # Real-world conversation prompts
```

Results are stored in:
```
results/<dataset>/<model>/
├── generations.jsonl   # Raw model outputs
├── partitions.jsonl    # Similarity groupings
├── scores.jsonl        # Quality scores
└── summary.json        # Final metrics
```

## Dependencies and Environment

Key dependencies:
- `openai`, `anthropic`, `cohere`, `google-genai`: LLM provider SDKs
- `transformers`: For DeBERTa classifier
- `datasets`, `evaluate`: HuggingFace libraries for metrics
- `bert_score`, `rouge-score`: Similarity metrics
- `ruff`: Code formatting (configured in pyproject.toml)

The project uses async operations for efficient API calls with configurable concurrency limits.