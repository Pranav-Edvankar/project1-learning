@echo off
echo ============================================================================
echo Project 2: Cross-Platform Large-Model Runtime Launcher (Windows)
echo ============================================================================
set OLLAMA_ORIGINS=*
set OLLAMA_FLASH_ATTENTION=1
set OLLAMA_KV_CACHE_TYPE=q8_0
python "%~dp0hardware_profiler.py"
python "%~dp0runtime_engine.py"