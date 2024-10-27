# Contributing to Semantic Kernel

> ℹ️ **NOTE**: The Python SDK for Semantic Kernel is currently in preview. While most
> of the features available in the C# SDK have been ported, there may be bugs and
> we're working on some features still - these will come into the repo soon. We are
> also actively working on improving the code quality and developer experience,
> and we appreciate your support, input and PRs!

You can contribute to Semantic Kernel with issues and pull requests (PRs). Simply
filing issues for problems you encounter is a great way to contribute. Contributing
code is greatly appreciated.

## Reporting Issues

We always welcome bug reports, API proposals and overall feedback. Here are a few
tips on how you can make reporting your issue as effective as possible.

### Where to Report

New issues can be reported in our [list of issues](https://github.com/microsoft/semantic-kernel/issues).

Before filing a new issue, please search the list of issues to make sure it does
not already exist.

If you do find an existing issue for what you wanted to report, please include
your own feedback in the discussion. Do consider upvoting (👍 reaction) the original
post, as this helps us prioritize popular issues in our backlog.

### Writing a Good Bug Report

Good bug reports make it easier for maintainers to verify and root cause the
underlying problem.
The better a bug report, the faster the problem will be resolved. Ideally, a bug
report should contain the following information:

- A high-level description of the problem.
- A _minimal reproduction_, i.e. the smallest size of code/configuration required
  to reproduce the wrong behavior.
- A description of the _expected behavior_, contrasted with the _actual behavior_ observed.
- Information on the environment: OS/distribution, CPU architecture, SDK version, etc.
- Additional information, e.g. Is it a regression from previous versions? Are there
  any known workarounds?

## Contributing Changes

Project maintainers will merge accepted code changes from contributors.

### DOs and DON'Ts

DO's:

- **DO** follow the standard coding conventions

  - [.NET](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
  - [Python](https://pypi.org/project/black/)
  - [Typescript](https://typescript-eslint.io/rules/)/[React](https://github.com/jsx-eslint/eslint-plugin-react/tree/master/docs/rules)

- **DO** give priority to the current style of the project or file you're changing
  if it diverges from the general guidelines.
- **DO** include tests when adding new features. When fixing bugs, start with
  adding a test that highlights how the current behavior is broken.
- **DO** keep the discussions focused. When a new or related topic comes up
  it's often better to create new issue than to side track the discussion.
- **DO** clearly state on an issue that you are going to take on implementing it.
- **DO** blog and tweet (or whatever) about your contributions, frequently!

DON'Ts:

- **DON'T** surprise us with big pull requests. Instead, file an issue and start
  a discussion so we can agree on a direction before you invest a large amount of time.
- **DON'T** commit code that you didn't write. If you find code that you think is a good
  fit to add to Semantic Kernel, file an issue and start a discussion before proceeding.
- **DON'T** submit PRs that alter licensing related files or headers. If you believe
  there's a problem with them, file an issue and we'll be happy to discuss it.
- **DON'T** make new APIs without filing an issue and discussing with us first.

## Breaking Changes

Contributions must maintain API signature and behavioral compatibility. Contributions
that include breaking changes will be rejected. Please file an issue to discuss
your idea or change if you believe that a breaking change is warranted.

### Suggested Workflow

We use and recommend the following workflow:

1. Create an issue for your work.
   - You can skip this step for trivial changes.
   - Reuse an existing issue on the topic, if there is one.
   - Get agreement from the team and the community that your proposed change is
     a good one.
   - Clearly state that you are going to take on implementing it, if that's the case.
     You can request that the issue be assigned to you. Note: The issue filer and
     the implementer don't have to be the same person.
2. Create a personal fork of the repository on GitHub (if you don't already have one).
3. In your fork, create a branch off of main (`git checkout -b mybranch`).
   - Name the branch so that it clearly communicates your intentions, such as
     "issue-123" or "githubhandle-issue".
4. Make and commit your changes to your branch.
5. Add new tests corresponding to your change, if applicable.
6. Run the relevant scripts in [the section below](https://github.com/microsoft/semantic-kernel/blob/main/CONTRIBUTING.md#dev-scripts) to ensure that your build is clean and all tests are passing.
7. Create a PR against the repository's **main** branch.
   - State in the description what issue or improvement your change is addressing.
   - Verify that all the Continuous Integration checks are passing.
8. Wait for feedback or approval of your changes from the code maintainers.
9. When area owners have signed off, and all checks are green, your PR will be merged.

### Development scripts

The scripts below are used to build, test, and lint within the project.

- Python: see [python/DEV_SETUP.md](https://github.com/microsoft/semantic-kernel/blob/main/python/DEV_SETUP.md#pipeline-checks).
- .NET:
  - Build/Test: `run build.cmd` or `bash build.sh`
  - Linting (auto-fix): `dotnet format`
- Typescript:
  - Build/Test: `yarn build`
  - Linting (auto-fix): `yarn lint:fix`

### Adding Plugins and Memory Connectors

When considering contributions to plugins and memory connectors for Semantic
Kernel, please note the following guidelines:

#### Plugins

We appreciate your interest in extending Semantic Kernel's functionality through
plugins. However, we want to clarify our approach to hosting plugins within our
GitHub repository. To maintain a clean and manageable codebase, we will not be
hosting plugins directly in the Semantic Kernel GitHub repository.
Instead, we encourage contributors to host their plugin code in separate
repositories under their own GitHub accounts or organization. You can then
provide a link to your plugin repository in the relevant discussions, issues,
or documentation within the Semantic Kernel repository. This approach ensures
that each plugin can be maintained independently and allows for easier tracking
of updates and issues specific to each plugin.

#### Memory Connectors

For memory connectors, while we won't be directly adding hosting for them within
the Semantic Kernel repository, we highly recommend building memory connectors
as separate plugins. Memory connectors play a crucial role in interfacing with
external memory systems, and treating them as plugins enhances modularity and
maintainability.

### Examples and Use Cases

To help contributors understand how to use the repository effectively, we have included some examples and use cases below:

#### Example 1: Adding a New Feature

1. Identify the feature you want to add and create an issue to discuss it with the community.
2. Fork the repository and create a new branch for your feature.
3. Implement the feature in your branch, following the coding standards and guidelines.
4. Add tests to verify the new feature works as expected.
5. Run the development scripts to ensure your changes do not break the build or existing tests.
6. Create a pull request with a description of the feature and link to the issue.
7. Address any feedback from maintainers and community members.
8. Once approved, your feature will be merged into the main branch.

#### Example 2: Fixing a Bug

1. Identify the bug and create an issue to discuss it with the community.
2. Fork the repository and create a new branch for your bug fix.
3. Write a test that reproduces the bug.
4. Implement the fix in your branch.
5. Run the development scripts to ensure your changes do not break the build or existing tests.
6. Create a pull request with a description of the bug and the fix, and link to the issue.
7. Address any feedback from maintainers and community members.
8. Once approved, your bug fix will be merged into the main branch.

#### Example 3: Improving Documentation

1. Identify the documentation that needs improvement and create an issue to discuss it with the community.
2. Fork the repository and create a new branch for your documentation improvements.
3. Make the necessary changes to the documentation in your branch.
4. Run the development scripts to ensure your changes do not break the build or existing tests.
5. Create a pull request with a description of the documentation improvements and link to the issue.
6. Address any feedback from maintainers and community members.
7. Once approved, your documentation improvements will be merged into the main branch.

By following these examples and use cases, you can effectively contribute to the Semantic Kernel repository and help improve the project for everyone.

