# Native-AOT Samples
This application demonstrates how to use the Semantic Kernel Native-AOT compatible API in a Native-AOT application.

## Running Samples
The samples be run either in a debug mode by just setting a break point and pressing `F5` in Visual Studio (make sure the `AotCompatibility` project is set as the startup project) in which case they are run in a regular CoreCLR application and not in Native-AOT one. This might be useful to understand how the API works and how to use it.

To run the samples in a Native-AOT application, first publish it using the following command: `dotnet publish -r win-x64`. Then, execute the application by running the following command in the terminal: `.\bin\Release\net8.0\win-x64\publish\AotCompatibility.exe`.  

## Samples
Most of the samples don't require any additional setup, and can be run as is. However, some of them might require additional configuration.

### 1. [ONNX Chat Completion Service](./OnnxChatCompletionSamples.cs)
To configure the sample, you need to download the ONNX model from the Hugging Face repository. Go to a directory of your choice where the model should be downloaded and run the following command:
```powershell
git clone https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx
```

> [!IMPORTANT]
The `Phi-3` model may be too large to download using the `git clone` command unless you have the [git-lfs extension](https://git-lfs.com/) installed. 
You might need to download it manually using the following link: [Phi-3-Mini-4k CPU](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx/resolve/main/cpu_and_mobile/cpu-int4-rtn-block-32/phi3-mini-4k-instruct-cpu-int4-rtn-block-32.onnx.data?download=true) (approximately 2.7 GB).

After downloading the model, you need to configure the sample by setting the `Onnx:ModelPath` and `Onnx:ModelId` secrets. 
The `Onnx:ModelPath` should point to the directory where the model was downloaded, and the `Onnx:ModelId` should be set to `phi-3`.
The secrets can be set using [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets#secret-manager) in the following way:
```powershell
dotnet user-secrets set "Onnx:ModelId" "phi-3"
dotnet user-secrets set "Onnx:ModelPath" "C:\path\to\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32" 
```

### AOT Compatibility
At the moment, the following Semantic Kernel packages are AOT compatible:

| Package                   | AOT compatible |  
|--------------------------|----------------|  
| SemanticKernel.Abstractions | ✔️              |  
| SemanticKernel.Core         | ✔️              |  
| Connectors.Onnx            | ✔️              |  

Other packages are not AOT compatible yet, but we plan to make them compatible in the future.