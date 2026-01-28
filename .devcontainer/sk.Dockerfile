FROM mcr.microsoft.com/devcontainers/universal:latest

# Remove Yarn repository with expired GPG key to prevent apt-get update failures
# Tracking issue: https://github.com/devcontainers/images/issues/1752
RUN rm -f /etc/apt/sources.list.d/yarn.list