---
status: accepted
contact: markwallace
date: 2024-06-10
deciders: sergeymenshykh, mbolan, rbarreto, dmytrostruk, westey
consulted: 
informed: 
---

# Guidance for Breaking Changes

## Context and Problem Statement

We must avoid breaking changes in .Net because of the well known [diamond dependency issue](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/dependencies#diamond-dependencies) where breaking changes between different versions of the same package cause bugs and exceptions at run time.

## Decision Drivers

Breaking changes are only allowed under the following circumstances:

- Updates to an experimental feature i.e. we have learnt something new and need to modify the design of an experimental feature.
- When one of our dependencies introduces an unavoidable breaking change.

All breaking changes must be clearly documented, definitely in the release notes and possibly also via a migration guide Blog post.

- Include a detailed description of the breaking change in the PR description so that it is included in the release notes.
- Update Learn Site migration guide documentation and have this published to coincide with the release which includes the breaking change.

In all other cases we must avoid breaking changes. There will be situations where we need to move to accommodate a change to one of our dependencies or introduce a new capability e.g.

- When we find a security issue or a severe bug (e.g. data loss).
- One of our dependencies introduces a major breaking change e.g. the introduction of the new OpenAI SDK.
- When we find a severe limitation in our current implementation e.g. when the AI services introduce a new capability.

In these cases we will plan to obsolete the API(s) and provide a documented migration path to the new preferred pattern.
An example of this will be the switch to the new OpenAI .Net SDK.
During this transition there will be a period where the new and old API's will be supported to allow customers to migrate.

## Decision Outcome

Chosen option: We must avoid breaking changes in .Net because of the well known diamond dependency issue.
