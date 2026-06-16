# ⚙️ SAM3 Tracker - Specyfikacja Techniczna i Algorytmiczna

Węzeł `sam_tracker` nie jest wyłącznie warstwą abstrakcji (wrapperem) dla modelu Meta SAM3. Realizuje on krytyczną rolę pośrednika (middleware) pomiędzy asynchronicznym źródłem wizji (kamera) a synchronicznym rurociągiem obliczeniowym 6DoF, wprowadzając dwie autorskie heurystyki zabezpieczające.

---

## 1. Algorytm "Smart FPS" (Asynchroniczny Frame Dropping)

### Definicja Problemu
Strumień z kamery (RGB) nadaje klatki ze stałą częstotliwością, gdzie czas między klatkami to zazwyczaj $t_{cam} \approx 33.3\text{ ms}$ (dla 30 FPS).
Złożoność obliczeniowa sieci neuronowej segmentującej obraz wymaga czasu inferencji $t_{inf} \gg t_{cam}$ (często powyżej $500\text{ ms}$ na architekturze Turing/Ampere/Blackwell). 
Kolejkowanie klatek w strukturach ROS 2 bez sprzężenia zwrotnego prowadzi do wykładniczego wzrostu zajętości pamięci RAM oraz rosnącego opóźnienia (tzw. zjawisko *Backpressure*).

### Rozwiązanie
Zastosowano brutalny, sterowany zdarzeniami mechanizm odrzucania. 
Klatka $k_i$ wchodząca do bufora jest przekazywana do macierzy tensora GPU **tylko i wyłącznie**, jeśli procesor graficzny jest oznaczony jako bezczynny (flaga `is_computing = False`). W przeciwnym razie klatka $k_i$ ulega natychmiastowej destrukcji, a system czeka na klatkę $k_{i+n}$. Oszczędza to zasoby sieciowe dla modułu Contact-GraspNet.

---

## 2. Heurystyka "Grace Period" (Kompensacja Okluzji)

### Definicja Problemu
Segmentacja Zero-Shot z modelu SAM3 nie posiada wbudowanego modułu pamięci krótkotrwałej (np. LSTM). Jeżeli narzędzie medyczne (np. skalpel) zostanie przysłonięte dłonią operatora lub ramieniem robota, maska dla tej klatki znika:
$$M(x, y, t) = 0 \quad \text{dla obszaru okluzji}$$
Przesłanie pustej maski do węzła CGN spowodowałoby natychmiastowe usunięcie przestrzennego chwytu z pamięci ramienia robota (Emergency Drop).

### Rozwiązanie
Tracker implementuje bufor wygasania (Grace Period). Zdefiniujmy czas okluzji jako $\Delta t$.
Jeżeli model SAM3 nie wykryje nałożonego obiektu w czasie $t_{current}$, system weryfikuje warunek:
$$\Delta t < T_{grace}$$
* Jeśli warunek jest spełniony, węzeł publikuje sztucznie podtrzymaną maskę z klatki $t-1$.
* Jeśli $\Delta t \ge T_{grace}$, uznajemy obiekt za trwale utracony i zrzucamy maskę (Hard Reset).

Dla zachowania precyzji w dynamicznych scenariuszach (gdzie narzędzie szybko się porusza), parametr $T_{grace}$ w obecnej konfiguracji produkcyjnej został sprowadzony do minimalnych wartości, kładąc nacisk na obiektywizm położenia nad stabilnością wizualną.
