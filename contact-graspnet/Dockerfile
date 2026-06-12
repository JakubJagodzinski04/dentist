# Środowisko ROS 2 dla Contact-GraspNet (PyTorch Port)
# Zoptymalizowane pod GPU RTX 5060 (Blackwell) i chmury punktów 3D

FROM ros:humble

# 1. Narzędzia systemowe i mosty wizyjne ROS 2
RUN apt-get update && apt-get -y upgrade && apt-get -y install \
    ros-humble-desktop \
    ros-humble-cv-bridge \
    ros-humble-vision-msgs \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. PyTorch natywnie pod architekturę CUDA 12.8 (Blackwell)
RUN pip3 install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 3. Zależności Point-Cloud i matematyczne dla Contact-GraspNet
RUN pip3 install --no-cache-dir open3d trimesh scipy pyyaml "numpy<2.0.0" "opencv-python<4.11.0"

# 4. Sklonowanie nieoficjalnego portu CGN w PyTorch bezpośrednio do obrazu
WORKDIR /opt/contact_graspnet
RUN git clone https://github.com/elchun/contact_graspnet_pytorch.git .

# 5. Ustawienie docelowego katalogu roboczego na Twój zamontowany folder
WORKDIR /workspace/contact-graspnet
