#!/usr/bin/env python3
"""Genera dos PPTX importables en Google Slides a partir del Beamer renderizado.

La versión imagen conserva las capturas de las animaciones. La versión video
agrega, en las diapositivas 14--16 y 20--22, dos placeholders editables para
insertar los videos de YouTube en Google Slides.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue


PAGE_WIDTH = 25_400
PAGE_HEIGHT = 19_050
ANIMATION_SLIDES = {
    14: (
        ("η = 0.5", "https://youtu.be/sEDXRR8ARZ8"),
        ("η = 2", "https://youtu.be/j-hlr1N8Z2s"),
    ),
    15: (
        ("η = 0.5", "https://youtu.be/3qtWyzX8O0Y"),
        ("η = 2", "https://youtu.be/tSCNM-5Nypw"),
    ),
    16: (
        ("η = 0.5", "https://youtu.be/CjRGO-5fePk"),
        ("η = 2", "https://youtu.be/J3nHD0oBGfM"),
    ),
    20: (
        ("η = 0.5", "https://youtu.be/OyJbGN_weK4"),
        ("η = 2", "https://youtu.be/oLabBdmlHN4"),
    ),
    21: (
        ("η = 0.5", "https://youtu.be/XqlSIoh8m60"),
        ("η = 2", "https://youtu.be/IiN3baNlE9s"),
    ),
    22: (
        ("η = 0.5", "https://youtu.be/j0L89se9d-U"),
        ("η = 2", "https://youtu.be/JnMzeiVw5Tw"),
    ),
}

VIDEO_COLUMNS = (
    (1_500, 1_500),
    (13_300, 13_300),
)


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

def find_libreoffice() -> str:
    candidates = [
        os.environ.get("SOFFICE"),
        shutil.which("libreoffice"),
        shutil.which("soffice"),
    ]

    if sys.platform == "win32":
        candidates.extend([
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ])

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate

    raise FileNotFoundError(
        "No se encontró el ejecutable de LibreOffice. "
        "Se buscó SOFFICE, libreoffice/soffice en PATH "
        "y las rutas estándar de Windows."
    )

def connect_to_libreoffice(profile: Path):
    port = 2083
    command = [
        find_libreoffice(),
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


def add_link(document, page, url: str, x: int) -> None:
    shape = document.createInstance("com.sun.star.drawing.TextShape")
    shape.Position = point(x, 15_750)
    shape.Size = size(10_600, 650)
    shape.FillTransparence = 100
    shape.LineTransparence = 100
    page.add(shape)
    shape.ZOrder = 101
    url_field = document.createInstance("com.sun.star.text.textfield.URL")
    url_field.URL = url
    url_field.Representation = url
    url_field.TargetFrame = "_blank"
    shape.Text.insertTextContent(shape.Text.createTextCursor(), url_field, False)
    cursor = shape.Text.createTextCursor()
    cursor.gotoEnd(True)
    cursor.CharFontName = "Liberation Sans"
    cursor.CharHeight = 9.0
    cursor.CharColor = 0x3939B5
    cursor.CharUnderline = 1
    cursor.ParaAdjust = 3


def add_video_placeholder(document, page, label: str, url: str, x: int) -> None:
    box = document.createInstance("com.sun.star.drawing.TextShape")
    box.Position = point(x, 7_050)
    box.Size = size(10_600, 5_963)
    box.FillColor = 0x11112A
    box.FillTransparence = 8
    box.LineColor = 0x3939B5
    box.LineWidth = 60
    page.add(box)
    box.ZOrder = 100
    box.String = (
        "VIDEO DE YOUTUBE\n\n"
        f"Animación con {label}\n\n"
        "En Google Slides: Insertar → Video → YouTube\n"
        f"Reemplazar usando: {url}"
    )
    cursor = box.Text.createTextCursor()
    cursor.gotoEnd(True)
    cursor.CharFontName = "Liberation Sans"
    cursor.CharHeight = 10.0
    cursor.CharColor = 0xFFFFFF
    cursor.ParaAdjust = 3
    cursor.ParaTopMargin = 400

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
            for (label, url), (placeholder_x, link_x) in zip(
                ANIMATION_SLIDES[slide_number], VIDEO_COLUMNS, strict=True
            ):
                if video_mode:
                    add_video_placeholder(document, page, label, url, placeholder_x)
                add_link(document, page, url, link_x)

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
    parser.add_argument("--expected-slides", type=int, required=True)
    args = parser.parse_args()

    images = sorted(args.renders.glob("slide-*.png"))
    if len(images) != args.expected_slides:
        raise SystemExit(
            f"Se esperaban {args.expected_slides} diapositivas renderizadas; "
            f"se encontraron {len(images)}"
        )

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
