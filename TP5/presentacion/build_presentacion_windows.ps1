#requires -Version 5.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Igual que TP4/presentacion/build_presentacion_windows.ps1, con los mismos tres agregados que
# build_presentacion.sh: compila presentacion_tp5.tex, falla con "Overfull \vbox" y renombra el PDF
# con el nombre de la entrega.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OutputDir = Join-Path $ScriptDir "generated"
$Source = "presentacion_tp5"
$FinalName = "SdS_TP5_2026Q2G02CS_Presentaci$([char]0x00F3)n.pdf"   # "ó" sin depender de la codificación del .ps1
$Pdf = Join-Path $OutputDir "$Source.pdf"
$Log = Join-Path $OutputDir "$Source.log"
$Final = Join-Path $OutputDir $FinalName

if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
    Write-Error "Falta la dependencia 'latexmk'."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
# Se borra el PDF anterior para que un fallo no deje copiar una version vieja.
Remove-Item -Force -ErrorAction SilentlyContinue $Pdf, $Final

# -gg fuerza una recompilacion completa ignorando el estado guardado por
# latexmk (.fdb_latexmk/.fls). Sin esto, si una corrida anterior fallo a
# mitad de camino (ej. el PDF estaba abierto en un visor y no se pudo
# sobreescribir), latexmk puede creer erroneamente que el PDF ya esta
# actualizado y no recompilar, aunque el .tex haya cambiado.
# Se compila desde ScriptDir porque las figuras se buscan con rutas relativas (figuras/...).
Push-Location $ScriptDir
try {
    latexmk -pdf -gg -interaction=nonstopmode -halt-on-error "-outdir=$OutputDir" "$Source.tex"
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
if ($code -ne 0) {
    Write-Error "La compilacion de $Source.tex fallo. Ver $Log"
}
if (-not (Test-Path $Pdf)) {
    Write-Error "latexmk termino sin generar $Pdf"
}
$overfull = Select-String -Path $Log -Pattern '^Overfull \\vbox'
if ($overfull) {
    $overfull | ForEach-Object { Write-Host $_.Line }
    Write-Error "Hay contenido que no entra en la diapositiva (Overfull \vbox)."
}

# Se mueve (no se copia) para que en generated/ quede un solo PDF, con el nombre de la entrega.
Move-Item -Force $Pdf $Final
Write-Host "Presentacion generada en $Final"
