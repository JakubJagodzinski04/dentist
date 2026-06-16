```markdown
# 🚀 Procedura Startowa: Zintegrowany Rurociąg Wizyjny (SAM3 + CGN)

Poniższy dokument opisuje "Złotą Sekwencję" uruchamiania całego stosu AI dla robota Tiago Pro. Architektura opiera się na wydzielonych kontenerach, natywnym wsparciu CUDA 12.8 (RTX 5060) oraz zunifikowanym silniku komunikacyjnym **CycloneDDS**.

**Wymagania:** Otwórz 4 oddzielne terminale na hoście (Ubuntu). Uruchamiaj je ściśle w podanej kolejności.

---

## 🟢 Terminal 1: Nasłuch AI (Węzeł SAM3)
Uruchamiamy rdzeń śledzący, który alokuje VRAM i czeka na obraz.

```bash
cd ~/robotics/dentist/sam3_cyclone
xhost +local:root
docker run -it --rm --gpus all --net host --privileged --env-file .env -v /tmp/.X11-unix:/tmp/.X11-unix:rw -e DISPLAY=$DISPLAY -v $(pwd):/workspace --name tiago_vision tiago_vision_cyclone_container bash

# Wewnątrz kontenera:
cd /workspace/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run vision_pipeline sam_tracker --ros-args -p query_file:="/workspace/queries.json"

```

*⏳ Czekaj, aż model załaduje wagi do pamięci i odtworzy dźwięk (dzwonek).*

---

## 🟣 Terminal 2: Kaskada Chwytów (Węzeł Contact-GraspNet)

Uruchamiamy węzeł chwytaka, który nasłuchuje masek wygenerowanych przez SAM3.

```bash
cd ~/robotics/dentist/contact-graspnet
xhost +local:root
docker run -it --rm --gpus all --net host --privileged -v /tmp/.X11-unix:/tmp/.X11-unix:rw -e DISPLAY=$DISPLAY -v $(pwd):/workspace/contact-graspnet --name cgn_vision cgn_vision_container bash

# Wewnątrz kontenera:
cd /workspace/contact-graspnet/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
export LD_LIBRARY_PATH=/opt/ros/humble/lib:$LD_LIBRARY_PATH
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run grasp_generator cgn_event_node --ros-args -p use_mock_camera:=true

```

*⏳ Czekaj na komunikat: `🟣 TRYB SYMULACJI (Mock). Ignoruję /camera_info.*`

---

## 👁️ Terminal 3: Podgląd Operacyjny (RViz2)

Nie uruchamiamy środowiska na hoście. Wchodzimy do działającego kontenera SAM3, aby współdzielić tę samą przestrzeń sieciową i biblioteki.

```bash
docker exec -it tiago_vision bash

# Wewnątrz nowej powłoki kontenera:
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
rviz2

```

*⚙️ Konfiguracja RViz2:*

1. **[KRYTYCZNE] Global Options -> Fixed Frame:** Zmień z domyślnego `map` na ramkę odniesienia kamery (np. `camera_color_optical_frame` lub `camera_link`).
2. **Maski (SAM3):** `Add -> By topic -> /sam3/smoothed_mask` (Zmień *Reliability Policy* na *Best Effort*).
3. **Chmura Punktów (Point Cloud):** `Add -> By topic` i wybierz chmurę punktów z kamery.
4. **Wektory Chwytów (CGN):** `Add -> By topic -> /cgn/grasp_markers` (MarkerArray).

---

## 🎥 Terminal 4: Uderzenie Danych (Mock Camera / Hardware)

Mając gotowy układ nerwowy, wpuszczamy do niego dane z czujników. Moduł kamery uruchamiamy bezpośrednio z hosta, zachowując ten sam język komunikacji.

```bash
cd ~/robotics/dentist/mock_camera
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
./sim_orbbec_camera.sh

```

*Wygenerowane klatki natychmiast trafią do Terminala 1, stamtąd maski polecą do Terminala 2, a wygenerowane pozycje chwytaka zmaterializują się w Terminalu 3.*

```

```