# Reglas de figuras y gráficos

## Título — la regla más incumplida

**Nunca un título/subtítulo embebido dentro del área del gráfico** (nunca `ax.set_title()`/`fig.suptitle()` por default en matplotlib, nunca en TikZ tampoco). El título va en el `\caption` de LaTeX (informe) o en el subtítulo de la diapositiva (presentación), siempre AFUERA de la imagen. Un título por default calculado queda duplicado con el caption que lo acompaña — es redundancia, no refuerzo.

Esto aplica incluso para distinguir paneles dentro de una figura combinada — ver estructura-documentos.md sobre cuándo separar en figuras independientes en vez de usar texto interno.

**Excepción real, no una laguna a explotar:** un video/animación que se reproduce SOLO (sin caption externo alrededor, por ejemplo durante la exposición oral en vivo) puede llevar overlay de texto con los parámetros (η, ρ, t) porque cumple una función real de lectura en vivo, no duplica nada. Si ese mismo contenido se entrega embebido en un documento con caption, ahí sí hay que sacar el overlay.

## Leyendas

- Preferentemente DENTRO de la figura, en la esquina con más espacio libre — no hay una esquina "default" correcta, depende de dónde estén los datos.
- Afuera de la figura solo como excepción, cuando no hay lugar claro adentro (muchas curvas).
- Con varias entradas relacionadas (ej. distintas densidades), apilarlas verticalmente, no en fila horizontal.
- Nunca dejar texto en inglés en una leyenda de un documento en español (ej. "voter"/"standard" en vez de "votante"/"estándar") — si el dato interno usa nombres en inglés, traducir solo en la etiqueta visible, no tocar los identificadores de datos.

## Escala de ejes

Para magnitudes naturalmente acotadas en [0,1] (fracciones, proporciones): mostrar la escala completa [0,1] para dar una idea honesta de la magnitud real del efecto. Si hace falta revelar estructura fina (un efecto chico pero real, confirmado por barras de error), mostrar una figura ADICIONAL con zoom, explícitamente marcada como zoom — nunca reemplazar la vista de escala completa por la zoomeada sin aclarar.

## Cifras significativas y notación en labels

- Redondear a 1-2 dígitos significativos en labels de parámetros (ej. "ρ=0.32", no "ρ=0.3183098861...").
- Notación científica con superíndice real, nunca "1E2" ni "10^2" en texto plano.
- No repetir en el título/label de una figura algo que ya es evidente por el contexto de la sección (ej. si toda la sección ya es "modelo estándar", no hace falta repetirlo en cada figura de esa sección — pero sí en la primera figura que introduce la sección).

## Paleta de colores

Para curvas relacionadas que forman un gradiente conceptual (ej. distintos valores de un mismo parámetro como densidad), preferir una paleta perceptualmente uniforme y apta para daltonismo (Viridis, Parula) en vez de colores categóricos por default — se lee mejor como "una familia de curvas relacionadas" y convierte bien a escala de grises.

## Tamaño y legibilidad de paneles múltiples

Con 3+ paneles/curvas en una sola figura, cuidado con comprimir demasiado — si cada panel ya tiene su propia leyenda y barras de error, apretar el ancho los vuelve ilegibles. Preferir apilar verticalmente (más alto, ocupa más espacio de página) antes que comprimir horizontalmente, si el contenido no entra cómodo en fila.

## Animaciones — entrega vs presentación en vivo

- **Presentación en vivo:** el video se reproduce ahí mismo (funciona con PowerPoint/Google Slides con video insertado; con PDF puro puede no funcionar, confirmar).
- **PDF que se entrega:** solo una imagen fija (screenshot representativo) + link explícito a la animación — la animación NUNCA se embebe en el PDF de entrega. Son dos versiones de archivo distintas generadas del mismo contenido.
- Con varias animaciones comparadas, mejor mostrar menos por diapositiva (2, no 3) para que no queden chicas — que cambie solo UNA variable entre las animaciones comparadas en una misma diapositiva.
