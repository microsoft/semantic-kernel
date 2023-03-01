# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, request, json, redirect, url_for, render_template, jsonify
from utils import model_utils, create_responses, CompletionGenerator, EmbeddingGenerator, ImageGenerator
import os
import socket
import sys
import argparse

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/completions', methods=['POST'])
def receive_completion_request():
    request_data = request.data
    json_data = json.loads(request_data)
    requested_model = json_data["model"]
    try:
        prompt = json_data["prompt"]
        if "context" in json_data:
            context = json_data["context"]
        else:
            context = ""

        if "max_tokens" in json_data:
            max_tokens = json_data["max_tokens"]
        else:
            max_tokens = 32

        inference_generator = CompletionGenerator.CompletionGenerator(requested_model)
        result, num_prompt_tokens, num_result_tokens = inference_generator.perform_inference(prompt, context, max_tokens)
        return jsonify(create_responses.create_completion_response(
                        result,
                        requested_model,
                        num_prompt_tokens,
                        num_result_tokens))
    except Exception as e:
        print(e)
        return ("Sorry, unable to perform sentence completion with model {}".format(requested_model))

@app.route('/embeddings', methods=['POST'])
def receive_embedding_request():
    request_data = request.data
    json_data = json.loads(request_data)
    requested_model = json_data["model"]
    try:
        sentences = json_data["input"]
        inference_generator = EmbeddingGenerator.EmbeddingGenerator(requested_model)
        embeddings, num_prompt_tokens = inference_generator.perform_inference(sentences)
        return jsonify(create_responses.create_embedding_response(
                        embeddings,
                        num_prompt_tokens))
    except Exception as e:
        print(e)
        return ("Sorry, unable to generate embeddings with model {}".format(requested_model))

@app.route('/images/generations', methods=['POST'])
def receive_img_generation_request():
    request_data = request.data
    json_data = json.loads(request_data)
    requested_model = json_data["model"]
    num_images = json_data["n"]
    prompt = json_data["prompt"]
    image_size = json_data["size"]
    try:
        image_generator = ImageGenerator.ImageGenerator(requested_model)
        image_data = image_generator.perform_inference(prompt, num_images, image_size)
        return jsonify(create_responses.create_image_gen_response(image_data))
    except Exception as e:
        print(e)
        return ("Sorry, unable to generate images with model {}".format(requested_model))
        
    
# main driver function
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip',
                        default='0.0.0.0',
                        help='ip address for flask server endpoint'
                        )
    parser.add_argument('-p', '--port',
                        default=5000,
                        help='port for flask server endpoint',
                        type=int,
                        )
    args = parser.parse_args()

    host_ip = args.ip
    port = args.port

    app.run(host=host_ip, debug=True, ssl_context='adhoc', port=port)
