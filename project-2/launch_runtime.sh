#!/usr/bin/env bash
echo "============================================================================"
echo "Project 2: Cross-Platform Large-Model Runtime Launcher (macOS / Linux)"
echo "============================================================================"
export OLLAMA_ORIGINS="*"
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE="q8_0"
python3 "$(dirname "$0")/hardware_profiler.py"
python3 "$(dirname "$0")/runtime_engine.py"