# syntax=docker/dockerfile:1.2
FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install "huggingface_hub[cli]"
RUN --mount=type=secret,id=hf_token \
    huggingface-cli login --token $(cat /run/secrets/hf_token)
    
RUN pip install cmake
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
