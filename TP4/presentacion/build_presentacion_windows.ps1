#requires -Version 5.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OutputDir = Join-Path $ScriptDir "generated"

if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
    Write-Error "Falta la dependencia 'latexmk'."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
# -gg fuerza una recompilacion completa ignorando el estado guardado por
# latexmk (.fdb_latexmk/.fls). Sin esto, si una corrida anterior fallo a
# mitad de camino (ej. el PDF estaba abierto en un visor y no se pudo
# sobreescribir), latexmk puede creer erroneamente que el PDF ya esta
# actualizado y no recompilar, aunque el .tex haya cambiado.
latexmk -pdf -gg -interaction=nonstopmode -halt-on-error `
    "-outdir=$OutputDir" (Join-Path $ScriptDir "presentacion_imagen.tex")

Write-Host "Presentacion generada en $OutputDir/presentacion_imagen.pdf"

