# ROS 2 Environment with NVIDIA CUDA & PyTorch Optimization
# Konstanty Kaszubski (Zaktualizowano pod architekturę CycloneDDS)

FROM ros:humble

# 1. System tools and ROS2 CV Bridge (USUNIĘTO usb-cam, sprzęt działa teraz w osobnym module)
RUN apt-get update && apt-get -y upgrade && apt-get -y install \
    ros-humble-desktop \
    ros-humble-cv-bridge \
    ros-humble-rmw-cyclonedds-cpp \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    nano \
    && rm -rf /var/lib/apt/lists/*

# 2. Wymuszenie CycloneDDS jako jedynego silnika ROS 2 w kontenerze (Zabezpieczenie Linkera)
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV LD_LIBRARY_PATH=/opt/ros/humble/lib:$LD_LIBRARY_PATH

# 3. Triton Engine (required for PyTorch JIT compilation)
RUN pip3 install --no-cache-dir triton

# 4. Native PyTorch installation dla GPU NVIDIA
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 5. Vision models and supporting libraries with strict versioning
RUN pip3 install --no-cache-dir \
    transformers \
    typer \
    python-dotenv \
    huggingface_hub \
    "numpy<2.0.0" \
    "Pillow>=10.0.0" \
    opencv-python

# 6. DOMYŚLNY KATALOG ROBOCZY (Wymuszenie poprawnego logowania)
WORKDIR /workspace
