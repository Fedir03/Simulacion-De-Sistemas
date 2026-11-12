#!/usr/bin/env python3
# Uso (desde TP5/, después de bash presentacion/build_presentacion.sh): py presentacion/create_google_slides_sources.py
"""PPTX para exponer en vivo: una imagen por diapositiva del PDF y, donde hay animación, el MP4 insertado encima.

Adaptado de TP4/presentacion/create_google_slides_sources.py (misma vía: LibreOffice por UNO). Dos etapas:
  1. Con el Python normal (py): renderiza el PDF de entrega con pdftoppm, lee la URL visible de cada página con
     pdftotext y la posición del fotograma con PyMuPDF, y decide qué MP4 va en cada diapositiva (VIDEOS, abajo).
  2. Se vuelve a llamar con el Python de LibreOffice (necesita el módulo uno) y arma el PPTX como en TP4,
     con un MediaShape del tamaño y la posición del fotograma.
  3. De vuelta en py: LibreOffice deja los videos como link a una ruta local, así que se copian dentro del PPTX
     (ppt/media/) y se usa como póster el recorte del fotograma de la diapositiva. Así el PPTX se puede llevar a
     otra computadora o subir a Google Slides.
Salida: presentacion/generated/SdS_TP5_presentacion_en_vivo.pptx (no se versiona; es un paso aparte del build).
Opción: --extra "URL_O_FRAGMENTO=ruta.mp4" agrega una entrada al mapeo (para probar con un PDF que tenga otra URL).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

# URL (o fragmento de la URL) visible en la página -> MP4 (relativo a TP5/). Cuando se suban los videos a YouTube
# y el .tex tenga las URL reales, reemplazar cada clave por la URL nueva (o por un fragmento único de ella).
VIDEOS = {
    "https://youtu.be/PENDIENTE-recorte": "presentacion/animaciones/01_recorte_evento11.mp4",
    "https://youtu.be/PENDIENTE-sincapa": "presentacion/animaciones/02_sin_capa_vs_A_evento16.mp4",
    "https://youtu.be/PENDIENTE-ab": "presentacion/animaciones/03_A_y_B_evento16.mp4",
    "https://youtu.be/PENDIENTE-lado": "presentacion/animaciones/04_lado_contrario_evento12.mp4",
}

BASE = Path(__file__).resolve().parent          # TP5/presentacion
TP5 = BASE.parent
# Detección (qué páginas llevan video y dónde está el fotograma): el PDF de entrega, que muestra las URL.
PDF = BASE / "generated" / "SdS_TP5_2026Q2G02CS_Presentación.pdf"
PDF_FALLBACK = BASE / "generated" / "presentacion_tp5.pdf"
# Imágenes de las diapositivas: la versión en vivo (\versionvivo), igual pero sin la URL debajo del fotograma.
VIVO_TEX = BASE / "presentacion_vivo.tex"
VIVO_PDF = BASE / "generated" / "presentacion_vivo.pdf"
WORK = BASE / "generated" / "en_vivo"
OUTPUT = BASE / "generated" / "SdS_TP5_presentacion_en_vivo.pptx"
PAGE_WIDTH, PAGE_HEIGHT = 25400, 19050          # 1/100 mm, 4:3 como el Beamer (igual que TP4)
LO_PORT = 2083


# ================================================================ etapa 2: LibreOffice (python de LibreOffice)
def libreoffice_stage(plan_path):
    import uno
    from com.sun.star.beans import PropertyValue

    def prop(name, value):
        p = PropertyValue()
        p.Name, p.Value = name, value
        return p

    def point(x, y):
        v = uno.createUnoStruct("com.sun.star.awt.Point")
        v.X, v.Y = int(x), int(y)
        return v

    def size(w, h):
        v = uno.createUnoStruct("com.sun.star.awt.Size")
        v.Width, v.Height = int(w), int(h)
        return v

    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    profile = Path(tempfile.mkdtemp(prefix="tp5-lo-profile-"))
    process = subprocess.Popen([plan["soffice"], "--headless", "--nologo", "--nodefault", "--nofirststartwizard",
                                "--norestore", f"-env:UserInstallation={profile.as_uri()}",
                                f"--accept=socket,host=127.0.0.1,port={LO_PORT};urp;StarOffice.ComponentContext"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        for _ in range(80):
            try:
                ctx = resolver.resolve(f"uno:socket,host=127.0.0.1,port={LO_PORT};urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("No se pudo iniciar LibreOffice en modo headless")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        document = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0, ())
        pages = document.getDrawPages()
        for i, slide in enumerate(plan["slides"]):
            page = pages.getByIndex(0) if i == 0 else pages.insertNewByIndex(i)
            page.Width, page.Height = PAGE_WIDTH, PAGE_HEIGHT
            while page.getCount():
                page.remove(page.getByIndex(0))
            background = document.createInstance("com.sun.star.drawing.GraphicObjectShape")
            page.add(background)
            background.Position, background.Size = point(0, 0), size(PAGE_WIDTH, PAGE_HEIGHT)
            background.GraphicURL = Path(slide["image"]).as_uri()
            for v in slide.get("videos", []):
                x, y, w, h = v["box"]
                media = document.createInstance("com.sun.star.presentation.MediaShape")
                page.add(media)
                media.Position, media.Size = point(x, y), size(w, h)
                media.MediaURL = Path(v["video"]).as_uri()
        document.storeAsURL(Path(plan["output"]).as_uri(), (prop("FilterName", "Impress MS PowerPoint 2007 XML"),))
        document.close(True)
    finally:
        process.terminate()
        process.wait(timeout=10)


# ================================================================ etapas 1 y 3: python normal
def find_libreoffice():
    candidates = [os.environ.get("SOFFICE"), shutil.which("soffice"), shutil.which("libreoffice")]
    if sys.platform == "win32":
        candidates += [r"C:\Program Files\LibreOffice\program\soffice.exe",
                       r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c)
    raise FileNotFoundError("No se encontró LibreOffice (variable SOFFICE, soffice en PATH o rutas estándar).")


def libreoffice_python(soffice):
    name = "python.exe" if sys.platform == "win32" else "python"
    p = soffice.parent / name
    if not p.is_file():
        raise FileNotFoundError(f"No se encontró el Python de LibreOffice en {p} (hace falta el módulo uno).")
    return p


def videos_in(text, videos):
    """Claves de videos que aparecen en el texto de la página, sin que una clave contenida en otra cuente dos veces."""
    found = []
    for key in sorted(videos, key=len, reverse=True):
        if key in text and not any(key in k for k in found):
            found.append(key)
    return found


def frame_boxes(pdf_path, page_index, keys):
    """Para cada URL visible, la caja de la imagen que está justo arriba de ella (su fotograma), en 1/100 mm del PPTX.

    Con dos animaciones en la misma diapositiva cada URL queda debajo de su fotograma; si la URL no se encuentra
    como texto, se usa la imagen más grande de la página."""
    import pymupdf
    boxes = {}
    with pymupdf.open(pdf_path) as doc:
        page = doc[page_index]
        imgs = [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
        sx, sy = PAGE_WIDTH / page.rect.width, PAGE_HEIGHT / page.rect.height
        for key in keys:
            best = None
            hits = page.search_for(key)
            if hits and imgs:
                u = hits[0]
                above = [r for r in imgs if r.y1 <= u.y0 + 2 and min(r.x1, u.x1) - max(r.x0, u.x0) > 0]
                if above:
                    best = min(above, key=lambda r: u.y0 - r.y1)
            if best is None and imgs:
                best = max(imgs, key=lambda b: b.width * b.height)
            if best is not None:
                boxes[key] = (best, [best.x0 * sx, best.y0 * sy, best.width * sx, best.height * sy])
    return boxes


def image_rects(pdf_path, page_index):
    import pymupdf
    with pymupdf.open(pdf_path) as doc:
        return [tuple(round(c, 1) for c in i["bbox"]) for i in doc[page_index].get_image_info()]


TRANSITION = re.compile(r"<mc:AlternateContent>(?:(?!</mc:AlternateContent>).)*?<p:transition.*?</mc:AlternateContent>"
                        r"|<p:transition\b[^>]*/>|<p:transition\b.*?</p:transition>", re.S)


def video_ms(path):
    """Duración del MP4 en milisegundos (ffprobe)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return int(round(float(out) * 1000))


