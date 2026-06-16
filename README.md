# TiagoProDentist - Tool Perception System

Projekt wykrywania i pozycjonowania narzędzi stomatologicznych w przestrzeni 3D przy użyciu zaawansowanych systemów wizyjnych oraz systemu **ROS 2**. System posiada dwa niezależne potoki (pipelines) detekcji dla robota TIAGo Pro:
1. **Szybka detekcja (YOLOv8)** - przetwarzająca dane z kamery RGB-D, publikująca obraz z detekcjami oraz chmurę punktów.
2. **Precyzyjna segmentacja Zero-Shot (SAM3)** - działająca na dedykowanym węźle z własną heurystyką śledzenia (Temporal Smoothing).

### Architektura Systemu Wieloagentowego
```mermaid
graph TD
    %% Input Data Sources
    subgraph Input_Modules ["Input Modules (CycloneDDS)"]
        Src_Sim[Simulator: mock_camera <br> './sim_orbbec_camera.sh']
        Src_Live[Physical Camera: orbbec_live <br> './run_live.sh']
    end

    %% Pipeline A: Detection (YOLO)
    subgraph YOLO_Path ["Path A: High-Speed Detection (YOLOv8)"]
        N_Yolo[ROS 2 Node: camera_and_yolo]
        P_Yolo{{YOLOv8 Model}}
        N_Yolo -->|Fast Inference| P_Yolo
        P_Yolo -->|Bounding Boxes| N_Yolo
    end

    %% Pipeline B: Precise Manipulation (SAM3 + CGN)
    subgraph Manipulation_Path ["Path B: Precise Manipulation (SAM3 + CGN)"]
        subgraph SAM3_Cont ["SAM3 Container"]
            N_Sam[Node: sam_tracker]
            P_SAM3{{SAM3 Model <br> CUDA 12.8}}
            N_Sam -->|Query| P_SAM3
            P_SAM3 -->|Inference Mask| N_Sam
        end
        subgraph CGN_Cont ["CGN Container"]
            N_Grasp[Node: cgn_event_node]
            P_Grasp{{CGN Model <br> CUDA 12.8}}
            N_Grasp -->|3D Eval| P_Grasp
            P_Grasp -->|Grasp Vectors| N_Grasp
        end
        N_Sam -->|Topic: /sam3/smoothed_mask| N_Grasp
    end

    %% Visualization
    N_Yolo -->|Topic: /yolo/detections| RViz[RViz2]
    N_Sam -.->|Mask Preview| RViz
    N_Grasp -->|Topic: /cgn/grasp_markers| RViz

    %% Logic flows
    Src_Sim & Src_Live -->|RGB Stream| N_Yolo
    Src_Sim & Src_Live -->|RGB+D Stream| N_Sam
    Src_Sim & Src_Live -.->|Raw Depth| N_Grasp

    %% Styling
    style YOLO_Path fill:#fff8e1,stroke:#fbc02d,stroke-width:2px
    style Manipulation_Path fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
```
## 🛠️ Wymagania systemowe
- System: Ubuntu 24.04 (Noble Numbat).

- Docker & Docker Compose zainstalowane na hoście.

- Sterowniki NVIDIA (wymagane dla akceleracji GPU wewnątrz kontenera).

- ROS 2 Jazzy / Humble zainstalowany lokalnie (do uruchomienia RViz2 na hoście).

📁 Struktura projektu
```scripts/yolo_to_rviz.py```: Główny węzeł ROS 2 integrujący YOLO z danymi Depth.

```weights/best.pt```: Wytrenowane wagi modelu YOLO.

```bag/```: Folder z nagraniami (RGB i Depth).

```fastdds_no_shm.xml```: Konfiguracja DDS eliminująca błędy przesuwu dużych danych (No Shared Memory).

```sam3/```: Dedykowany moduł i węzeł ROS 2 dla precyzyjnej segmentacji instancji (SAM3). Szczegółowa instrukcja uruchomienia tego potoku znajduje się w sam3/README.md.

## 🚀 Szybki start (Potok YOLOv8)
# 1. Budowanie i uruchomienie kontenera
Będąc w głównym folderze projektu, wykonaj:
```Bash
docker compose build
docker compose up -d
```

# 2. Uruchomienie węzła percepcji
Wejdź do kontenera i odpal skrypt:
```Bash
docker exec -it TiagoProDentist bash
source /opt/ros/jazzy/setup.bash
python3 scripts/yolo_to_rviz.py
```

# 3. Wizualizacja w RViz2 (Na Hoście)
Aby zobaczyć wyniki, otwórz nowy terminal na Ubuntu i:

Uruchom publikator statycznego układu współrzędnych:
```Bash
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map camera_color_optical_frame
```

Uruchom RViz2:
```rviz2```

W RViz skonfiguruj:

- Fixed Frame: map

- Image Topic: /detected_tool_image (Reliability: Reliable)

- PointCloud2 Topic: /detected_tool_pc (Reliability: Reliable)

## ⚠️ Rozwiązywanie problemów
- Brak obrazu w RViz: Upewnij się, że na hoście i w Dockerze ustawiono zmienną środowiskową dla FastDDS: ```export FASTRTPS_DEFAULT_PROFILES_FILE=/Shared/fastdds_no_shm.xml.```

- Błąd rclpy: Pamiętaj o wykonaniu ```source /opt/ros/jazzy/setup.bash``` wewnątrz kontenera przed uruchomieniem skryptu.
