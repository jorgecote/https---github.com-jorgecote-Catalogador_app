@echo off
REM Descarga pesos CLIP/BLIP a mi_proyecto_streamlit/model_weights/
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe download_model_weights.py %*
) else (
    python download_model_weights.py %*
)
pause
