# Onnx Simple Chat with Cuda Execution Provider

This sample demonstrates how you use ONNX Connector with CUDA Execution Provider to run Local Models straight from files using Semantic Kernel.

In this example we setup Chat Client from ONNX Connector with [Microsoft's Phi-3-ONNX](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx) model 

> [!IMPORTANT]
> You can modify to use any other combination of models enabled for ONNX runtime.

## Semantic Kernel used Features

- [Chat Client](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service from [Onnx Connector](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.Onnx/OnnxRuntimeGenAIChatCompletionService.cs) to generate responses from the Local Model.

## Prerequisites

- [.NET 10](https://dotnet.microsoft.com/download/dotnet/10.0).
- [NVIDIA GPU](https://www.nvidia.com/en-us/geforce/graphics-cards)
- [NVIDIA CUDA v12 Toolkit](https://developer.nvidia.com/cuda-12-0-0-download-archive)
- [NVIDIA cuDNN v9.11](https://developer.nvidia.com/cudnn-9-11-0-download-archive)
- Windows users only: 
  
  Ensure `PATH` environment variable includes the `bin` folder of the CUDA Toolkit and cuDNN. 
    i.e:
    - C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin
    - C:\Program Files\NVIDIA\CUDNN\v9.11\bin\12.9

- Downloaded ONNX Models (see below).

## Downloading the Model

For this example we chose Hugging Face as our repository for download of the local models, go to a directory of your choice where the models should be downloaded and run the following commands:

```powershell
git lfs install
git clone https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx
```

Update the `Program.cs` file lines below with the paths to the models you downloaded in the previous step.

```csharp
// i.e. Running on Windows
string modelPath = "D:\\repo\\huggingface\\Phi-3-mini-4k-instruct-onnx\\cuda\\cuda-int4-rtn-block-32";
```

