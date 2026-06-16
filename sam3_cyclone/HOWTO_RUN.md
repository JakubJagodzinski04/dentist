# 🚀 Instrukcja uruchomienia: Węzeł SAM3 (Zero-Shot Tracking) - Wersja Cyclone

Poniższy poradnik przeprowadza przez proces uruchomienia sterylnego środowiska sztucznej inteligencji, podpięcia źródła obrazu i wizualizacji wygenerowanych masek. Całość działa w architekturze ROS 2 Humble i opiera się na wydajnym silniku **CycloneDDS**.

**Ważne przed startem:** Upewnij się, że w folderze `sam3_cyclone` znajduje się Twój prywatny plik `.env` z kluczem Hugging Face (`HF_TOKEN=...`) oraz odchudzony plik `queries.json` (zawierający maksymalnie 2-3 narzędzia dla zachowania płynności FPS i odciążenia VRAM).

---

## Krok 1: Inicjalizacja środowiska AI (Terminal 1)

Budujemy i podnosimy czysty kontener obliczeniowy.

1. Przejdź do nowego folderu modułu SAM3:
```bash
cd ~/robotics/dentist/sam3_cyclone
```
Zbuduj obraz od zera (wymagane ze względu na nową architekturę):

```Bash
docker build -t tiago_vision_cyclone_container .
```
Uruchom kontener z mapowaniem sprzętu (podmontuje to obecny folder do /workspace):

```Bash
xhost +local:root
docker run -it --rm --gpus all --net host --privileged --env-file .env -v /tmp/.X11-unix:/tmp/.X11-unix:rw -e DISPLAY=$DISPLAY -v $(pwd):/workspace --name tiago_vision tiago_vision_cyclone_container bash
```
Wewnątrz kontenera załaduj środowisko i przeprowadź sterylną kompilację paczki:

```Bash
cd /workspace/ros2_ws
source /opt/ros/humble/setup.bash
rm -rf build/ install/ log/
colcon build --packages-select vision_pipeline --symlink-install
source install/setup.bash
```
[KRYTYCZNE] Wymuś zunifikowany silnik CycloneDDS i wystartuj węzeł ze wskazanym słownikiem:

```Bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run vision_pipeline sam_tracker --ros-args -p query_file:="/workspace/queries.json"
```
Czekaj na komunikat gotowości z modelu SAM3.

Krok 2: Uruchomienie strumienia wideo (Terminal 2)
Otwórz drugi, natywny terminal w systemie Ubuntu.

Opcja A: Symulator (mock_camera / rosbag)
Jeśli testujesz system bez sprzętu medycznego:

```Bash
cd ~/robotics/dentist/mock_camera
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
./sim_orbbec_camera.sh
```
Opcja B: Kamera fizyczna (Orbbec Live)
Uruchom dedykowany moduł sprzętowy, omijający blokady sieciowe Dockera:

```Bash
cd ~/robotics/dentist/orbbec_live
./run_live.sh
```
Krok 3: Wizualizacja efektów (Terminal 3)
Podgląd wyników na natywnej instalacji ROS 2 na Ubuntu.

Uruchom interfejs RViz2 upewniając się, że jest w tej samej podsieci DDS co nowe kontenery:

```Bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
rviz2
```
Konfiguracja podglądu:

Dodaj obraz: Add -> By topic -> /sam3/smoothed_mask.

Zmień Reliability Policy na Best Effort, aby uniknąć przerw w renderowaniu przy dużym obciążeniu.
