#requires -Version 5.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OUTPUT_DIR = Join-Path $SCRIPT_DIR "generated"
New-Item -ItemType Directory -Force -Path $OUTPUT_DIR | Out-Null

Write-Host "[1/2] Compilando informe PDF..."
Set-Location $SCRIPT_DIR
pdflatex -interaction=nonstopmode -halt-on-error -output-directory $OUTPUT_DIR informe_tp2.tex

Write-Host "[2/2] Limpiando archivos auxiliares..."
Get-ChildItem $OUTPUT_DIR -Include *.aux,*.log,*.out,*.toc -File | Remove-Item -Force

Write-Host ""
Write-Host "Informe generado correctamente en:"
Write-Host "  $OUTPUT_DIR/informe_tp2.pdf"
