# Semantic Kernel Responsible AI FAQs

## What is Microsoft Semantic Kernel?
Microsoft Semantic Kernel is a lightweight, open-source development kit designed to facilitate the integration of AI models into applications written in languages such as C#, Python, or Java.

It serves as efficient middleware that supports developers in building AI agents, automating business processes, and connecting their code with the latest AI technologies. Input to this system can range from text data to structured commands, and it produces various outputs, including natural language responses, function calls, and other actionable data.

## What can Microsoft Semantic Kernel do?
Building upon its foundational capabilities, Microsoft Semantic Kernel facilitates several functionalities:
-	AI Agent Development: Users can create agents capable of performing specific tasks or interactions based on user input.
-	Function Invocation: It can automate code execution by calling functions based on AI model outputs.
-	Modular and Extensible: Developers can enhance functionality through plugins and a variety of pre-built connectors, providing flexibility in integrating additional AI services.
-	Multi-Modal Support: The kernel easily expands existing applications to support modalities like voice and video through its architecture
-   Filtering: Developers can use filters to monitor the application, control function invocation or implement Responsible AI.
-   Prompt Templates: Developer can define their prompts using various template languages including Handlebars and Liquid or the built-in Semantic Kernel format.

## What is/are Microsoft Semantic Kernel’s intended use(s)?
The intended uses of Microsoft Semantic Kernel include:
- 	Production Ready Applications: Building small to large enterprise scale solutions that can leverage advanced AI models capabilities.
-	Automation of Business Processes: Facilitating quick and efficient automation of workflows and tasks within organizations.
- 	Integration of AI Services: Connecting client code with a variety of pre-built AI services and capabilities for rapid development.


## How was Microsoft Semantic Kernel evaluated? What metrics are used to measure performance?
Microsoft Semantic Kernel metrics include:
-	Integration Speed: Assessed by the time taken to integrate AI models and initiate functional outputs based on telemetry.
-	Performance Consistency: Measurements taken to verify the system's reliability based on telemetry.


## What are the limitations of Microsoft Semantic Kernel?
Semantic Kernel integrates with Large Language Models (LLMs) to allow AI capabilities to be added to existing application.
LLMs have some inherent limitations such as:
-	Contextual Misunderstanding: The system may struggle with nuanced requests, particularly those involving complex context.
-	Bias in LLM Outputs: Historical biases in the training data can inadvertently influence model outputs. 
	-	Users can mitigate these issues by:
		-	Formulating clear and explicit queries.
		-	Regularly reviewing AI-generated outputs to identify and rectify biases or inaccuracies.
        -   Providing relevant information when prompting the LLM so that it can base it's responses on this data
-   Not all LLMs support all features uniformly e.g., function calling.
Semantic Kernel is constantly evolving and adding new features so:
-   There are some components still being developed e.g., support for some modalities such as Video and Classification, memory connectors for certain Vector databases, AI connectors for certain AI services.
-   There are some components that are still experimental, these are clearly flagged and are subject to change.

## What operational factors and settings allow for effective and responsible use of Microsoft Semantic Kernel?
Operational factors and settings for optimal use include:
-	Custom Configuration Options: Users can tailor system parameters to match specific application needs, such as output style or verbosity.
-	Safe Operating Parameters: The system operates best within defined ranges of input complexity and length, ensuring reliability and safety.
-	Real-Time Monitoring: System behavior should be regularly monitored to detect unexpected patterns or malfunctions promptly.
-	Incorporate RAI and safety tools like Prompt Shield with filters to ensure responsible use.

### Plugins and Extensibility

#### What are plugins and how does Microsoft Semantic Kernel use them?
Plugins are API calls that enhance and extend the capabilities of Microsoft Semantic Kernel by integrating with other services. They can be developed internally or by third-party developers, offering functionalities that users can toggle on or off based on their requirements. The kernel supports OpenAPI specifications, allowing for easy integration and sharing of plugins within developer teams.

#### What data can Microsoft Semantic Kernel provide to plugins? What permissions do Microsoft Semantic Kernel plugins have?
Plugins can access essential user information necessary for their operation, such as:
-	Input Context: Information directly related to the queries and commands issued to the system.
-	Execution Data: Results and performance metrics from previous operations, provided they adhere to user privacy standards. Developers retain control over plugin permissions, choosing what information plugins can access or transmit, ensuring compliance with data protection protocols.
-   Semantic Kernel supports filters which allow developers to integrate with RAI solutions

#### What kinds of issues may arise when using Microsoft Semantic Kernel enabled with plugins?
Potential issues that may arise include:
-	Invocation Failures: Incorrectly triggered plugins can result in unexpected outputs.
-	Output Misinformation: Errors in plugin handling can lead to generation of inaccurate or misleading results.
-	Dependency Compatibility: Changes in external dependencies may affect plugin functionality. To prevent these issues, users are advised to keep plugins updated and to rigorously test their implementations for stability and accuracy

#### When working with AI, the developer can enable content moderation in the AI platforms used, and has complete control on the prompts being used, including the ability to define responsible boundaries and guidelines. For instance:
-	When using Azure OpenAI, by default the service includes a content filtering system that works alongside core models. This system works by running both the prompt and completion through an ensemble of classification models aimed at detecting and preventing the output of harmful content. In addition to the content filtering system, the Azure OpenAI Service performs monitoring to detect content and/or behaviors that suggest use of the service in a manner that might violate applicable product terms. The filter configuration can be adjusted, for example to block also "low severity level" content. See here for more information.
-	The developer can integrate Azure AI Content Safety to detect harmful user-generated and AI-generated content, including text and images. The service includes an interactive Studio online tool with templates and customized workflows. See here for more information.
-	When using OpenAI the developer can integrate OpenAI Moderation to identify problematic content and take action, for instance by filtering it. See here for more information.
-	Other AI providers provide content moderation and moderation APIs, which developers can integrate with Node Engine.

#### If a sequence of components are run, additional risks/failures may arise when using non-deterministic behavior. To mitigate this, developers can:
Implement safety measures and bounds on each component to prevent undesired outcomes.
Add output to the user to maintain control and awareness of the system's state.
In multi-agent scenarios, build in places that prompt the user for a response, ensuring user involvement and reducing the likelihood of undesired results due to multi-agent looping.
