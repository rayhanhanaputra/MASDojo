# MASDojo grading runner.
#
# Boots an Android emulator, so the CONTAINER MUST RUN ON A KVM-ENABLED HOST
# with /dev/kvm mapped in (see docker-compose.yml). Without KVM the emulator
# will not start; set RUNNER_DRY_RUN=true to grade flag/static tasks only.
#
# NOTE: build context is the repo ROOT (see docker-compose.yml) so this image
# can copy both runner/ and infra/avd/ provisioning scripts.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ANDROID_SDK_ROOT=/opt/android-sdk \
    ANDROID_AVD_HOME=/root/.android/avd \
    DEBIAN_FRONTEND=noninteractive

# System deps: JDK (sdkmanager), KVM/qemu libs, adb, and emulator runtime libs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \
        curl unzip git \
        android-tools-adb \
        libpulse0 libnss3 libxcomposite1 libxcursor1 libxi6 libxtst6 \
        libgl1 libglu1-mesa libx11-6 libxdamage1 qemu-kvm \
    && rm -rf /var/lib/apt/lists/*

# Android command-line tools + platform + emulator + a KVM-accelerated image.
ARG ANDROID_API=34
ARG SYSTEM_IMAGE="system-images;android-34;google_apis;x86_64"
COPY infra/avd/setup-sdk.sh /tmp/setup-sdk.sh
RUN bash /tmp/setup-sdk.sh "${ANDROID_API}" "${SYSTEM_IMAGE}"

ENV PATH="${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${ANDROID_SDK_ROOT}/emulator:${PATH}"

# Create the AVD the worker boots.
COPY infra/avd/create-avd.sh /tmp/create-avd.sh
RUN bash /tmp/create-avd.sh "${SYSTEM_IMAGE}" "masdojo_avd"

WORKDIR /app
COPY runner/pyproject.toml ./
RUN pip install --upgrade pip && pip install .
COPY runner/runner ./runner

# frida-server is fetched during the SDK setup and pushed to the device on boot.
COPY infra/avd/push-frida.sh /app/push-frida.sh

CMD ["python", "-m", "runner.worker"]
