# Chequeo de máquina (D12), para usar con `source` desde runtime_tp4.sh y control_tp3.sh.
# check_machine_tp3 ARCHIVO PERMITIR: compara hostname, $PROCESSOR_IDENTIFIER y java (vendor + versión) con
# TP4/bench/maquina_tp3.properties. Con PERMITIR=true (--allow-other-machine) no compara y lo avisa.
# Deja MACHINE_CHECK=ok|omitido; si un campo falta o no coincide, termina el script con código 5.

check_machine_tp3() {
    local ref="$1" allow="$2" host cpu props java_now key expected actual
    local errors=()
    host="$(hostname | tr -d '\r')"
    cpu="${PROCESSOR_IDENTIFIER:-}"
    props="$(java -XshowSettings:properties -version 2>&1 | tr -d '\r')"
    java_now="$(sed -n 's/^ *java\.vendor = //p' <<< "$props" | head -n 1) $(sed -n 's/^ *java\.version = //p' <<< "$props" | head -n 1)"

    if [[ "$allow" == true ]]; then
        MACHINE_CHECK=omitido
        echo "AVISO: --allow-other-machine: chequeo de máquina omitido (hostname=$host | cpu=$cpu | java=$java_now)." >&2
        echo "       Los tiempos de esta corrida no valen como medición de la máquina de TP3." >&2
        return 0
    fi
    [[ -f "$ref" ]] || { echo "Error: no existe $ref (referencia de la máquina de TP3)." >&2; exit 5; }
    for key in hostname processor_identifier java_version; do
        expected="$(sed -n "s/^${key}=//p" "$ref" | head -n 1 | tr -d '\r' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
        case "$key" in
            hostname) actual="$host" ;;
            processor_identifier) actual="$cpu" ;;
            java_version) actual="$java_now" ;;
        esac
        if [[ -z "$expected" || "$expected" == "<PEGAR>" ]]; then
            errors+=("$key: falta el valor en $ref")
        elif [[ "$actual" != "$expected" ]]; then
            errors+=("$key: esperado '$expected', esta máquina '$actual'")
        fi
    done
    if ((${#errors[@]})); then
        echo "Error: esta no es la máquina de TP3 (D12):" >&2
        printf '  - %s\n' "${errors[@]}" >&2
        echo "  Solo para pruebas en otra PC: agregar --allow-other-machine (nunca en la medición)." >&2
        exit 5
    fi
    MACHINE_CHECK=ok
    echo "Máquina verificada: $host | $cpu | $java_now" >&2
}
