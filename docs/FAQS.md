# Frequently Asked Questions

### How do I get access to nightly builds?

Nightly builds of the Semantic Kernel are available [here](https://github.com/orgs/microsoft/packages?repo_name=semantic-kernel).

To download nightly builds follow the following steps:

1. You will need a GitHub account to complete these steps.
1. Create a GitHub Personal Access Token with the `read:packages` scope using these [instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).
1. If you account is part of the Microsoft organization then you must authorize the `Microsoft` organization as a single sign-on organization.
    1. Click the "Configure SSO" next to the Person Access Token you just created and then authorize `Microsoft`.
1. Create a `NuGet.Config` file.

    ```xml
    <?xml version="1.0" encoding="utf-8"?>
    <configuration>
      <packageSources>
        <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
        <add key="github" value="https://nuget.pkg.github.com/microsoft/index.json" />
      </packageSources>
    
      <packageSourceMapping>
        <packageSource key="nuget.org">
          <package pattern="*" />
        </packageSource>
        <packageSource key="github">
          <package pattern="*nightly"/>
        </packageSource>
      </packageSourceMapping>
    
      <packageSourceCredentials>
        <github>
            <add key="Username" value="<Your GitHub Id>" />
            <add key="ClearTextPassword" value="<Your Personal Access Token>" />
          </github>
      </packageSourceCredentials>
    </configuration>
    ```

    * If you place this file in your project folder make sure to have Git (or whatever source control you use) ignore it.
    * For more information on where to store this file go [here](https://learn.microsoft.com/en-us/nuget/reference/nuget-config-file).
1. You can now add packages from the nightly build to your project.
    * E.g. use this command `dotnet add package Microsoft.SemanticKernel.Core --version 0.26.231003.1-nightly`