def autoplay_timing(items):
    """<p:timing> de PowerPoint para que los videos arranquen solos al entrar a la diapositiva (todos juntos).

    items: [(spid, dur_ms)]. Es el patrón que escribe PowerPoint con "Inicio: automáticamente": el primero
    después de la entrada de la diapositiva (afterEffect) y el resto a la vez (withEffect), más un cMediaNode
    por video. Sin este bloque el video queda quieto en el póster hasta que se hace clic.
    """
    n = [2]

    def nid():
        n[0] += 1
        return n[0]

    calls = []
    for k, (spid, dur) in enumerate(items):
        node = "afterEffect" if k == 0 else "withEffect"
        a, b = nid(), nid()
        calls.append(
            f'<p:par><p:cTn id="{a}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="{node}">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="{b}" dur="{dur}" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd></p:childTnLst></p:cTn></p:par>')
    outer, inner = nid(), nid()
    seq = (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
           f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
           f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
           f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
           + "".join(calls) +
           '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>'
           '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
           '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>')
    media = "".join(
        f'<p:video><p:cMediaNode vol="80000"><p:cTn id="{nid()}" fill="hold" display="0"><p:stCondLst>'
        f'<p:cond delay="indefinite"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
        f'</p:cMediaNode></p:video>' for spid, _ in items)
    return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            + seq + media + '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')


