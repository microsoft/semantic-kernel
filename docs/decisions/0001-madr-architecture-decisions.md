---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-05-29
deciders: dluc,shawncal,hathind,alliscode
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

How would we use ADR's to track technical decisions?

1. Copy docs/decisions/adr-template.md to docs/decisions/NNNN-title-with-dashes.md, where NNNN indicates the next number in sequence.
    1. Check for existing PR's to make sure you use the correct sequence number.
    2. There is also a short form template docs/decisions/adr-short-template.md
2. Edit NNNN-title-with-dashes.md.
    1. Status must initially be `proposed`
    2. List of `deciders` must include the aliases of the people who will sign off on the decision.
    3. The relevant EM and `dluc` must be listed as deciders or informed of all decisions.
    4. You should list the aliases of all partners who were consulted as part of the decision.
3. For each option list the good, neutral and bad aspects of each considered alternative.
    1. Detailed investigations can be included in the `More Information` section inline or as links to external documents.
4. Share your PR with the deciders and other interested parties.
   1. Deciders must be listed as required reviewers.
   2. The status must be updated to `accepted` once a decision is agreed and the date must also be updated.
   3. Approval of the decision is captured using PR approval.
5. Decisions can be changed later and superseded by a new ADR. In this case it is useful to record any negative outcomes in the original ADR.

* Good, because lightweight format which is easy to edit
* Good, because this uses the standard Git review process for commenting and approval
* Good, because decisions and review process are transparent to the community
