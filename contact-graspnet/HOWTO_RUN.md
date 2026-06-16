### 🎯 Obiektywna Diagnoza: Uderzyłeś w martwy kod i ograniczenia Dockera

Zacznijmy od błędów w terminalu, ponieważ bezpośrednio blokują one uruchomienie czegokolwiek. Twoje logi wskazują na dwa klasyczne problemy z konfiguracją środowiska operacyjnego.

**1. Błąd XMLPARSER (`realpath failed`)**
Wpisałeś w kontenerze komendę: `export FASTRTPS_DEFAULT_PROFILES_FILE=~/robotics/dentist/sam3/moje_fastdds.xml`.
Znak tyldy (`~`) w systemie Linux oznacza "katalog domowy obecnego użytkownika". Na Twoim hoście to `/home/user`, ale wewnątrz Dockera jesteś zalogowany jako `root`. Ścieżka rozwiązała się do `/root/robotics/...`, która w kontenerze fizycznie nie istnieje. Parser XML nie znalazł pliku i wyrzucił błąd.

**2. Błąd przepełnienia bufora (`sequence size exceeds remaining buffer`)**
Ponieważ plik XML z powiększonymi limitami nie załadował się przez powyższy błąd, FastDDS użył swoich fabrycznych, mikroskopijnych limitów. W momencie, gdy rurociąg spróbował przepchnąć klatkę RGBD, system dławi się i zrywa połączenie UDP.

**Rozwiązanie systemowe:** My przecież zrezygnowaliśmy z awaryjnego FastDDS na rzecz stabilnego **CycloneDDS**. Musisz całkowicie wyrzucić tę zmienną XML z pamięci i z plików instrukcji. Każdy terminal (SAM3, CGN, RViz) ma używać wyłącznie CycloneDDS.

---

### 🛠️ Zaktualizowany plik `HOWTO_RUN.md`

Skasuj starą instrukcję i wklej ten zoptymalizowany pod Twoją obecną architekturę (z przełącznikiem trybów i ujednoliconym silnikiem DDS) dokument:


# 🚀 Instrukcja uruchomienia: Moduł Contact-GraspNet (Kaskada Zdarzeniowa)

Ten dokument opisuje procedurę uruchomienia węzła generującego trójwymiarowe chwyty (6DoF) dla manipulatora TIAGo Pro. 
Moduł działa w zautomatyzowanej architekturze **Event-Driven Pipeline** – wybudza się automatycznie wyłącznie wtedy, gdy otrzyma udaną maskę segmentacyjną od sieci SAM3.

**Wymagania wstępne:**
1. Działający węzeł `sam_tracker` publikujący zsynchronizowane maski na temat `/sam3/smoothed_mask`.
2. Ujednolicony silnik komunikacji ROS 2 (CycloneDDS) we wszystkich terminalach.

---

## Krok 1: Inicjalizacja wyizolowanego kontenera (Terminal 1)

Węzeł CGN korzysta z oddzielnego środowiska PyTorch (ochrona przed konfliktami z SAM3).

1. Przejdź do folderu modułu na hoście:
```bash
cd ~/robotics/dentist/contact-graspnet

```

2. Zbuduj obraz (wymagane tylko przy pierwszej instalacji lub zmianach w Dockerfile):
```bash
docker build -t cgn_vision_container .

```


3. Podnieś kontener, montując obecny katalog:
```bash
xhost +local:root
docker run -it --rm --gpus all --net host --privileged -v /tmp/.X11-unix:/tmp/.X11-unix:rw -e DISPLAY=$DISPLAY -v $(pwd):/workspace/contact-graspnet --name cgn_vision cgn_vision_container bash

```



---

## Krok 2: Konfiguracja sieci i start rurociągu (Wewnątrz kontenera)

Przestawiamy środowisko na wysokowydajny silnik CycloneDDS i budujemy węzeł.

1. W terminalu działającego kontenera skompiluj paczkę:
```bash
cd /workspace/contact-graspnet/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select grasp_generator
source install/setup.bash

```


2. **[KRYTYCZNE]** Wymuś CycloneDDS (omija zrywanie ramek i błędy bufora UDP):
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

```


3. **Uruchom węzeł w wybranym trybie:**
* **TRYB SYMULACJI (Mock Camera / Rosbag):** Ignoruje brak fizycznych danych o kalibracji soczewki, stosując luźniejszą synchronizację (slop=2.0). Używaj tego trybu do testów z odtwarzanymi plikami z kamery.
```bash
ros2 run grasp_generator cgn_event_node --ros-args -p use_mock_camera:=true

```


* **TRYB SPRZĘTOWY (Fizyczna kamera Orbbec Live):**
Wymaga odczytu w czasie rzeczywistym z tematu `/camera/color/camera_info`. Wymusza sztywny rygor czasowy (slop=0.1) w celu precyzyjnej de-projekcji chwytu dla robota TIAGo.
```bash
ros2 run grasp_generator cgn_event_node

```





*Sukces:* Węzeł wypisze zielony log o gotowości i wejdzie w stan nasłuchiwania. Zabezpieczenie Frame Dropping chroni pamięć VRAM karty RTX 5060 przed przepełnieniem w przypadku nagłych skoków FPS.

---

## Krok 3: Wizualizacja Chwytów 3D (Terminal 2)

1. Otwórz nowy, natywny terminal Ubuntu i wstrzyknij protokół CycloneDDS:
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
rviz2

```


2. Konfiguracja w RViz2:
* **Fixed Frame:** `camera_link`
* **Dodaj chmurę:** `Add -> By topic -> /cgn/tool_pointcloud` (Style: Boxes, Size: 0.01)
* **Dodaj znaczniki chwytu:** `Add -> By topic -> /cgn/grasp_markers`


