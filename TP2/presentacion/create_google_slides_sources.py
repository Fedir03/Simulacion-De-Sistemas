#!/usr/bin/env python3
"""Genera dos PPTX importables en Google Slides a partir del Beamer renderizado.

La versión imagen conserva las capturas de las animaciones. La versión video
agrega, en las diapositivas 15--17, placeholders editables para insertar luego
los videos de YouTube en Google Slides, y en la diapositiva 23 un placeholder
16:9 para el video de la variante de interacción.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue


PAGE_WIDTH = 25_400
PAGE_HEIGHT = 19_050
ANIMATION_SLIDES = {
    15: ("ρ = 2", "https://www.youtube.com/watch?v=yNQh6aFtVFk"),
    16: ("ρ = 4", "https://youtu.be/REEMPLAZAR-RHO4"),
    17: ("ρ = 8", "https://youtu.be/REEMPLAZAR-RHO8"),
}
VARIANT_VIDEO_SLIDE = 23


def property_value(name: str, value) -> PropertyValue:
    prop = PropertyValue()
    prop.Name = name
    prop.Value = value
    return prop


def point(x: int, y: int):
    value = uno.createUnoStruct("com.sun.star.awt.Point")
    value.X = x
    value.Y = y
    return value


def size(width: int, height: int):
    value = uno.createUnoStruct("com.sun.star.awt.Size")
    value.Width = width
    value.Height = height
    return value


def connect_to_libreoffice(profile: Path):
    port = 2083
    command = [
        shutil.which("libreoffice") or "libreoffice",
        "--headless",
        "--nologo",
        "--nodefault",
        "--nofirststartwizard",
        "--norestore",
        f"-env:UserInstallation={profile.as_uri()}",
        f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    for _ in range(60):
        try:
            context = resolver.resolve(
                f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"
            )
            desktop = context.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", context
            )
            return process, desktop
        except Exception:
            time.sleep(0.25)
    process.terminate()
    raise RuntimeError("No se pudo iniciar LibreOffice en modo headless")


def add_background(document, page, image_path: Path) -> None:
    shape = document.createInstance("com.sun.star.drawing.GraphicObjectShape")
    shape.Position = point(0, 0)
    shape.Size = size(PAGE_WIDTH, PAGE_HEIGHT)
    shape.GraphicURL = image_path.resolve().as_uri()
    page.add(shape)


def add_link(document, page, url: str) -> None:
    shape = document.createInstance("com.sun.star.drawing.TextShape")
    shape.Position = point(1_700, 16_850)
    shape.Size = size(14_600, 650)
    shape.FillTransparence = 100
    shape.LineTransparence = 100
    page.add(shape)
    shape.ZOrder = 101
    shape.String = "▶ Ver video en YouTube"
    cursor = shape.Text.createTextCursor()
    cursor.gotoEnd(True)
    cursor.CharFontName = "Liberation Sans"
    cursor.CharHeight = 9.0
    cursor.CharColor = 0x3939B5
    cursor.CharUnderline = 1
    cursor.ParaAdjust = 3


def add_video_placeholder(document, page, density: str, url: str) -> None:
    box = document.createInstance("com.sun.star.drawing.TextShape")
    box.Position = point(1_250, 4_100)
    box.Size = size(15_400, 11_750)
    box.FillColor = 0x11112A
    box.FillTransparence = 8
    box.LineColor = 0x3939B5
    box.LineWidth = 60
    page.add(box)
    box.ZOrder = 100
    box.String = (
        "VIDEO DE YOUTUBE\n\n"
        f"Animación para {density}\n\n"
        "En Google Slides: Insertar → Video → YouTube\n"
        f"Reemplazar usando:\n{url}"
    )
    cursor = box.Text.createTextCursor()
    cursor.gotoEnd(True)
    cursor.CharFontName = "Liberation Sans"
    cursor.CharHeight = 15.0
    cursor.CharColor = 0xFFFFFF
    cursor.ParaAdjust = 3
    cursor.ParaTopMargin = 400


def add_variant_video_placeholder(document, page) -> None:
    """Agrega un marco editable transparente con relación exacta 16:9."""
    box = document.createInstance("com.sun.star.drawing.TextShape")
    box.Position = point(2_700, 4_250)
    box.Size = size(20_000, 11_250)
    box.FillColor = 0xF4F4F7
    box.FillTransparence = 100
    box.LineColor = 0x858585
    box.LineWidth = 45
    page.add(box)
    box.ZOrder = 100
    box.String = ""


def build_deck(desktop, images: list[Path], output: Path, video_mode: bool) -> None:
    document = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0, ())
    pages = document.getDrawPages()
    while pages.getCount() > 1:
        pages.remove(pages.getByIndex(pages.getCount() - 1))

    for index, image_path in enumerate(images):
        page = pages.getByIndex(0) if index == 0 else pages.insertNewByIndex(index)
        page.Width = PAGE_WIDTH
        page.Height = PAGE_HEIGHT
        add_background(document, page, image_path)
        slide_number = index + 1
        if slide_number in ANIMATION_SLIDES:
            density, url = ANIMATION_SLIDES[slide_number]
            if video_mode:
                add_video_placeholder(document, page, density, url)
            add_link(document, page, url)
        elif video_mode and slide_number == VARIANT_VIDEO_SLIDE:
            add_variant_video_placeholder(document, page)

    output.parent.mkdir(parents=True, exist_ok=True)
    document.storeAsURL(
        output.resolve().as_uri(),
        (property_value("FilterName", "Impress MS PowerPoint 2007 XML"),),
    )
    document.close(True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    images = sorted(args.renders.glob("slide-*.png"))
    if len(images) != 28:
        raise SystemExit(f"Se esperaban 28 diapositivas renderizadas; se encontraron {len(images)}")

    with tempfile.TemporaryDirectory(prefix="tp2-lo-profile-") as profile_dir:
        process, desktop = connect_to_libreoffice(Path(profile_dir))
        try:
            build_deck(desktop, images, args.outdir / "TP2_Vicsek_imagenes.pptx", False)
            build_deck(desktop, images, args.outdir / "TP2_Vicsek_videos.pptx", True)
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
