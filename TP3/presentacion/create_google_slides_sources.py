#!/usr/bin/env python3
"""Convierte el PDF Beamer renderizado en un PPTX de imágenes para Google Slides."""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import uno
from com.sun.star.beans import PropertyValue

PAGE_WIDTH = 25400
PAGE_HEIGHT = 19050

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
    return shape


def main():
    base = Path(__file__).resolve().parent
    output_dir = base / "generated" / "google-slides"
    pdf = base / "generated" / "presentacion_imagen.pdf"
    renders = output_dir / "rendered"
    renders.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-scale-to", "2400", "-png", str(pdf),
                    str(renders / "slide")], check=True)
    texts = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True).split("\f")
    if not texts[-1].strip():
        texts.pop()
    import re
    images = [renders / f"slide-{i:0{len(str(len(texts)))}d}.png"
              for i in range(1, len(texts) + 1)]
    output = output_dir / "TP3_Billar_Metegol_imagenes.pptx"
    with tempfile.TemporaryDirectory(prefix="tp3-lo-profile-") as profile:
        process, desktop = connect_to_libreoffice(Path(profile))
        try:
            document = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0, ())
            pages = document.getDrawPages()
            for i, image in enumerate(images):
                page = pages.getByIndex(0) if i == 0 else pages.insertNewByIndex(i)
                page.Width, page.Height = PAGE_WIDTH, PAGE_HEIGHT
                while page.getCount():
                    page.remove(page.getByIndex(0))
                shape = add_background(document, page, image)
                match = re.search(r"https://youtu\.be/[A-Za-z0-9_-]+", texts[i])
                if match:
                    shape.OnClick = uno.Enum("com.sun.star.presentation.ClickAction", "DOCUMENT")
                    shape.Bookmark = match.group()
                    print(f"Diapositiva {i + 1}: {match.group()}")
            document.storeAsURL(output.as_uri(),
                (property_value("FilterName", "Impress MS PowerPoint 2007 XML"),))
            document.close(True)
        finally:
            process.terminate()
            process.wait(timeout=10)
    print(f"Generadas {len(images)} diapositivas: {output}")


if __name__ == "__main__":
    main()

