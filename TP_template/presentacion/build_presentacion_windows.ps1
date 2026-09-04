#requires -Version 5.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OutputDir = Join-Path $ScriptDir "generated"

if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
    Write-Error "Falta la dependencia 'latexmk'."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
latexmk -pdf -interaction=nonstopmode -halt-on-error `
    -outdir=$OutputDir (Join-Path $ScriptDir "presentacion_template.tex")

Write-Host "Presentacion generada en $OutputDir/presentacion_template.pdf"

