#!/bin/bash

# Zatrzymanie i usunięcie starego kontenera, jeśli istnieje
docker stop orbbec_live_container 2>/dev/null
docker rm orbbec_live_container 2>/dev/null

echo "🛠️ Budowanie zoptymalizowanego obrazu sprzętowego (Orbbec + CycloneDDS)..."
docker build -t orbbec_live_image .

echo "🚀 Uruchamianie sterownika kamery (Sieć Hosta, Pełen dostęp USB)..."
# Tłumaczenie flag:
# --network host: Kontener widzi SAM3 w tej samej sieci.
# --privileged i -v /dev:/dev: Kontener ma absolutny dostęp do fizycznego portu USB w laptopie.
docker run -it \
    --name orbbec_live_container \
    --network host \
    --privileged \
    -v /dev:/dev \
    orbbec_live_image
