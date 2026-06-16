# Środowisko ROS 2 dla Contact-GraspNet (PyTorch Port)
# Zoptymalizowane pod GPU RTX 5060 i chmury punktów 3D

FROM ros:humble

# 1. Narzędzia systemowe i mosty wizyjne (Bez CycloneDDS na tym etapie!)
RUN apt-get update && apt-get -y upgrade && apt-get -y install \
    ros-humble-desktop \
    ros-humble-cv-bridge \
    ros-humble-vision-msgs \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    nano \
    && rm -rf /var/lib/apt/lists/*

# 2. PyTorch natywnie pod architekturę CUDA 
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 3. Zależności Point-Cloud i matematyczne 
RUN pip3 install --no-cache-dir open3d trimesh scipy pyyaml "numpy<2.0.0" opencv-python

# 4. LEKARSTWO ARCHITEKTONICZNE: Instalacja CycloneDDS na samym końcu.
# Zmuszamy system do zbudowania linków C++ dopasowanych do obecności PyTorcha.
RUN apt-get update && apt-get install -y ros-humble-rmw-cyclonedds-cpp && rm -rf /var/lib/apt/lists/*

# 5. Wymuszenie silnika w zmiennych systemowych
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV LD_LIBRARY_PATH=/opt/ros/humble/lib:$LD_LIBRARY_PATH

# 6. Sklonowanie sieci neuronowej
WORKDIR /opt/contact_graspnet
RUN git clone https://github.com/elchun/contact_graspnet_pytorch.git .

WORKDIR /workspace/contact-graspnet
