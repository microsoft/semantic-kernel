# Sample Guidelines

Samples are extremely important for developers to get started with Semantic Kernel. We strive to provide a wide range of samples that demonstrate the capabilities of Semantic Kernel with consistency and quality. This document outlines the guidelines for creating samples.

## General Guidelines

- **Clear and Concise**: Samples should be clear and concise. They should demonstrate a specific set of features or capabilities of Semantic Kernel. The less concepts a sample demonstrates, the better.
- **Consistent Structure**: All samples should have a consistent structure. This includes the folder structure, file naming, and the content of the sample.
- **Incremental Complexity**: Samples should start simple and gradually increase in complexity. This helps developers understand the concepts and features of Semantic Kernel.
- **Documentation**: Samples should be over-documented.

### **Clear and Concise**

Try not to include too many concepts in a single sample. The goal is to demonstrate a specific feature or capability of Semantic Kernel. If you find yourself including too many concepts, consider breaking the sample into multiple samples. A good example of this is to break non-streaming and streaming modes into separate samples.

### **Consistent Structure**

#### Getting Started Samples

The getting started samples are the simplest samples that require minimal setup. These samples should be named in the following format: `step<number>_<name>.py`. One exception to this rule is when the sample is a notebook, in which case the sample should be named in the following format: `<number>_<name>.ipynb`.

#### Concept Samples

Concept samples under [./concepts](./concepts) should be grouped by feature or capability. These samples should be relatively short and demonstrate a specific concept. These samples are more advanced than the getting started samples.

#### Demos

Demos under [./demos](./demos) are full console applications that demonstrate a specific set of features or capabilities of Semantic Kernel, potentially with external dependencies. Each of the demos should have a README.md file that explains the purpose of the demo and how to run it.

### **Incremental Complexity**

Try to do a best effort to make sure that the samples are incremental in complexity. For example, in the getting started samples, each step should build on the previous step, and the concept samples should build on the getting started samples, same with the demos.

### **Documentation**

Try to over-document the samples. This includes comments in the code, README.md files, and any other documentation that is necessary to understand the sample. We use the guidance from [PEP8](https://peps.python.org/pep-0008/#comments) for comments in the code, with a deviation for the initial summary comment in samples and the output of the samples.

For the getting started samples and the concept samples, we should have the following:

1. A README.md file is included in each set of samples that explains the purpose of the samples and the setup required to run them.
2. A summary should be included at the top of the file that explains the purpose of the sample and required components/concepts to understand the sample. For example:

    ```python
    '''
    This sample shows how to create a chatbot. This sample uses the following two main components:
    - a ChatCompletionService: This component is responsible for generating responses to user messages.
    - a ChatHistory: This component is responsible for keeping track of the chat history.
    The chatbot in this sample is called Mosscap, who responds to user messages with long flowery prose.
    '''
    ```

3. Mark the code with comments to explain the purpose of each section of the code. For example:

    ```python
    # 1. Create the instance of the Kernel to register the plugin and service.
    ...
    
    # 2. Create the agent with the kernel instance.
    ...
    ```

    > This will also allow the sample creator to track if the sample is getting too complex.

4. At the end of the sample, include a section that explains the expected output of the sample. For example:

    ```python
    '''
    Sample output:
    User:> Why is the sky blue in one sentence?
    Mosscap:> The sky is blue due to the scattering of sunlight by the molecules in the Earth's atmosphere,
    a phenomenon known as Rayleigh scattering, which causes shorter blue wavelengths to become more
    prominent in our visual perception.    
    '''
    ```

For the demos, a README.md file must be included that explains the purpose of the demo and how to run it. The README.md file should include the following:

- A description of the demo.
- A list of dependencies required to run the demo.
- Instructions on how to run the demo.
- Expected output of the demo.
