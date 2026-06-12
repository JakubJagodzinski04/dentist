# 🏗️ Architektura Integracji: Contact-GraspNet (CGN) dla TIAGo Pro

**Dokument Projektowy Systemu Generowania Chwytów Przestrzennych (6DoF)**

Ten moduł odpowiada za transformację płaskich masek 2D (wygenerowanych przez sieć SAM3) na trójwymiarowe, stabilne punkty chwytu dla efektora końcowego robota. Moduł został zaprojektowany z bezwzględnym naciskiem na optymalizację pamięci VRAM oraz fizyczną zgodność z kinematyką robota TIAGo.

---

## 1. Wybór Technologii i Repozytorium Bazowego

Po analizie dostępnych implementacji, moduł opiera się na **nieoficjalnym porcie PyTorch** (`elchun/contact_graspnet_pytorch`), a nie na oryginalnym repozytorium NVIDIA (TensorFlow).

**Uzasadnienie inżynieryjne:**
* **Uniknięcie OOM (Out Of Memory):** TensorFlow domyślnie alokuje 100% dostępnej pamięci VRAM. Na karcie 8GB (RTX 5060), przy działającym w tle modelu SAM3, doprowadziłoby to do natychmiastowego błędu `CUDA Out of Memory`.
* **Współdzielenie VRAM:** Użycie PyTorch pozwala na sprzętowe ograniczenie zużycia pamięci w kodzie inicjalizacyjnym węzła (np. `torch.cuda.set_per_process_memory_fraction(0.4)`), co gwarantuje stabilną koegzystencję obu sieci neuronowych.
* **Kompatybilność Architektury:** Natywna współpraca ze sterownikami CUDA 12 (Blackwell) bez konieczności karkołomnej kompilacji starych bibliotek TF z 2021 roku.

---

## 2. Dopasowanie Kinematyki (Fizyka Chwytaka)

Wygenerowane przez sztuczną inteligencję wektory chwytu muszą odzwierciedlać fizyczne ograniczenia robota. Oparcie się na domyślnych wagach chwytaka Franka Emika Panda doprowadziłoby do kolizji z blatem (tzw. *stand-off error*) lub zgniecenia narzędzi endodontycznych.

Model integruje parametry konfiguracyjne z repozytorium `jucamohedano/ros_contact_graspnet`, które modyfikują macierz generacji specjalnie pod **chwytak PAL Robotics (TIAGo)**:
* Dopasowana maksymalna głębokość penetracji palców.
* Precyzyjna szerokość rozwarcia szczęk (odpowiednia dla strzykawek i blistrów z pilnikami).

---

## 3. Paradygmat Wykonania: ROS 2 Service (Zamiast Publishera)

Z uwagi na potężne obciążenie jednostki obliczeniowej przetwarzaniem chmur punktów, węzeł CGN **nie działa w sposób ciągły** (Real-Time). Został zaprojektowany jako usługa asynchroniczna.

**Przepływ Logiki:**
1. Ramie TIAGo ustawia się w pozycji obserwacyjnej nad stołem.
2. System nadrzędny wysyła żądanie do serwera `/generate_grasp_from_mask`.
3. Węzeł CGN pobiera za pomocą `message_filters` tylko jedną, zsynchronizowaną próbkę czasową z czterech tematów:
   * `/image_raw` (RGB)
   * `/depth/image_raw` (Głębia)
   * `/sam3/smoothed_mask` (Maska 2D)
   * `/camera_info` (Macierz K)
4. Moduł mapuje głębię na chmurę punktów, a następnie używa maski SAM3 jako "cięcia laserowego" – odrzuca wszystkie punkty poza obrysem narzędzia (eliminacja blatu stołu).
5. Sieć wylicza i publikuje w odpowiedzi listę Top-5 najstabilniejszych chwytów (Macierze Translacji i Rotacji 6DoF), po czym zwalnia zasoby GPU.

---

## 4. Struktura Modułu

System zachowuje ścisłą izolację wewnątrz odrębnego kontenera Docker, zapobiegając konfliktom zależności (`dependency hell`) z potokiem wizyjnym.

```text
/workspace/contact-graspnet/
├── Dockerfile                  # Wyizolowane środowisko (PyTorch + Open3D)
├── HOWTO_RUN.md                # Instrukcja uruchomienia usługi
├── config/
│   └── tiago_gripper.yaml      # Parametry kinematyczne chwytaka PAL
├── weights/
│   └── checkpoints.pt          # Przetrenowane wagi modelu CGN
└── ros2_ws/
    └── src/
        └── grasp_generator/
            ├── package.xml
            └── grasp_generator/
                └── cgn_service.py # Główny węzeł serwera ROS 2

```
