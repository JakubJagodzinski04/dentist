# 👁️ Moduł Wizyjny SAM3 (Vision Pipeline) - Dashboard Wersjonowania

Katalog ten stanowi kompletne środowisko percepcji 2D dla projektu chirurgicznego robota TIAGo Pro. Architektura opiera się na zasadzie modułowości oraz równoległego rozwijania niezależnych wersji oprogramowania (side-by-side development). Pozwala to na bezpieczne testowanie algorytmów bez ryzyka destabilizacji głównego rurociągu produkcyjnego.

---

## 🗂️ Architektura i Mapa Folderów

Katalog zorganizowany jest w trzy niezależne obszary: produkcyjny, testowy oraz historyczny (punkt odniesienia).

### 1. Rdzeń Produkcyjny (Aktualna Wersja)
* **`ros2_ws/`** Główny, skompilowany obszar roboczy ROS 2 Humble. Zawiera zoptymalizowany pod kątem FPS węzeł `sam_tracker` (algorytmy Async Drop oraz Grace Period) zlokalizowany w paczce `vision_pipeline`.
* **`Dockerfile`** Definicja bazowego kontenera produkcyjnego zoptymalizowanego pod kątem obsługi ciężkich wag modelu SAM3 na GPU.
* **`HOWTO_RUN.md`** 🔴 **[ZACZNIJ TUTAJ]** Aktualna, szczegółowa instrukcja sekwencji startowej dla całego zintegrowanego systemu 2D/3D.
* **`moje_fastdds.xml`** Konfiguracja middleware usuwająca dławienie sieci (pakiety UDP powyżej 65 KB) podczas transmisji masek o wysokiej rozdzielczości.
* **`queries.json`** Słownik wejściowy z promptami narzędzi dla aktualnie uruchomionego modelu AI.

### 2. Środowisko Walidacji i Testów Wsadowych (Izolowana Piaskownica)
* **`test_sam3/`** Całkowicie autonomiczny podmoduł przeznaczony do testów typu bench-marking i ad-hoc.
  * Posiada własny, niezależny **`Dockerfile`** chroniący konfigurację produkcyjną przed instalacją pobocznych bibliotek.
  * Zawiera skrypty automatyzujące (`test_batch_sam3.py`, `test_batch_annotate_sam3.py`) do masowego przetwarzania i adnotacji statycznych baz obrazów testowych znajdujących się w podfolderach `input/` i `output/`.

### 3. Archiwum Wersji Stabilnych (Regresja i Punkty Odniesienia)
* **`tiago_vision_project_30-05-2026/`** Zamrożona, w pełni funkcjonalna migawka systemu z dnia 30 maja 2026. 
  * Zawiera pierwotną implementację węzła wizyjnego (`sam3_live_node.py`) wraz z jej oryginalnym środowiskiem uruchomieniowym (`Dockerfile`).
  * Pozostawiona w strukturze projektu jako nienaruszalny punkt odniesienia (Baseline) do testów porównawczych wydajności oraz stabilności masek po wdrożeniu nowych optymalizacji w głównym rurociągu.

---

## 🚀 Uruchomienie i Eksploatacja

Każdy z wyżej wymienionych modułów posiada własny cykl życia. W celu uruchomienia aktualnej, zintegrowanej wersji produkcyjnej, należy przejść bezpośrednio do instrukcji zawartej w pliku **`HOWTO_RUN.md`**. Prace badawcze i testy skryptowe należy bezwzględnie ograniczyć do przestrzeni katalogu `test_sam3/`.
