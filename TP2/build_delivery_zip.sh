#!/usr/bin/env bash
# Arma el ZIP de codigo del TP2 (entregable "c" del enunciado).
#
# Contenido: SOLO el motor de simulacion del TP2 y las clases de TP1 de las que
# depende. Queda deliberadamente afuera todo lo demas del repo: tests, scripts de
# Python (graficado/animacion/sweeps), informe, presentacion, documentacion,
# output de simulaciones, target/ y .git/.
#
# Ademas de empaquetar, verifica la entrega: extrae el ZIP en un directorio
# aislado y lo compila con un repositorio Maven local vacio, para probar que el
# codigo entregado se builda solo, sin nada del repo de desarrollo.
#
# Uso:   bash TP2/build_delivery_zip.sh
# Salida: TP2/generated/SdS_TP2_2026Q2G02CS_Codigo.zip
set -euo pipefail

# --- Configuracion -----------------------------------------------------------
# Nomenclatura pedida por el enunciado: SdS_TP2_2026Q2GXXCSS_Codigo
# (XX = numero de grupo, SS = comision).
GRUPO="${GRUPO:-02}"
COMISION="${COMISION:-S}"
ZIP_NAME="SdS_TP2_2026Q2G${GRUPO}C${COMISION}_Codigo.zip"
MAX_ZIP_KB="${MAX_ZIP_KB:-256}"   # el enunciado pide "del orden de los kb"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/TP2/generated"

# Clases de TP1 de las que depende el motor del TP2 (cierre transitivo).
# NeighborLookup usa NeighborFinder + Particle; los comandos usan CellIndexMethod.
TP1_CLASSES=(
    Particle.java
    NeighborFinder.java
    CellIndexMethod.java
)

# --- Directorios de trabajo --------------------------------------------------
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
STAGE="$WORK/${ZIP_NAME%.zip}"
TESTDIR="$WORK/build-test"
LOCALREPO="$WORK/m2-empty-repo"

echo "== 1. Staging =="
mkdir -p "$STAGE/TP1/src/main/java/ar/edu/itba/sds/tp1" "$STAGE/TP2/src/main"

for cls in "${TP1_CLASSES[@]}"; do
    src="$REPO_ROOT/TP1/src/main/java/ar/edu/itba/sds/tp1/$cls"
    [ -f "$src" ] || { echo "ERROR: falta la clase de TP1 '$cls' en $src" >&2; exit 1; }
    cp "$src" "$STAGE/TP1/src/main/java/ar/edu/itba/sds/tp1/"
done

# Motor del TP2: todo src/main (engine + analysis + command + Main), sin tests.
cp -r "$REPO_ROOT/TP2/src/main/." "$STAGE/TP2/src/main/"

# --- POMs de entrega ---------------------------------------------------------
# Se escriben aca en vez de copiar los del repo: los del repo declaran JUnit y
# surefire (no se entregan los tests) y el TP1 del repo apunta su manifest a una
# clase Main que este ZIP no incluye.
cat > "$STAGE/pom.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>ar.edu.itba.sds</groupId>
    <artifactId>simulacion-de-sistemas</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>pom</packaging>

    <modules>
        <module>TP1</module>
        <module>TP2</module>
    </modules>
</project>
EOF

cat > "$STAGE/TP1/pom.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!-- Solo las clases de busqueda de vecinos del TP1 que reusa el motor del TP2. -->
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>ar.edu.itba.sds</groupId>
        <artifactId>simulacion-de-sistemas</artifactId>
        <version>1.0-SNAPSHOT</version>
    </parent>

    <artifactId>tp1-cell-index-method</artifactId>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>21</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <build>
        <finalName>tp1</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.13.0</version>
            </plugin>
        </plugins>
    </build>
</project>
EOF

cat > "$STAGE/TP2/pom.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>ar.edu.itba.sds</groupId>
        <artifactId>simulacion-de-sistemas</artifactId>
        <version>1.0-SNAPSHOT</version>
    </parent>

    <artifactId>tp2-vicsek</artifactId>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>21</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <dependency>
            <groupId>ar.edu.itba.sds</groupId>
            <artifactId>tp1-cell-index-method</artifactId>
            <version>1.0-SNAPSHOT</version>
        </dependency>
    </dependencies>

    <build>
        <finalName>tp2</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.13.0</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <version>3.4.1</version>
                <configuration>
                    <archive>
                        <manifest>
                            <mainClass>ar.edu.itba.sds.tp2.Main</mainClass>
                        </manifest>
                    </archive>
                </configuration>
            </plugin>
            <!-- Shade: empaqueta las clases de TP1 dentro de tp2.jar para que sea ejecutable solo. -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.5.1</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>ar.edu.itba.sds.tp2.Main</mainClass>
                                </transformer>
                            </transformers>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
EOF

cat > "$STAGE/README.txt" <<'EOF'
Simulacion de Sistemas (72.25) - TP2: Automatas Celulares (modelo de Vicsek)
Grupo 02 - Comision S - 2026 2C

CONTENIDO
  TP2/  motor de simulacion (paquetes engine, analysis y command + Main)
  TP1/  unicamente las clases de busqueda de vecinos del TP1 que reusa el TP2
        (Particle, NeighborFinder, CellIndexMethod), declaradas como
        dependencia Maven en TP2/pom.xml -- no se copio codigo entre modulos.

