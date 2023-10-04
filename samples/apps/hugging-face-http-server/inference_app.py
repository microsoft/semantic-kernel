# Copyright (c) Microsoft. All rights reserved.

# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
import argparse

from huggingface_hub.hf_api import HfFolder

from flask import Flask, json, jsonify, render_template, request
from utils import (
    CompletionGenerator,
    EmbeddingGenerator,
    ImageGenerator,
    create_responses,
)

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/docs")
def docs():
    return render_template("documentation.html")


@app.route("/docs/completions")
def completions_docs():
    return render_template("completions.html")


@app.route("/docs/embeddings")
def embeddings_docs():
    return render_template("embeddings.html")


@app.route("/docs/images")
def images_docs():
    return render_template("images.html")


@app.route("/completions/<model>", methods=["POST"])
def receive_completion_by_model(model):
    return process_completion_request(request, model)


@app.route("/completions/<organization>/<model>", methods=["POST"])
def receive_completion_by_organization_model(organization, model):
    return process_completion_request(request, f"{organization}/{model}")


@app.route("/embeddings/<model>", methods=["POST"])
def receive_embedding_by_model(model):
    return process_embedding_request(request, model)


@app.route("/embeddings/<organization>/<model>", methods=["POST"])
def receive_embedding_by_organization_model(organization, model):
    return process_embedding_request(request, f"{organization}/{model}")


@app.route("/images/generations/<model>", methods=["POST"])
def receive_image_generation_by_model(model):
    return process_image_generation_request(request, model)


@app.route("/images/generations/<organization>/<model>", methods=["POST"])
def receive_image_generation_by_organization_model(organization, model):
    return process_image_generation_request(request, f"{organization}/{model}")


def process_completion_request(request, model):
    request_data = request.data
    json_data = json.loads(request_data)

    save_api_key(request)

    try:
        prompt = json_data["inputs"]
        if "context" in json_data:
            context = json_data["context"]
        else:
            context = ""

        if "max_tokens" in json_data:
            max_tokens = json_data["max_tokens"]
        else:
            max_tokens = 64

        inference_generator = CompletionGenerator.CompletionGenerator(model)
        (
            result,
            num_prompt_tokens,
            num_result_tokens,
        ) = inference_generator.perform_inference(prompt, context, max_tokens)
        return jsonify(
            create_responses.create_completion_response(
                result, model, num_prompt_tokens, num_result_tokens
            )
        )
    except Exception as e:
        print(e)
        return "Sorry, unable to perform sentence completion with model {}".format(
            model
        )


def process_embedding_request(request, model):
    request_data = request.data
    json_data = json.loads(request_data)

    save_api_key(request)

    try:
        sentences = json_data["inputs"]
        inference_generator = EmbeddingGenerator.EmbeddingGenerator(model)
        embeddings, num_prompt_tokens = inference_generator.perform_inference(sentences)
        return jsonify(
            create_responses.create_embedding_response(embeddings, num_prompt_tokens)
        )
    except Exception as e:
        print(e)
        return "Sorry, unable to generate embeddings with model {}".format(model)


def process_image_generation_request(request, model):
    request_data = request.data
    json_data = json.loads(request_data)
    num_images = json_data["n"]
    prompt = json_data["inputs"]
    image_size = json_data["size"]

    save_api_key(request)

    try:
        image_generator = ImageGenerator.ImageGenerator(model)
        image_data = image_generator.perform_inference(prompt, num_images, image_size)
        return jsonify(create_responses.create_image_gen_response(image_data))
    except Exception as e:
        print(e)
        return "Sorry, unable to generate images with model {}".format(model)


def save_api_key(request):
    auth_header = request.headers.get("Authorization")
    header_prefix = "Bearer "

    if auth_header and auth_header.startswith(header_prefix):
        token = auth_header[len(header_prefix) :]

        if token:
            HfFolder.save_token(token)


# main driver function
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--ip", default="0.0.0.0", help="ip address for flask server endpoint"
    )
    parser.add_argument(
        "-p",
        "--port",
        default=5000,
        help="port for flask server endpoint",
        type=int,
    )
    args = parser.parse_args()

    host_ip = args.ip
    port = args.port

    app.run(host=host_ip, debug=True, port=port)
