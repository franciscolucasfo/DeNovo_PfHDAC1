#!/bin/bash

# =========================
# Generar SMILES + Name + InChI + Propiedades del INDEX (PARALELIZADO)
# =========================

# Función para procesar un archivo mol2
process_mol2() {
    f="$1"
    index_file="$2"
    
    # SMILES usando nombre del archivo (-xk)
    smiles=$(obabel "$f" -osmi --canonical -xk 2>/dev/null | cut -f1)
    
    # Nombre del archivo sin extensión, incluyendo la carpeta
    folder=$(basename "$(dirname "$f")")
    name=$(basename "${f%.mol2}")
    full_name="${folder}/${name}"
    
    # InChI de la molécula
    inchi=$(obabel "$f" -oinchi 2>/dev/null)
    
    # Extraer propiedades del INDEX
    formula=""
    mw=""
    logp=""
    pkd=""
    struct=""
    synth=""
    chem=""
    
    if [ -f "$index_file" ]; then
        # Buscar la línea correspondiente en el INDEX
        mol2_basename=$(basename "$f")
        index_line=$(grep -v "^#" "$index_file" | grep "$mol2_basename")
        
        if [ -n "$index_line" ]; then
            formula=$(echo "$index_line" | awk '{print $2}')
            mw=$(echo "$index_line" | awk '{print $3}')
            logp=$(echo "$index_line" | awk '{print $4}')
            pkd=$(echo "$index_line" | awk '{print $5}')
            struct=$(echo "$index_line" | awk '{print $6}')
            synth=$(echo "$index_line" | awk '{print $7}')
            chem=$(echo "$index_line" | awk '{print $8}')
        fi
    fi
    
    # Retornar la línea CSV
    echo "${smiles};${full_name};${inchi};${formula};${mw};${logp};${pkd};${struct};${synth};${chem}"
}

export -f process_mol2

# Crear archivo temporal para resultados
tmp_file=$(mktemp)

# Crear el encabezado
echo "SMILES;Name;InChI;Formula;MW;LogP;pKd;Structure;Synthesize;Chemical" > extracted_denovo.csv

# Buscar arquivos mol2 nas pastas de 1 a 30 y procesarlos en paralelo
for i in {1..30}; do
    if [ -d "$i" ]; then
        index_file="$i/INDEX"
        find "$i" -maxdepth 1 -name "*.mol2" -type f | \
            parallel -j+0 process_mol2 {} "$index_file" >> "$tmp_file"
    fi
done

# Agregar resultados al archivo final
cat "$tmp_file" >> extracted_denovo.csv

# Limpiar archivo temporal
rm "$tmp_file"

echo "SMILES + InChI + Propiedades generados en extracted_denovo.csv (procesamiento paralelo completado)"
