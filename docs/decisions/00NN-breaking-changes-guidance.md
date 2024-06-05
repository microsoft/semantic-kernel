---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: markwallace
date: 2024-06-05
deciders: sergeymenshykh, mbolan, rbarreto, dmytrostruk, westey
consulted: 
informed: 
---

# Guidance for Breaking Changes

## Context and Problem Statement

We must avoid breaking changes in .Net because of the well known [diamond dependency issue](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/dependencies#diamond-dependencies)

## Decision Drivers

Breaking changes are allowed under the following circumstances

- Updates to an experimental feature i.e. we have learnt something new and need to modify the design
- When one of our dependencies introduces a breaking change e.g. the introduction of the new OpenAI SDK
- When we find a security issue or a severe bug (e.g. data loss) 
- When we find a severe limitation in our current implementation e.g. when the industry has changed (3 AI services...)

All breaking changes must be clearly documented, definitely in the release notes and possibly also via a migration guide Blog post.

- 

In all other cases we must avoid breaking changes

- We must obsolete API if we determine there is a preferred pattern we want customer to switch to

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.