REQUISITOS
  Java 21 y Maven 3.8+

COMPILAR (desde la raiz de este zip)
  mvn clean package
  -> genera TP2/target/tp2.jar (jar ejecutable, ya incluye las clases de TP1)

EJECUTAR
  java -jar TP2/target/tp2.jar <comando> [opciones]

  simulate --model=voter|standard --eta=<double> --steps=<int> --out=<archivo>
           (--n=<int> --seedIC=<long|auto> | --icFile=<archivo>) --seedLoop=<long|auto>
           [--l=10.0] [--rc=1.0] [--dt=1.0] [--v0=0.03] [--periodic=true|false]
           [--theta0=random|<radianes>]
  clusters --in=<corrida.txt> --out=<S.csv> [--stride=1]
  generate-ic --n=<int> --seedIC=<long|auto> --out=<archivo> [--l=10.0]
  benchmark-cim --in=<a.txt,b.txt,...> --out=<csv> [--warmup=50]

  Ejemplo:
    java -jar TP2/target/tp2.jar simulate --model=standard --n=200 --eta=0.5 \
         --steps=1000 --seedIC=1 --seedLoop=1 --out=corrida.txt

La simulacion escribe su output a archivo de texto; la animacion y los graficos
se generan aparte, a partir de esos archivos (no forman parte de esta entrega).
EOF

# Nota por modulo: Maven exige buildear desde la raiz (TP2 solo no resuelve el
# parent ni la dependencia sobre TP1), y el error que tira Maven en ese caso no
# lo explica. Estas notas evitan ese callejon.
for m in TP1 TP2; do
    cat > "$STAGE/$m/LEEME.txt" <<'EOF'
Este directorio es un modulo Maven: NO se compila por separado.

Correr siempre desde la raiz de este zip (el directorio de arriba):

    mvn clean package
    java -jar TP2/target/tp2.jar <comando> [opciones]

Ver README.txt en la raiz para la lista de comandos.
EOF
done

echo "-- Archivos incluidos --"
(cd "$STAGE" && find . -type f | sort)

echo "== 2. Empaquetando =="
(cd "$WORK" && zip -r -q -X "$WORK/$ZIP_NAME" "$(basename "$STAGE")" -x '*.DS_Store' -x '*/__pycache__/*')

ZIP_SIZE_KB=$(du -k "$WORK/$ZIP_NAME" | cut -f1)
echo "OK: $ZIP_NAME generado (${ZIP_SIZE_KB}K)"
if [ "$ZIP_SIZE_KB" -gt "$MAX_ZIP_KB" ]; then
    echo "ERROR: el zip pesa ${ZIP_SIZE_KB}K (limite ${MAX_ZIP_KB}K) -- se colo algo que no deberia estar." >&2
    exit 1
fi

echo "-- Chequeo: nada de output/scripts/tests/docs adentro --"
if unzip -Z1 "$WORK/$ZIP_NAME" | grep -Ei '(^|/)(target|scripts|informe|presentacion|enunciado|generated|\.git|src/test)(/|$)|\.(py|csv|png|pdf|md|txt~)$' ; then
    echo "ERROR: el zip contiene archivos que no corresponden a la entrega." >&2
    exit 1
fi
echo "OK: solo codigo fuente, poms y README."

echo "== 3. Verificacion: extraer aislado y compilar con repo Maven local vacio =="
mkdir -p "$TESTDIR"
(cd "$TESTDIR" && unzip -q "$WORK/$ZIP_NAME")
EXTRACTED="$TESTDIR/${ZIP_NAME%.zip}"
(cd "$EXTRACTED" && mvn -q -Dmaven.repo.local="$LOCALREPO" clean package)

JAR="$EXTRACTED/TP2/target/tp2.jar"
[ -f "$JAR" ] || { echo "ERROR: no se genero TP2/target/tp2.jar tras el build aislado." >&2; exit 1; }

echo "-- Smoke test 1/2: generate-ic --"
IC="$EXTRACTED/smoke_ic.txt"
java -jar "$JAR" generate-ic --n=50 --seedIC=1 --out="$IC" >/dev/null
[ -s "$IC" ] || { echo "ERROR: generate-ic no produjo output." >&2; exit 1; }

echo "-- Smoke test 2/2: simulate (ejercita el CIM de TP1) --"
RUN="$EXTRACTED/smoke_run.txt"
java -jar "$JAR" simulate --model=standard --eta=0.5 --steps=20 \
     --icFile="$IC" --seedLoop=1 --out="$RUN" >/dev/null
[ -s "$RUN" ] || { echo "ERROR: simulate no produjo output." >&2; exit 1; }
echo "OK: smoke tests pasaron ($(wc -l < "$RUN") lineas de corrida)."

echo "== 4. Copiando ZIP final =="
mkdir -p "$DEST"
cp "$WORK/$ZIP_NAME" "$DEST/"

echo "=================================================="
echo "LISTO: $DEST/$ZIP_NAME (${ZIP_SIZE_KB}K)"
echo "Compilacion standalone y ejecucion verificadas."
echo "=================================================="
