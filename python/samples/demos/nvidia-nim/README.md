# NVidia NIM Plugin

NVidia Inference Microservice is fully optimized and has wide variety.  Perfect tools to enpower Copilot's semantic kernel.  

This sample show how to encorperate NIM into semantic kernel.
This sample is based on llama-3.1-8b-instruct:latest which is version 1.1.2 at this time.  Please check the the documentation of the NIM you plan to sue to see whethere there is any additional change you need to make.

## Deploy NIM to Azure

NIM can deploy to anyplace include but not limited to Azure ML. AKS and Azure VM.  Just do one of the following to prepare NIM endpoint for next step.

1. **Azure ML Deployment:**

 - Detail instruction can be found [here](https://github.com/NVIDIA/nim-deploy/tree/main/cloud-service-providers/azure/azureml)
        
2. **Azure Kubernetes Service Deployment**
   
 - Detail instruction can be found [here](https://github.com/NVIDIA/nim-deploy/tree/main/cloud-service-providers/azure/aks)
  
3. **Azure VM Deployment**

 - Create an Azure VM with 1x A100 GPU and NVidia AI Enterprise imGE 
 - Follow the link [here](https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html) to continue
 - export the endpoint to public accessable.

## NVidia NIM Plugin 

We use llama-3.1-8b-instruct as example.  We assume there is an expert called nllama3.  We create a plugin called nllama3 and a magic word called nllama3.  Any question asked nllama3 will redirect to this plugin and other questions will use default llm

 - Update the nim_url with the endpoint created in previous step.
 - run nvidia_nim_plugin.py and see how it work.

## Additional Resources:

- Refer to the [NVidia NIM documentation](https://docs.nvidia.com/nim/large-language-models/latest/introduction.html) for guidance on deploying the service.