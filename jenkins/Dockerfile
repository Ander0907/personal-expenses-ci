# Jenkins LTS controller with Docker CLI + Compose + Buildx (talks to the HOST daemon via the mounted socket).
FROM jenkins/jenkins:2.580.2-lts-jdk21

USER root

# Docker CLI, Buildx and Compose plugins from Docker's official apt repo (versions pinned).
# Only clients are installed; there is no Docker daemon inside this image.
# Buildx is required: api/Dockerfile uses BuildKit features (RUN --mount=type=cache).
# bash, curl and git already ship in the base image.
# The apt signing key is checked against Docker's published fingerprint; the build fails on mismatch.
# gnupg is only needed for that check and is removed in the same layer.
ARG DOCKER_GPG_FPR=9DC858229FC7DD38854AE2D88D81803C0EBFCD88
ARG DOCKER_CLI_VERSION=5:29.9.2-1~debian.13~trixie
ARG DOCKER_COMPOSE_VERSION=5.7.2-1~debian.13~trixie
ARG DOCKER_BUILDX_VERSION=0.39.1-1~debian.13~trixie
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL --proto '=https' --tlsv1.2 https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && [ "$(gpg --show-keys --with-colons /etc/apt/keyrings/docker.asc | awk -F: '/^fpr:/ {print $10; exit}')" = "${DOCKER_GPG_FPR}" ] \
    && echo "deb [signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian trixie stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        "docker-ce-cli=${DOCKER_CLI_VERSION}" \
        "docker-compose-plugin=${DOCKER_COMPOSE_VERSION}" \
        "docker-buildx-plugin=${DOCKER_BUILDX_VERSION}" \
    && apt-get purge -y --auto-remove gnupg \
    && rm -rf /var/lib/apt/lists/* /root/.gnupg

USER jenkins

# Plugins pinned in plugins.txt (full tree frozen); installed at build time.
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
