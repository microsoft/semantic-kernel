## MultiConnector Integration Tests

This directory houses integration tests for the MultiConnector, which are tailored to ensure the MultiConnector's accurate operation comprehensively.


### What is the MultiConnector?

The MultiConnector serves as an AI completion provider for the semantic-kernel. It integrates various connectors and directs completion calls to the suitable connector based on its capabilities.

### What is the MultiConnector Test?

This test measures the performance of different text generation software connectors, focusing on their response times. By conducting this test, users can discern which connector aligns best with their requirements in terms of efficiency and dependability.

For the purposes of the test, ChatGPT acts as the primary connector for generating samples while also evaluating secondary connectors on identical tasks. The secondary connectors are smaller LLama 2 models self-hosted using the open-source application, oobabooga.


### Directory Structure

- **MultistartScripts**: Contains scripts to initialize multiple connectors concurrently.
- **Plans**: Contains JSON plans for the connectors.
- **Texts**: Contains text files which can be used during testing.

**Primary File** :

- `MultiConnectorTests.cs` - Contains the integration test cases for the MultiConnector.


## Setting Up Oobabooga & Downloading Models:

1. **Determine Your GPU VRAM**:
   - First, identify your GPU's VRAM, as the models you choose should align with your GPU's capacity. You can utilize GPU-Z for this task. [Download here](https://www.techpowerup.com/gpuz/).

2. **Install Oobabooga**: 

   Oobabooga's Gradio Web UI is a notable solution for hosting Large Language Models. Set it up by:
   - Fetching the zip file tailored for your OS from [Oobabooga GitHub](https://github.com/oobabooga/text-generation-webui).
     - Options include: [Windows](https://github.com/oobabooga/one-click-installers/oobabooga-windows.zip), [Linux](https://github.com/oobabooga/one-click-installers/oobabooga-linux.zip), [macOS](https://github.com/oobabooga/one-click-installers/oobabooga-macos.zip), and [WSL](https://github.com/oobabooga/one-click-installers/oobabooga-wsl.zip).
   - Decompress the zip file and run "start". This action installs and commences the Web UI on your local system. Access it using the given endpoint (typically, http://localhost:7860/).


3. **Copy and Refine the `.bat` Multiscript**:
   - Relocate the relevant multi_start script from /MultistartScripts to the Oobabooga directory.
   - Customize the multistart script to select models based on your GPU's VRAM. Remember to keep a VRAM margin for optimal operation.

4. **Downloading Models**:
   Most models can be sourced from [HuggingFace](https://huggingface.co/). For a curated selection, consider the [open_llm_leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard).
   
   [Tom Jobbins](https://huggingface.co/TheBloke) provides quantized models, harmonizing memory usage and performance. To download:
   
   - Navigate to the **Models** tab in Oobabooga's UI.
   - Employ the "Download custom model or LoRA" function.
   - For each desired model:
     - Access its Hugging Face page, such as [TheBloke's StableBeluga-13B-GGML](https://huggingface.co/TheBloke/StableBeluga-13B-GGML).
     - Copy its name.
     - Insert it into the Oobabooga model section, appending `:main`. For instance, "TheBloke/StableBeluga-13B-GGML:main".
     - Click **Download**.
   
   🚨 **Special Guidance for GGML Models**: 
   - These repositories contain versions with varying quantizations.
   - Typically, Oobabooga selects the initial `.bin` model alphabetically, often a 2bit quantized version.
   - **Advice**: Initiate the download in Oobabooga to create the required subfolder. Then, interrupt the download. Now, directly fetch the desired `.bin` model file (like `stablebeluga-13b.ggmlv3.q4_K_M.bin`) from Hugging Face and place it in the new subfolder.

5. **Sync Your Settings**:
   The settings file appears as shown below. For these tests, the primary connector will be OpenAI. Ensure you've configured the respective settings or user secrets accurately.

   To toggle secondary connectors on or off, adjust the IncludedConnectors section by commenting or uncommenting lines.

   **Note**: Using an extra testsettings.development.json file to leave the main one intact? Employ the IncludedConnectorsDev section, which takes precedence over the IncludedConnectors section. 
   
   If you've modified models in your multi-start script, reflect those changes in the OobaboogaCompletions section of the main settings file.

   Also, most models were trained with a specific chat-instruct format, so those were included in the default settings in order to wrap call prompts. Additional global tokens are available in the settings files to fine tune  bindings between semantic function prompts and chat-instruct templates.

```json
{
  "OpenAI": { ... },
  "AzureOpenAI": { ... },
  "OpenAIEmbeddings": { ... },
  "AzureOpenAIEmbeddings": { ... },
  "HuggingFace": { ... },
  "Bing": { ... },
  "Postgres": { ... },
  "MultiConnector": {
    "OobaboogaEndPoint": "http://localhost",
    "GlobalParameters": {
      "SystemSupplement": "User is now playing a game where he is writing messages in the form of semantic functions. That means you are expected to strictly answer with a completion of his message, without adding any additional comments.",
      "UserPreamble": "Let's play a game: please read the following instructions, and simply answer with a completion of my message, don't add any personal comments."
    },
    "IncludedConnectors": [
      ...
    ],
    "IncludedConnectorsDev": [
      // Toggle models for development/testing without altering the main settings:
      //"TheBloke_orca_mini_3B-GGML",
      //"togethercomputer_RedPajama-INCITE-Chat-3B-v1",
      ...
    ],
    "OobaboogaCompletions": [
      {
        "Name": "TheBloke_orca_mini_3B-GGML",
        ...
      },
      ...
    ]
  }
}
```



6. **Launch Using `.bat` or `.sh` Script**:
   For WSL users, administrator access is required for port forwarding. The terminal displays the model's initialization progress and, once done, indicates the model's port number.

7. **Initiate Your Tests**:
   Integration tests are off by default. To activate, switch [Theory(Skip = "This test is for manual verification.")] to [Theory].

8. **Pick a Test**:
   The length of tests can vary based on parameter intricacy. Running tests separately through your IDE is preferable over the complete suite.

Each test follows this workflow:

    - Initialization
        - MultiCompletion settings are initialized from global parameters, according to the models you have activated in the settings file.
        - A kernel is initialized with skills and multicompletion settings
        - A plan with one or several semantic functions is generated from a factory
    - The plan is run once. The primary connector defined (Chat GPT) is used to generate the various completions.
        - Performance in cost and in duration is recorded.
        - Samples are collected automatically during the run
        - Result of the plan is shown.
    - An analysis task is run from samples collected during the run.
        - Each connector is tested on the samples.
        - The primary connector (ChatGPT) evaluates the test runs, vetting each connector's capability to handle each corresponding prompt type.
        - New settings are computed from the evaluation. Vetted connectors are promoted to handle the corresponding prompt types.
        - MultiCompletion settings are updated according to the analysis results.
    - The original plan is reloaded and run again. This time, the secondary connectors may be used to generate some or all of the completions according to the updated settings.
        - Performance in cost and in duration is recorded.
        - Result of the plan is shown
    - A third instance of a plan is generated with distinct data.
        - New plan is run with same settings
        - New samples are collected automatically during the run
        - Samples are evaluated by the primary connector
    - Asserts are run on the results to validate the test, which succeeds iif:
        - Some cost performance were observed between 1st and 2nd run (at least a secondary connector was vetted once)
        - Validation samples belonging to secondary connectors are all vetted by the primary connector, with at least one sample validated.


   There are 2 kinds of plan factories available: 

   - Static plans are loaded from .json files the Plan folder. They are injected with test and validation texts of various complexities from .txt files in the Text folder.
        - ChatGptOffloadsToMultipleOobaboogaUsingFileAsync loads a multiCompletion with all tests enabled in the settings, and will fail if the corresponding models are not loaded. 
        - ChatGptOffloadsToSingleOobaboogaUsingFileAsync will test a single model, and will succeed if the corresponding model is not loaded.
   - Dynamic plans are generated by calling primary connector with a sequential planner. Those plans are more variable and test's success rate is variable. 
        - ChatGptOffloadsToOobaboogaUsingPlannerAsync is the entry point for those tests.

 9. **Gather and Examine Execution Trace**:

    Tests produce extensive log traces detailing all stages and results. For better clarity, transfer the trace to a markdown viewer.