def embed_videos(pptx, slides):
    """Pasa los videos de link externo a archivo dentro del PPTX y pone como póster el recorte de su fotograma."""
    from io import BytesIO
    from PIL import Image
    # MP4 (ruta absoluta) -> póster (recorte del fotograma en la imagen de su diapositiva)
    posters = {}
    for s in slides:
        for v in s.get("videos", []):
            x, y, w, h = v["box"]
            img = Image.open(s["image"])
            k = img.width / PAGE_WIDTH
            posters[(s["image"], str(Path(v["video"]).resolve()).lower())] = img.crop(
                (int(x * k), int(y * k), int((x + w) * k), int((y + h) * k)))
    tmp = pptx.with_suffix(".tmp.pptx")
    media_n = 0
    with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        names = zin.namelist()
        replaced = {}           # nombre en el zip -> bytes nuevos
        added = {}
        for name in names:
            m = re.fullmatch(r"ppt/slides/_rels/slide(\d+)\.xml\.rels", name)
            if not m:
                continue
            rels = zin.read(name).decode("utf-8")
            targets = sorted(set(re.findall(r'Target="(file:///[^"]+\.mp4)" TargetMode="External"', rels)))
            if not targets:
                continue
            slide_no = int(m.group(1))
            slide_image = slides[slide_no - 1]["image"]
            slide_xml = zin.read(f"ppt/slides/slide{slide_no}.xml").decode("utf-8")
            # Antes de reescribir: rId del video -> archivo, para saber qué póster va en cada p:pic
            rid_to_file = {rid: re.sub(r"^file:///", "", tgt).replace("%20", " ")
                           for rid, tgt in re.findall(r'Id="(rId\d+)"[^>]*Target="(file:///[^"]+\.mp4)"', rels)}
            autoplay = []           # (spid, duración en ms) de cada video de la diapositiva
            for pic in re.findall(r'<p:pic>(?:(?!</p:pic>).)*?videoFile(?:(?!</p:pic>).)*?</p:pic>', slide_xml, re.S):
                link = re.search(r'videoFile r:link="(rId\d+)"', pic)
                emb = re.search(r'r:embed="(rId\d+)"', pic)
                if not (link and emb and link.group(1) in rid_to_file):
                    continue
                spid = re.search(r'<p:cNvPr id="(\d+)"', pic).group(1)
                autoplay.append((spid, video_ms(rid_to_file[link.group(1)])))
                key = (slide_image, str(Path(rid_to_file[link.group(1)]).resolve()).lower())
                tgt = re.search(rf'Id="{emb.group(1)}"[^>]*Target="\.\./(media/[^"]+)"', rels)
                if key in posters and tgt:
                    buf = BytesIO()
                    posters[key].convert("RGB").save(buf, format="PNG")
                    replaced[f"ppt/{tgt.group(1)}"] = buf.getvalue()
            for target in targets:
                media_n += 1
                inner = f"media/video{media_n}.mp4"
                added[f"ppt/{inner}"] = Path(re.sub(r"^file:///", "", target).replace("%20", " ")).read_bytes()
                rels = rels.replace(f'Target="{target}" TargetMode="External"', f'Target="../{inner}"')
            replaced[name] = rels.encode("utf-8")
            # El video queda adentro del PPTX: p14:media tiene que ser r:embed (con r:link PowerPoint lo trata
            # como externo y muestra solo el póster). Y arranque automático al entrar a la diapositiva.
            slide_xml = slide_xml.replace("<p14:media r:link=", "<p14:media r:embed=")
            slide_xml = TRANSITION.sub("", slide_xml)
            if autoplay:
                slide_xml = slide_xml.replace("</p:sld>", autoplay_timing(autoplay) + "</p:sld>")
            replaced[f"ppt/slides/slide{slide_no}.xml"] = slide_xml.encode("utf-8")
        ct = zin.read("[Content_Types].xml").decode("utf-8")
        if 'Extension="mp4"' not in ct:
            ct = ct.replace("<Default ", '<Default Extension="mp4" ContentType="video/mp4"/><Default ', 1)
        replaced["[Content_Types].xml"] = ct.encode("utf-8")
        for name in names:
            data = replaced.get(name)
            if data is None:
                data = zin.read(name)
                # Sin transiciones (LibreOffice deja una de 2 s en cada diapositiva)
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                    data = TRANSITION.sub("", data.decode("utf-8")).encode("utf-8")
            zout.writestr(name, data)
        for name, data in added.items():
            zout.writestr(name, data)
    tmp.replace(pptx)
    return media_n


