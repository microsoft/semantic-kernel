# Semantic Kernel for Java

Semantic Kernel (SK) is a lightweight SDK that lets you easily mix conventional programming languages with the latest in Large Language Model (LLM) AI "prompts" with templating, chaining, and planning capabilities out-of-the-box.

To learn more about Microsoft Semantic Kernel, visit the [Microsoft Semantic Kernel documentation](https://learn.microsoft.com/en-us/semantic-kernel/whatissk).

The Semantic Kernel for Java is an SDK that implements the key concepts of the Semantic Kernel in Java. It is designed to be used in Java applications and services in an idiomatic way, and to be easily integrated with other Java libraries and frameworks.

## Get Started

To run the LLM prompts and semantic functions in this kernel, make sure you have an [Open AI API Key](https://openai.com/api/) or [Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api).

### Requirements

To build the semantic kernel, you will need to have:

- **Required**: 
  - [JDK 17](https://microsoft.com/openjdk/) or newer
  - [Apache Maven](https://maven.apache.org/) 3.9.1 or newer
  - Azure OpenAI SDK for Java _(see below for instructions)_

## Building the semantic kernel

The semantic kernel is built using [Apache Maven](https://maven.apache.org/). To build the semantic kernel, you will first need to have the Azure OpenAI SDK for Java installed in your local Maven repository. At this moment, this SDK is not available on Maven Central, so you will need to build it locally from the source.

### Build the Azure OpenAI SDK locally

2. Clone the Azure SDK OpenAI repository

       git clone git@github.com:Azure/azure-sdk-for-java.git

3. Switch to the OpenAI feature branch

       cd azure-sdk-for-java
       git checkout feature/open-ai

4. Build and install the Azure SDK OpenAI in your local Maven Repository

       mvn -pl sdk/openai/azure-ai-openai -am install

### Build the semantic kernel

1. Clone this repository

        git clone git@github.com:microsoft/semantic-kernel.git

2. Build the semantic kernel

        cd semantic-kernel/java
        mvn install

    - _Note: disable the integration tests if the build of the semantic kernel fails for lack of an OpenAI key_

          mvn install -DskipITs

## Using the semantic kernel

Check the `samples` folder for examples of how to use the semantic kernel.

## Discord community

Join the [Microsoft Semantic Kernel Discord community](https://aka.ms/java-sk-discord) to discuss the Semantic Kernel and get help from the community. We have a `#java` channel for Java-specific questions.

## Contributing

### Testing locally

The project may contain integratoin tests that require an OpenAI key to run. To run the integration tests locally, you will need to set the following environment variable:

- `OPENAI_API_KEY` - the OpenAI API key.

If you are using Azure OpenAI, you will also need to set the following environment variables:

- `AZURE_OPENAI_ENDPOINT` - the Azure OpenAI endpoint found in **Keys * Endpoint** section of the Azure OpenAI service.
- `AZURE_OPENAI_API_KEY` - the Azure OpoenAI API key found in **Keys * Endpoint** section of the Azure OpenAI service.
- `AZURE_OPENAI_DEPLOYMENT_NAME` - the custom name you chose for your deployment when you deployed a model. It can be found under **Resource Management > Deployments** in the Azure Portal.

For more information, see the Azure OpenAI documentation on [how to get your Azure OpenAI credentials](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?pivots=rest-api&tabs=command-line#retrieve-key-and-endpoint).

To run the unit tests only, run the following command:

    mvn package

To run all tests, including integration tests that require an OpenAI key, run the following command:

    mvn verify

### Submitting a pull request

Before submitting a pull request, please make sure that:

- All tests pass
- All unit tests under `src/test/java` do not require an OpenAI key to run
- Only integration tests under `src/it/java` require an OpenAI key to run
- All new code is covered by unit tests
- All new code is covered by integration tests

Once your proposal is ready, submit a pull request to the `main` branch. The pull request will be reviewed by the project maintainers.

Make sure your pull request has an objective title and a clear description explaining the problem and solution.

## License

This project is licensed under the [MIT License](LICENSE).

## Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

