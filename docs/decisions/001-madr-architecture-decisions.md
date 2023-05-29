---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-05-29
deciders: dluc,shawncal,hathind
consulted: 
informed: 
---
# Use Markdown Any Decision Records to track Semantic Kernel Architecture Decisions

## Context and Problem Statement

We have multiple different language versions of the Semantic Kernel under active development i.e., C#, Python, Java and Typescript.
We need a way to keep the implementations aligned with regard to key architectural decisions e.g., we are reviewing a change to the format used to store
semantic function configuration (config.json) and when this change is agreed it must be reflected in all of the Semantic Kernel implementations.

MADR is a lean template to capture any decisions in a structured way. The template originated from capturing architectural decisions and developed to a template allowing to capture any decisions taken.
For more information [see](https://adr.github.io/madr/)

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers

* Architecture changes and the associated decision making process should be transparent to the community.
* Decision records are stored in the repository and are easily discoverable for teams involved in the various language ports.

## Considered Options

* Use MADR format and store decision documents in the repository.

## Decision Outcome

Chosen option:

## Pros and Cons of the Options

### Use MADR format and store decision documents in the repository

* Good, because lightweight format which is easy to edit
* Good, because this uses the standard Git review process for commenting and approval
* Good, because decisions and review process are transparent to the community
