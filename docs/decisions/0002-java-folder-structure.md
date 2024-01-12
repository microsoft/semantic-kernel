---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2013-06-19
deciders: shawncal,johnoliver
consulted: 
informed:
---
# Java Folder Structure

## Context and Problem Statement

A port of the Semantic Kernel to Java is under development in the `experimental-java` branch. The folder structure being used has diverged from the .Net implementation.
The purpose of this ADR is to document the folder structure that will be used by the Java port to make it clear to developers how to navigate between the .Net and Java implementations.

## Decision Drivers

* Goal is to learn for SDKs that already have excellent multiple language support e.g., [Azure SDK](https://github.com/Azure/azure-sdk/)
* The Java SK should follow the general design guidelines and conventions of Java. It should feel natural to a Java developer.
* Different language versions should be consistent with the .Net implementation. In cases of conflict, consistency with Java conventions is the highest priority.
* The SK for Java and .Net should feel like a single product developed by a single team.
* There should be feature parity between Java and .Net. Feature status must be tracked in the [FEATURE_MATRIX](../../FEATURE_MATRIX.md)

## Considered Options

Below is a comparison of .Net and Java Folder structures

```bash
dotnet/src
           Connectors
           Extensions
           IntegrationTests
           InternalUtilities
           SemanticKernel.Abstractions
           SemanticKernel.MetaPackage
           SemanticKernel.UnitTests
           SemanticKernel
           Skills
```

| Folder                         | Description |
|--------------------------------|-------------|
| Connectors                     | Parent folder for various Connector implementations e.g., AI or Memory services |
| Extensions                     | Parent folder for SK extensions e.g., planner implementations |
| IntegrationTests               | Integration tests |
| InternalUtilities              | Internal utilities i.e., shared code |
| SemanticKernel.Abstractions    | SK API definitions |
| SemanticKernel.MetaPackage     | SK common package collection |
| SemanticKernel.UnitTests       | Unit tests |
| SemanticKernel                 | SK implementation |
| Skills                         | Parent folder for various Skills implementations e.g., Core, MS Graph, GRPC, OpenAI, ... |

Some observations:

* The `src` folder is at the very start of the folder structure, which reduces flexibility
* The use of the `Skills` term is due to change

```bash
java
     api-test
     samples
     semantickernel-api
     semantickernel-bom
     semantickernel-connectors-parent
     semantickernel-core-skills
     semantickernel-core
     semantickernel-extensions-parent
```

| Folder                              | Description |
|-------------------------------------|-------------|
| `api-test`                          | Integration tests and API usage example |
| `samples`                           | SK samples |
| `semantickernel-api`                | SK API definitions |
| `semantickernel-bom`                | SK Bill Of Materials |
| `semantickernel-connectors-parent`  | Parent folder for various Connector implementations |
| `semantickernel-core-skills`        | SK core skills (in .Net these are part of the core implementation) |
| `semantickernel-core`               | SK core implementation |
| `semantickernel-extensions-parent`  | Parent folder for SK extensions e.g., planner implementation |

Some observations:

* Using lowercase folder name with the `-` delimiter is idiomatic Java
* The `src` folders are located as close as possible to the source files e.g., `semantickernel-api/src/main/java`, this is idiomatic Java
* Unit tests are contained together with the implementation
* The samples are located within the `java` folder and each sample runs standalone

## Decision Outcome

Follow these guidelines:

* The folder names will match those used (or planned for .Net) but in the idiomatic Java folder naming convention
* Use `bom` instead of `MetaPackage` as the latter is .Net centric
* Use `api` instead of `Abstractions` as the latter is .Net centric
* Move `semantickernel-core-skills` to a new `plugins` folder and rename to `plugins-core`
* Use the term `plugins` instead of `skills` and avoid introducing technical debt

| Folder                           | Description |
|----------------------------------|-------------|
| `connectors`                     | Containing: `semantickernel-connectors-ai-openai`, `semantickernel-connectors-ai-huggingface`, `semantickernel-connectors-memory-qadrant`, ...  |
| `extensions`                     | Containing: `semantickernel-planning-action-planner`, `semantickernel-planning-sequential-planner` |
| `integration-tests`              | Integration tests |
| `semantickernel-api`             | SK API definitions |
| `semantickernel-bom`             | SK common package collection |
| `semantickernel-core`            | SK core implementation |
| `plugins`                        | Containing: `semantickernel-plugins-core`, `semantickernel-plugins-document`, `semantickernel-plugins-msgraph`, ... |
