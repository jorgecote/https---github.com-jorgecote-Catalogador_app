# setup_dev_env.ps1
# Recrea el entorno virtual aislado e instala dependencias desde requirements.txt
# Uso: .\setup_dev_env.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".venv"
$ReqFile = Join-Path $ProjectRoot "requirements.txt"
$PythonCmd = $null

Write-Host ""
Write-Host "=== ByteBox Catalogador — Setup entorno de desarrollo ===" -ForegroundColor Cyan
Write-Host "Proyecto: $ProjectRoot"
Write-Host ""

foreach ($cmd in @("python", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PythonCmd = $cmd
        break
    }
}

if (-not $PythonCmd) {
    Write-Host "ERROR: No se encontró Python. Instala Python 3.10+ y vuelve a ejecutar." -ForegroundColor Red
    exit 1
}

$pyVersion = & $PythonCmd --version 2>&1
Write-Host "Python detectado: $pyVersion ($PythonCmd)" -ForegroundColor Green

if (-not (Test-Path $ReqFile)) {
    Write-Host "ERROR: No se encontró requirements.txt en $ProjectRoot" -ForegroundColor Red
    exit 1
}

if (Test-Path $VenvPath) {
    Write-Host ""
    Write-Host "Eliminando entorno anterior (.venv)..." -ForegroundColor Yellow
    Write-Host "  Cierra otras terminales que usen este venv si la eliminación falla."

    try {
        Remove-Item -Path $VenvPath -Recurse -Force
        Write-Host "  Entorno anterior eliminado." -ForegroundColor Green
    }
    catch {
        Write-Host ""
        Write-Host "ERROR: No se pudo borrar .venv. Posibles causas:" -ForegroundColor Red
        Write-Host "  - Otra terminal tiene activado el venv"
        Write-Host "  - OneDrive está sincronizando la carpeta"
        Write-Host "  - Un proceso Python sigue en ejecución"
        Write-Host ""
        Write-Host "Detalle: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "No había entorno .venv previo. Se creará uno nuevo." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Creando entorno virtual (.venv --copies)..." -ForegroundColor Cyan
& $PythonCmd -m venv .venv --copies

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló la creación del entorno virtual." -ForegroundColor Red
    exit 1
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: No se generó Scripts\python.exe en .venv" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Actualizando pip..." -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip

Write-Host ""
Write-Host "Instalando dependencias desde requirements.txt..." -ForegroundColor Cyan
Write-Host "(torch CPU + transformers pueden tardar varios minutos)"
& $VenvPython -m pip install -r $ReqFile

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Falló la instalación de dependencias." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Verificando paquetes clave..." -ForegroundColor Cyan
& $VenvPython -c "import streamlit, torch, transformers, cv2, PIL; print('OK:', 'torch', torch.__version__, '| streamlit', streamlit.__version__)"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ADVERTENCIA: Algún paquete no importa correctamente." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== Entorno listo ===" -ForegroundColor Green
Write-Host ""
Write-Host "Activar entorno:" -ForegroundColor White
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Ejecutar la app:" -ForegroundColor White
Write-Host "  cd mi_proyecto_streamlit"
Write-Host "  streamlit run app.py"
Write-Host ""
Write-Host "Descargar modelos IA (CLIP/BLIP) si Hugging Face esta bloqueado:" -ForegroundColor White
Write-Host "  python download_model_weights.py --model clip --insecure"
Write-Host "  (o: download_model_weights.bat --model clip --insecure)"
Write-Host ""
