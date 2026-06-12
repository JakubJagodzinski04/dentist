# 🚀 Instrukcja uruchomienia: Moduł Contact-GraspNet (Kaskada Zdarzeniowa)

Ten dokument opisuje procedurę uruchomienia węzła generującego trójwymiarowe chwyty (6DoF) dla robota TIAGo Pro. 
Moduł działa w zautomatyzowanej architekturze **Event-Driven Pipeline** – wybudza się automatycznie wyłącznie wtedy, gdy otrzyma udaną maskę segmentacyjną od sieci SAM3.

**Wymagania wstępne:**
Zanim uruchomisz ten węzeł, w systemie MUSZĄ działać:
1. Źródło obrazu RGB i Głębi (np. `mock_camera` lub fizyczna kamera Orbbec). Oczekiwana rozdzielczość: VGA (640x480).
2. Węzeł `sam_tracker` publikujący zsynchronizowane maski na temat `/sam3/smoothed_mask`.

---

## Krok 1: Inicjalizacja wyizolowanego kontenera (Terminal 1)

Węzeł CGN korzysta z oddzielnego środowiska PyTorch, aby uniknąć konfliktów zależności z systemem SAM3.

1. Przejdź do folderu modułu:
   ```bash
   cd ~/robotics/dentist/contact-graspnet

```

2. Jeśli jeszcze tego nie zrobiłeś, zbuduj obraz (wymagane tylko raz):
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

Z uwagi na ogromny rozmiar przesyłanych klatek RGBD oraz masek, standardowy protokół FastDDS ulega przepełnieniu bufora (błąd UDP). Konieczne jest wymuszenie niestandardowego profilu sieciowego.

1. W terminalu działającego kontenera załaduj środowisko i zbuduj paczkę:
```bash
cd /workspace/contact-graspnet/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select grasp_generator
source install/setup.bash

```


2. **[KRYTYCZNE]** Wyeksportuj powiększony profil FastDDS (omija błąd `sequence size exceeds remaining buffer`):
```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=/workspace/contact-graspnet/moje_fastdds.xml

```


3. Uruchom zautomatyzowany węzeł zdarzeniowy:
```bash
ros2 run grasp_generator cgn_event_node

```



*Sukces:* Węzeł wypisze komunikat `🟢 CGN Event Node gotowy` i zapadnie w sen, nasłuchując masek z SAM3. Gdy maska się pojawi, węzeł przetworzy chmurę punktów i wyrzuci log o zwolnieniu blokady GPU.

---

## Krok 3: Wizualizacja Chwytów 3D (Terminal 2)

Wyniki pracy sieci Contact-GraspNet są rzutowane bezpośrednio do przestrzeni trójwymiarowej w formacie `MarkerArray`.

1. Otwórz nowy, natywny terminal Ubuntu i uruchom RViz2:
```bash
source /opt/ros/humble/setup.bash
rviz2

```


2. Upewnij się, że w *Global Options* pole **Fixed Frame** jest ustawione na `camera_link` (lub odpowiednią ramkę Twojej kamery głębi).
3. Kliknij **Add** w lewym dolnym rogu -> **By topic** -> wybierz `/cgn/grasp_markers`.

Z powodu zaimplementowanego mechanizmu *Frame Dropping*, znaczniki chwytaka (zielone prostopadłościany odpowiadające rozwarciu szczęk TIAGo) będą aktualizować się na ekranie asynchronicznie, chroniąc kartę RTX 5060 przed przeciążeniem VRAM.
