# SenseNova Skills Studio — Windows install helper
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File .\scripts\install_studio.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "Repo root: $RepoRoot"

$imageReq = Join-Path $RepoRoot "skills\sn-image-base\requirements.txt"
$studioReq = Join-Path $RepoRoot "requirements-studio.txt"

if (-not (Test-Path $imageReq)) {
    throw "Missing $imageReq — ensure you are in the inner SenseNova-Skills repo (contains skills\sn-image-base)."
}
if (-not (Test-Path $studioReq)) {
    throw "Missing $studioReq"
}

python -m pip install --upgrade pip
python -m pip install -r $imageReq
python -m pip install -r $studioReq -e .

python -c "import gradio; import huggingface_hub; print('gradio', gradio.__version__, '| huggingface_hub', huggingface_hub.__version__)"
python -c "from sn_studio.ui.app import build_app; build_app(); print('sn_studio import OK')"

Write-Host ""
Write-Host "Done. Start Studio with:"
Write-Host "  cd $RepoRoot"
Write-Host "  python -m sn_studio"
