# Local Hugging Face Model Inteference Server

> [!IMPORTANT]
> This learning sample is for educational purposes only and should not be used in any production
> use case. It is intended to make Semantic Kernel features more accessible for scenarios that
> do not require an OpenAI or Azure OpenAI endpoint.

This application provides an API service for interacting with models available through [Hugging Face](https://huggingface.co/). The request bodies and responses are modeled after OpenAI and Azure OpenAI for smooth transition to more capable LLMs.

## Building the Sample Container
`docker image build -t hf_model_server .`

## Running the Sample Container
`docker run -p 5000:5000 -d hf_model_server`

This will run the service at **`http://localhost:5000`**. Navigating to **`http://localhost:5000`** in a browser window will provide instruction on how to construct requests to the service. 

## Alternative: Bare-Metal
Alternatively, the service can be started on bare-metal. To do this, you will need to have Python 3.6 installed. 

Before proceeding, it is highly recommended that you create a Python 3.6 virtual environment.

Example: `python -m venv myvenv` or  `python3 -m venv myvenv` or  `python3.6 -m venv myvenv`

Then, run `pip install -r requirements.txt`.

Once all the required dependencies have been installed, you can run the service using `python inference_app.py`. Navigating to **`http://localhost:5000`** in a browser window will provide instruction on how to construct requests to the service.