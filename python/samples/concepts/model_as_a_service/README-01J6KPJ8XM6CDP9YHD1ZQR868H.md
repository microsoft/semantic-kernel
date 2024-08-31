---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:54:44Z
---

# Semantic Kernel Model-as-a-Service Sample

This sample contains a script to run multiple models against the popular [**Measuring Massive Multitask Language Understanding** (MMLU)](ht******************************LU) dataset and produces results for benchmarking.

You can use this script as a starting point if you are planning to do the followings:

1. You are developing a new dataset or augmenting an existing dataset for benchmarking Large Language Models.
2. You would like to reproduce results from academic papers with existing datasets and models available on Azure AI Studio, such as the Phi series of models, or larger models like the Llama series and the Mistral large model. You can find model availabilities [here](ht******************************************************************************************ty).

## Dataset

In this sample, we will be using the MMLU dataset hosted on HuggingFace.

To gain access to the dataset from HuggingFace, you will need a HuggingFace access token. Follow the steps [here](ht*******************************************ns) to create one. You will be asked to provide the token when you run the sample.

The MMLU dataset has many subsets, organized by subjects. You can load whichever subjects you are interested in. Add or remove subjects by modifying the following line in the script:

```Python {"id":"01J6KPVR96ZMY976MTJA9S5387"}
datasets = load_mmlu_dataset(
    [
        "college_computer_science",
        "astronomy",
        "college_biology",
        "college_chemistry",
        "elementary_mathematics",
        # Add more subjects here.
        # See here for a full list of subjects: ht********************************************er
    ]
)
```

## Models

This sample by default assumes three models: [Ll*****8b](ht**************************************************************************************************************************************pi), [Ph*****ni](ht*******************************************************************************************************************************is), and [Ph******ll](ht********************************************************************************************************************************is). However, you are free to add or remove models as long as it's available in the [model catalog](ht***************************************************************************ew).

Add a new model by adding a new AI service to the kernel in the script:

```Python {"id":"01J6KPVR96ZMY976MTJB01D6XC"}
def setup_kernel():
    """Set up the kernel."""
    ...
    kernel.add_service(
        AzureAIInferenceChatCompletion(
            ai_model_id="",
            api_key="",
            endpoint="",
        )
    )
    ...
```

The new service will automatically get picked up to run against the dataset.

The default models are selected based on the benchmark results reported on page 6 of the paper [**Phi-3 Technical Report:
A Highly Capable Language Model Locally on Your Phone**](ht****************************19). In theory, Ph******ll will perform better than Ph*****ni, which will perform better than Ll*****8b. You should see the same result when you run this sample, though the numbers will not be the same, because this sample employs zero-shot learning whereas the report employed 5-**ot learning.

Follow the steps [here](ht**************************************************************************************************io) to deploy models of your choice.

> We intentionally use zero-shot so that you will have the opportunity to tune the prompt to get accuracies closer to what the report shows. You can tune the prompt in [helpers.py](helpers.py).

## Running the sample

1. Deploy the required models. Follow the steps [here](ht**************************************************************************************************io).
2. Fill in the API keys and endpoints in the script.
3. Open a terminal and activate your virtual environment for the Semantic Kernel project.
4. Run `pip install datasets` to install the HuggingFace `datasets` module.
5. Run `python mmlu_model_eval.py`

> If you are using VS code, you can simply select the interpreter in your virtual environment and click the run icon on the top right corner of the file panel when you focus on the script file.

## Results

After the sample finishes running, you will see outputs similar to the following:

```sh {"id":"01J6KPVR96ZMY976MTJCEM6VVJ"}
Finished evaluating college_biology.
Accuracy of Ll*****8b: 75.00%.
Accuracy of Ph*****ni: 81.25%.
Accuracy of Ph******ll: 93.75%.
...
Overall results:
Overall Accuracy of Ll*****8b: 51.09%.
Overall Accuracy of Ph*****ni: 55.43%.
Overall Accuracy of Ph******ll: 66.30%.
```