def check(pptx):
    """Diapositivas totales y cuáles tienen video embebido (y que no quede ningún link externo)."""
    with zipfile.ZipFile(pptx) as z:
        slides = sorted(int(m.group(1)) for n in z.namelist() if (m := re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n)))
        with_video = []
        for n in slides:
            rels = z.read(f"ppt/slides/_rels/slide{n}.xml.rels").decode("utf-8")
            assert "TargetMode=\"External\"" not in rels or ".mp4" not in rels, f"diapositiva {n}: video externo"
            # Cada video tiene dos relaciones al mismo MP4 (video y media de p14): se cuentan archivos distintos
            k = len(set(re.findall(r'Target="\.\./media/(video\d+\.mp4)"', rels)))
            if k:
                with_video.append(n if k == 1 else f"{n} ({k} videos)")
    return slides, with_video


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--libreoffice-stage":
        libreoffice_stage(sys.argv[2])
        return
    sys.stdout.reconfigure(encoding="utf-8")
    videos = {k: str(TP5 / v) for k, v in VIDEOS.items()}
    args = sys.argv[1:]
    while args:
        if args[0] == "--extra" and len(args) > 1:
            key, value = args[1].split("=", 1)
            videos[key] = str((TP5 / value).resolve())
            args = args[2:]
        else:
            raise SystemExit(f"Argumento desconocido: {args[0]}")
    # 1. Fuente de detección: el PDF de entrega; si no está o no se puede leer, el de latexmk (mismo contenido)
    detect = PDF
    try:
        with open(PDF, "rb") as f:
            f.read(4)
    except OSError:
        detect = PDF_FALLBACK
        print(f"No se puede leer {PDF.name}; se detectan los videos en {PDF_FALLBACK.name}")
    if not detect.is_file():
        raise SystemExit(f"No está {detect}; correr antes bash presentacion/build_presentacion.sh")
    # 2. Versión en vivo (sin la URL debajo de cada fotograma)
    if not VIVO_TEX.is_file():
        raise SystemExit(f"No está {VIVO_TEX}")
    r = subprocess.run(["latexmk", "-pdf", "-gg", "-interaction=nonstopmode", "-halt-on-error", "-outdir=generated",
                        VIVO_TEX.name], cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0 or not VIVO_PDF.is_file():
        raise SystemExit(f"Error: falló la compilación de {VIVO_TEX.name}; ver generated/presentacion_vivo.log")
    for v in set(videos.values()):
        if not Path(v).is_file():
            print(f"Aviso: falta el video {v}")
    renders = WORK / "rendered"
    shutil.rmtree(renders, ignore_errors=True)
    renders.mkdir(parents=True)
    subprocess.run(["pdftoppm", "-scale-to", "2400", "-png", str(VIVO_PDF), str(renders / "slide")], check=True)
    texts = subprocess.check_output(["pdftotext", "-enc", "UTF-8", "-layout", str(detect), "-"], text=True,
                                    encoding="utf-8").split("\f")
    if not texts[-1].strip():
        texts.pop()
    images = sorted(renders.glob("slide-*.png"))
    assert len(images) == len(texts), f"{len(images)} diapositivas en vivo contra {len(texts)} páginas de entrega"
    slides = []
    for i, (image, text) in enumerate(zip(images, texts)):
        slide = {"image": str(image)}
        keys = [k for k in videos_in(text, videos) if Path(videos[k]).is_file()]
        if keys:
            boxes = frame_boxes(detect, i, keys)
            # Control: los fotogramas tienen que estar en el mismo lugar en la versión en vivo
            vivo = image_rects(VIVO_PDF, i)
            for k, (rect, _) in boxes.items():
                if tuple(round(c, 1) for c in rect) not in vivo:
                    raise SystemExit(f"Diapositiva {i + 1}: el fotograma de {k} no está en el mismo lugar en la "
                                     f"versión en vivo ({tuple(round(c, 1) for c in rect)} contra {vivo})")
            slide["videos"] = [{"video": videos[k], "box": boxes[k][1]} for k in keys if k in boxes]
            for k in keys:
                print(f"Diapositiva {i + 1}: {k} -> {Path(videos[k]).name}")
        slides.append(slide)
    # Control: la diapositiva de animaciones + d(t) (Resultados) lleva los dos videos del evento 16 juntos, uno sobre
    # cada fotograma (el gráfico de d(t) es vectorial y no cuenta como imagen)
    merged = [VIDEOS[k] for k in ("https://youtu.be/PENDIENTE-sincapa", "https://youtu.be/PENDIENTE-ab") if k in VIDEOS]
    if len(merged) == 2:
        wanted = {str(TP5 / v) for v in merged}
        pages = [n for n, s in enumerate(slides, 1) if wanted & {v["video"] for v in s.get("videos", [])}]
        if len(pages) != 1 or len(slides[pages[0] - 1]["videos"]) != 2:
            raise SystemExit(f"Error: los videos sin capa/A y A/B tienen que ir juntos en una diapositiva (están en {pages})")
        boxes = [v["box"] for v in slides[pages[0] - 1]["videos"]]
        if boxes[0] == boxes[1]:
            raise SystemExit(f"Error: diapositiva {pages[0]}: los dos videos quedaron sobre el mismo fotograma")
    soffice = find_libreoffice()
    plan = WORK / "plan.json"
    OUTPUT.unlink(missing_ok=True)
    plan.write_text(json.dumps({"soffice": str(soffice), "output": str(OUTPUT), "slides": slides}), encoding="utf-8")
    subprocess.run([str(libreoffice_python(soffice)), str(Path(__file__).resolve()), "--libreoffice-stage", str(plan)],
                   check=True)
    n = embed_videos(OUTPUT, slides)
    total, with_video = check(OUTPUT)
    print(f"Generadas {len(total)} diapositivas, {n} videos embebidos (diapositivas {with_video}): {OUTPUT}")


if __name__ == "__main__":
    main()
