---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: 2025-02-11
deciders: markwallace, sergey, dmytro, weslie, evan, shawn
---

# Structured Concepts

## Context and Problem Statement

Currently, the Concepts project has grown considerably, with many samples that do not consistently follow a structured pattern or guideline.

A revisit of our sample patterns in favor of key drivers needs to be considered.

This ADR starts by suggesting rules we might follow to keep new concepts following good patterns that make them easy to comprehend, find, and descriptive.

The Semantic Kernel audience can vary greatly—from pro-devs, beginners, and non-developers. We understand that making sure examples and guidelines are as straightforward as possible is of our highest priority.

### Decision Drivers

- Easy to find
- Easy to understand
- Easy to set up
- Easy to execute

The above drivers focus on ensuring that we follow good practices, patterns, and a structure for our samples, guaranteeing proper documentation, simplification of code for easier understanding, as well as the usage of descriptive classes, methods, and variables.

We also understand how important it is to ensure our samples are copy-and-paste friendly (work "as is"), being as frictionless as possible.

## Solution

Applying a set of easy-to-follow guidelines and good practices to the Concepts project will help maintain a good collection of samples that are easy to find, understand, set up, and execute.

This guideline will be applied for any maintenance or newly added samples to the Concepts project. The contents may be added to a new CONTRIBUTING.md file in the Concepts project.

> [!NOTE]
> Rules/Conventions that are already ensured by analyzers are not mentioned in the list below.

## Rules

### Sample Classes

Each class in the Concepts project MUST have an xmldoc description of what is being sampled, with clear information on what is being sampled.

✅ DO have xmldoc description detailing what is being sampled.

✅ DO have xmldoc remarks for the required packages.

✅ CONSIDER using xmldoc remarks for additional information.

❌ AVOID using generic descriptions.

✅ DO name classes with at least two words, separated by an underscore `First_Second_Third_Fourth`.

✅ DO name classes with the `First` word reserved for the given concept or provider name (e.g., `OpenAI_ChatCompletion`).

When the file has examples for a specific `<provider>`, it should start with the `<provider>` as the first word. `<provider>` here can also include runtime, platform, protocol, or service names.

✅ CONSIDER naming `Second` and later words to create the best grouping for examples,  
e.g., `AzureAISearch_VectorStore_ConsumeFromMemoryStore`.

✅ CONSIDER naming when there are more than two words, using a left-to-right grouping,  
e.g., `AzureAISearch_VectorStore_ConsumeFromMemoryStore`: for `AzureAISearch` within `VectorStore` grouping, there's a `ConsumeFromMemoryStore` example.

### Sample Methods

✅ DO have an xmldoc description detailing what is being sampled when the class has more than one sample method.

✅ DO have descriptive method names limited to five words, separated by an underscore,  
e.g., `[Fact] public Task First_Second_Third_Fourth_Fifth()`.

❌ DO NOT use `Async` suffix for Tasks.

❌ AVOID using parameters in the method signature.

❌ DO NOT have more than 3 samples in a single class. Split the samples into multiple classes when needed.

### Code

✅ DO keep code clear and concise. For the most part, variable names and APIs should be self-explanatory.

✅ CONSIDER commenting the code for large sample methods.

❌ DO NOT use acronyms or short names for variables, methods, or classes.

❌ AVOID any references to common helper classes or methods that are not part of the sample file,  
e.g., avoid methods like `BaseTest.OutputLastMessage`.

## Decision Outcome

TBD
