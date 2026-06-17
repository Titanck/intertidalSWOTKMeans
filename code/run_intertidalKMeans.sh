#!/bin/bash
declare -a tokens
OutputEPSG=2154
fichier_params=.././data/params.txt
# Vérifications préliminaires
if [ ! -f "IntertidalKMeans.py" ]; then
    echo "Erreur : Le fichier IntertidalKMeans.py n'existe pas dans le répertoire courant."
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "Erreur : Python n'est pas installé ou n'est pas dans le PATH."
    exit 1
fi

while IFS= read -r ligne; do
    if $skip_first_line; then
        skip_first_line=false
        continue
    fi
    if [[ -z "$ligne" ]]; then
        continue
    fi
    AOIName=$(echo "$ligne" | awk '{print $1}')
    AOIType=$(echo "$ligne" | awk '{print $2}')
    start_date=$(echo "$ligne" | awk '{print $3}')
    end_date=$(echo "$ligne" | awk '{print $4}')
    DataWebsite=$(echo "$ligne" | awk '{print $5}')
    Method=$(echo "$ligne" | awk '{print $6}' | sed 's/^ *//;s/ *$//' | sed 's/^$/Kmeans/')
    Reso=$(echo "$ligne" | awk '{print $7}' | sed 's/^ *//;s/ *$//' | sed 's/^$/20/')
    WaterThreshold=$(echo "$ligne" | awk '{print $8}' | sed 's/^ *//;s/ *$//' | sed 's/^$/1/')
    DistMaxInterpo=$(echo "$ligne" | awk '{print $9}' | sed 's/^ *//;s/ *$//' | sed 's/^$/2e3/')
    Interpolateur=$(echo "$ligne" | awk '{print $10}' | sed 's/^ *//;s/ *$//' | sed 's/^$/Moyenne/')
    MAJ_data=$(echo "$ligne" | awk '{print $11}' | sed 's/^ *//;s/ *$//' | sed 's/^$/True/')
    
    echo "Zone d'intérêt : ${AOIName}"
    echo "Réolution finale : ${Reso}"
    # Appel du script Python
    mkdir -p "../Logs/${AOI}/"
    log_file=".././Logs/${AOI}/log_${AOI}_${start_date}_${end_date}_${reso_script}m.txt"
    python IntertidalKMeans.py $AOIName $AOIType $start_date $end_date $Reso $Method $WaterThreshold $DistMaxInterpo $OutputEPSG $DataWebsite $Interpolateur $MAJ_data 2> "$log_file" | tee "$log_file"

done < $fichier_params
echo "Tous les traitements sont terminés."
