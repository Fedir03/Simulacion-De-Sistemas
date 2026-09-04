#requires -Version 5.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Directorios
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OUTPUT_DIR = Join-Path $SCRIPT_DIR "generated"
$BUILD_DIR = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath()) -Name ("tp2-presentacion-" + (Get-Random))

# Limpieza al salir
Register-EngineEvent PowerShell.Exiting -Action { Remove-Item -Recurse -Force $BUILD_DIR }

# Dependencias requeridas
$dependencies = @("latexmk", "pdfinfo", "pdftoppm")

# Verificación especial para LibreOffice
if (-not (Get-Command soffice -ErrorAction SilentlyContinue)) {
    $sofficePath = "C:\Program Files\LibreOffice\program\soffice.exe"
    if (-not (Test-Path $sofficePath)) {
        Write-Error "Falta la dependencia 'soffice' (no está en PATH ni en $sofficePath)."
        exit 1
    }
} else {
    $sofficePath = (Get-Command soffice).Source
}

# Verificación especial para Perl
if (-not (Get-Command perl -ErrorAction SilentlyContinue)) {
    $perlPath = "C:\Strawberry\perl\bin\perl.exe"
    if (-not (Test-Path $perlPath)) {
        Write-Error "Falta la dependencia 'perl' (no está en PATH ni en $perlPath)."
        exit 1
    }
} else {
    $perlPath = (Get-Command perl).Source
}

# Verificación especial para Python (LibreOffice UNO)
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonPath = "C:\Program Files\LibreOffice\program\python.exe"
    if (-not (Test-Path $pythonPath)) {
        Write-Error "Falta la dependencia 'python' (no está en PATH ni en $pythonPath)."
        exit 1
    }
} else {
    $pythonPath = (Get-Command python).Source
}

foreach ($dep in $dependencies) {
    if (-not (Get-Command $dep -ErrorAction SilentlyContinue)) {
        Write-Error "Falta la dependencia '$dep'."
        exit 1
    }
}

if (-not (Test-Path (Join-Path $SCRIPT_DIR "template_presentacion_tp2.tex"))) {
    Write-Error "No se encontró template_presentacion_tp2.tex en $SCRIPT_DIR."
    exit 1
}

New-Item -ItemType Directory -Force -Path "$BUILD_DIR/latex","$BUILD_DIR/rendered","$BUILD_DIR/pptx","$OUTPUT_DIR" | Out-Null

Write-Host "[1/4] Compilando PDF de entrega..."
Set-Location $SCRIPT_DIR
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$BUILD_DIR/latex" presentacion_imagen.tex

$PAGE_COUNT = (& pdfinfo "$BUILD_DIR/latex/presentacion_imagen.pdf" | ForEach-Object {
    if ($_ -match "^Pages:\s+(\d+)") { $matches[1] }
})

if (-not $PAGE_COUNT) {
    Write-Error "No se pudo determinar la cantidad de diapositivas del PDF."
    exit 1
}

Write-Host "[2/4] Renderizando las $PAGE_COUNT diapositivas para Google Slides..."
pdftoppm -png -r 384 -f 1 -l $PAGE_COUNT "$BUILD_DIR/latex/presentacion_imagen.pdf" "$BUILD_DIR/rendered/slide" | Out-Null

Write-Host "[3/4] Generando PPTX importable en Google Slides..."
$env:PATH += ";C:\Program Files\LibreOffice\program"
$env:SOFFICE = "C:\Program Files\LibreOffice\program\soffice.exe"

& $pythonPath "$SCRIPT_DIR/create_google_slides_sources.py" `
    --renders "$BUILD_DIR/rendered" `
    --outdir "$BUILD_DIR/pptx" `
    --expected-slides $PAGE_COUNT


Copy-Item "$BUILD_DIR/latex/presentacion_imagen.pdf" "$OUTPUT_DIR/TP2_Vicsek_entrega.pdf"
Copy-Item "$BUILD_DIR/pptx/TP2_Vicsek_videos.pptx" "$OUTPUT_DIR/TP2_Vicsek_para_Google_Slides.pptx"

Write-Host "[4/4] Limpiando archivos auxiliares..."
latexmk -C "$SCRIPT_DIR/template_presentacion_tp2.tex" "$SCRIPT_DIR/presentacion_imagen.tex" | Out-Null

Get-ChildItem $SCRIPT_DIR -Include *.aux,*.fdb_latexmk,*.fls,*.log,*.nav,*.out,*.snm,*.synctex.gz,*.toc -File | Remove-Item -Force

Remove-Item -Force "$SCRIPT_DIR/TP2_Vicsek_entrega.pdf","$SCRIPT_DIR/TP2_Vicsek_para_Google_Slides.pptx" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Presentaciones generadas correctamente en:"
Write-Host "  $OUTPUT_DIR/TP2_Vicsek_entrega.pdf"
Write-Host "  $OUTPUT_DIR/TP2_Vicsek_para_Google_Slides.pptx"
