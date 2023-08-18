# Contributing to Semantic Kernel

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

### Breaking Changes

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
When considering contributions to plugins and memory connectors for Semantic Kernel, please note the following guidelines:
#### Plugins
We appreciate your interest in extending Semantic Kernel's functionality through plugins. However, we want to clarify our approach to hosting plugins within our GitHub repository. To maintain a clean and manageable codebase, we will not be hosting plugins directly in the Semantic Kernel GitHub repository.
Instead, we encourage contributors to host their plugin code in separate repositories under their own GitHub accounts or organization. You can then provide a link to your plugin repository in the relevant discussions, issues, or documentation within the Semantic Kernel repository. This approach ensures that each plugin can be maintained independently and allows for easier tracking of updates and issues specific to each plugin.
#### Memory Connectors
For memory connectors, while we won't be directly adding hosting for them within the Semantic Kernel repository, we highly recommend building memory connectors as separate plugins. Memory connectors play a crucial role in interfacing with external memory systems, and treating them as plugins enhances modularity and maintainability.

### PR - CI Process

The continuous integration (CI) system will automatically perform the required
builds and run tests (including the ones you are expected to run) for PRs. Builds
and test runs must be clean.

If the CI build fails for any reason, the PR issue will be updated with a link
that can be used to determine the cause of the failure.
