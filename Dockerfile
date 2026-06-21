FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY . .

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

# foxglove.CompressedPointCloud is not shipped in the published keelson 0.5.3 wheel.
# Drop the generated pb2 next to the other foxglove modules so its relative import
# (`from . import Pose_pb2`) resolves and it registers in the default descriptor pool.
RUN cp vendor/CompressedPointCloud_pb2.py \
    "$(python -c 'import os, keelson.payloads.foxglove as f; print(os.path.dirname(f.__file__))')/CompressedPointCloud_pb2.py"

RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python", "bin/main.py"]

CMD ["-r", "rise"]