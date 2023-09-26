# Local Hugging Face Model Inference Server

> [!IMPORTANT]
> This sample will be removed in a future release. If you are looking for samples that demonstrate
> how to use Semantic Kernel, please refer to the sample folders in the root [python](../../../python/samples/)
> and [dotnet](../../../dotnet/samples/) folders.

> [!IMPORTANT]
> This learning sample is for educational purposes only and should not be used in any production
> use case. It is intended to make Semantic Kernel features more accessible for scenarios that
> do not require an OpenAI or Azure OpenAI endpoint.

This application provides an API service for interacting with models available
through [Hugging Face](https://huggingface.co/). The request bodies and responses
are modeled after OpenAI and Azure OpenAI for smooth transition to more capable LLMs.

## Building the Sample Container

`docker image build -t hf_model_server .`

This step will take some minutes to download Docker image dependencies.

## Running the Sample Container

`docker run -p 5000:5000 -d hf_model_server`

This will run the service at **`http://localhost:5000`**. Navigating to
**`http://localhost:5000`** in a browser window will provide instruction on how
to construct requests to the service.

> [!IMPORTANT]
> If the model has not been cached (ex: first time calling it) the response can
> take some time due to the model being downloaded.
> Using this service to generate images can also take a very long time - a factor
> that scales with your hardware.

## Alternative: Bare-Metal

Alternatively, the service can be started on bare-metal. To do this, you will
need to have Python 3.9 installed.

Before proceeding, it is highly recommended that you create a Python 3.9 virtual
environment.

Example: `python -m venv myvenv` or `python3 -m venv myvenv`.

Make sure your environment is activated:

For Windows, run in PowerShell: `./myvenv/Scripts/Activate`.
For Linux/macOS, run: `source myvenv/bin/activate`.

Then, run `pip install -r requirements.txt`.

Once all the required dependencies have been installed, you can run the service
using `python inference_app.py`. Navigating to **`http://localhost:5000`** in a
browser window will provide instruction on how to construct requests to the service.
