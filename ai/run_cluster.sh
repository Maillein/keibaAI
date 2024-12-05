#!/bin/bash
set -euo pipefail
cd `dirname $0`

printf "password: "
read -s password
echo ""

scale=5
proxies=(

)

# echo "$password" | sudo -S docker compose up -d --scale keiba-ai="$scale" --scale selenium="$scale"
for ((i=0; i<scale; i++)) do
    echo "$password" | sudo -S docker exec -d keibaai-keiba-ai-((i+1)) python main.py -i "$i" --proxy "${proxies[i]}"
done
