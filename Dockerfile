ARG MODEL_NAME
ARG MODEL_PARAMS
ARG MODEL_PROMPT_TEMPLATE
ARG APP_COLOR
ARG APP_NAME

FROM node:20 as chatui-builder
ARG MODEL_NAME
ARG MODEL_PARAMS
ARG APP_COLOR
ARG APP_NAME
ARG MODEL_PROMPT_TEMPLATE

WORKDIR /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git gettext && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/huggingface/chat-ui.git

WORKDIR /app/chat-ui

COPY .env.local.template .env.local.template

RUN mkdir defaults
ADD defaults /defaults
RUN chmod -R 777 /defaults
RUN --mount=type=secret,id=MONGODB_URL,mode=0444 \
    MODEL_NAME="${MODEL_NAME:="$(cat /defaults/MODEL_NAME)"}" && export MODEL_NAME \
    && MODEL_PARAMS="${MODEL_PARAMS:="$(cat /defaults/MODEL_PARAMS)"}" && export MODEL_PARAMS \
    && MODEL_PROMPT_TEMPLATE="${MODEL_PROMPT_TEMPLATE:="$(cat /defaults/MODEL_PROMPT_TEMPLATE)"}" && export MODEL_PROMPT_TEMPLATE \
    && APP_COLOR="${APP_COLOR:="$(cat /defaults/APP_COLOR)"}" && export APP_COLOR \
    && APP_NAME="${APP_NAME:="$(cat /defaults/APP_NAME)"}" && export APP_NAME \
    && MONGODB_URL=$(cat /run/secrets/MONGODB_URL > /dev/null | grep '^' || cat /defaults/MONGODB_URL) && export MONGODB_URL && \
    echo "${MONGODB_URL}" && \
    envsubst < ".env.local.template" > ".env.local" \ 
    && rm .env.local.template

RUN --mount=type=cache,target=/app/.npm \
    npm set cache /app/.npm && \
    npm ci

RUN npm run build

FROM ghcr.io/huggingface/text-generation-inference:latest

ARG MODEL_NAME
ARG MODEL_PARAMS
ARG MODEL_PROMPT_TEMPLATE
ARG APP_COLOR
ARG APP_NAME

ENV TZ=Europe/Paris \
    PORT=3000

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    gnupg \
    curl \
    gettext && \
    rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh.template entrypoint.sh.template

RUN mkdir defaults
ADD defaults /defaults
RUN chmod -R 777 /defaults

RUN --mount=type=secret,id=MONGODB_URL,mode=0444 \
    MODEL_NAME="${MODEL_NAME:="$(cat /defaults/MODEL_NAME)"}" && export MODEL_NAME \
    && MODEL_PARAMS="${MODEL_PARAMS:="$(cat /defaults/MODEL_PARAMS)"}" && export MODEL_PARAMS \
    && MODEL_PROMPT_TEMPLATE="${MODEL_PROMPT_TEMPLATE:="$(cat /defaults/MODEL_PROMPT_TEMPLATE)"}" && export MODEL_PROMPT_TEMPLATE \
    && APP_COLOR="${APP_COLOR:="$(cat /defaults/APP_COLOR)"}" && export APP_COLOR \
    && APP_NAME="${APP_NAME:="$(cat /defaults/APP_NAME)"}" && export APP_NAME \
    && MONGODB_URL=$(cat /run/secrets/MONGODB_URL > /dev/null | grep '^' || cat /defaults/MONGODB_URL) && export MONGODB_URL &&  \
    envsubst < "entrypoint.sh.template" > "entrypoint.sh" \
    && rm entrypoint.sh.template

RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor

RUN echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    mongodb-org && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data/db
RUN chown -R 1000:1000 /data

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | /bin/bash -

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /app
RUN chown -R 1000:1000 /app

RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN npm config set prefix /home/user/.local
RUN npm install -g pm2

COPY --from=chatui-builder --chown=1000 /app/chat-ui/node_modules /app/node_modules
COPY --from=chatui-builder --chown=1000 /app/chat-ui/package.json /app/package.json
COPY --from=chatui-builder --chown=1000 /app/chat-ui/build /app/build

ENTRYPOINT ["/bin/bash"]
CMD ["entrypoint.sh"]

# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile

FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

# Set up environment variables using a .env file
COPY .env /app/.env

# Create a configuration file using config.json
COPY config.json /app/config.json

# Build the Docker image
RUN docker build -t my-app .

# Run the Docker container
CMD ["docker", "run", "-p", "3000:3000", "--env-file", ".env", "my-app"]

# Access the web page
CMD ["open", "http://localhost:3000"]
