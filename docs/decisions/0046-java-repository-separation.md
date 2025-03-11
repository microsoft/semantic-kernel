---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: John Oliver
date: 2024-06-18
---

# Separate Java Repository To a Separate Code Base

## Context and Problem Statement

Managing multiple languages within a single repository provides some challenges with respect to how different languages and their build tools
manage repositories. Particularly with respect to how common build tooling for Java, like Apache Maven, interacts with repositories. Typically,
while doing a Maven release you want to be able to freeze your repository so that commits are not being added while
preparing a release. To achieve this in a shared repository we would effectively need to request all languages halt
merging pull requests while we are in this process. The Maven release process also interacts badly with the projects
desire for merges to be squashed which for the most part blocks a typical Maven release process that needs to push
multiple commits into a repository.

Additionally, from a discoverability standpoint, in the original repository the majority of current pull requests, issues and activity are from
other languages. This has created some
confusion from users about if the semantic kernel repository is the correct repository for Java. Managing git history
when performing tasks such as looking
at diffs or compiling release notes is also significantly harder when the majority of commits and code are unrelated to Java.

Also managing repository policies that are preferred by all languages is a challenge as we have to produce a more
complex build process to account for building multiple languages. If a user makes accidental changes to the repository outside their own language,
or make changes to the common files, require sign off from other languages, leading to delays as we
require review from users in other languages. Similarly common files such as GitHub Actions workflows, `.gitignore`, VS Code settings, `README.md`, `.editorconfig` etc, become
more complex as they have to simultaneously support multiple languages.

In a community point of view, having a separate repo will foster community engagement, allowing developers to contribute, share ideas, and collaborate on the Java projects only.
Additionally, it enables transparent tracking of contributions, making it easy to identify top contributors and acknowledge their efforts. 
Having a single repository will also provide valuable statistics on commits, pull requests, and other activities, helping maintainers monitor project progress and activity levels. 

## Decision Drivers

- Allow project settings that are compatible with Java tooling
- Improve the communities' ability to discover and interact with the Java project
- Improve the ability for the community to observe changes to the Java project in isolation
- Simplify repository build/files to concentrate on a single language

## Considered Options

We have in the past run out of a separate branch within the [Semantic Kernel](https://github.co/microsoft/semantic-kernel) repository which solved 
some of the issues however significantly hindered user discoverability as users expect to find the latest code on the main branch.

## Decision Outcome

Java repository has been moved to [semantic-kernel-java](https://github.com/microsoft/semantic-kernel-java)
