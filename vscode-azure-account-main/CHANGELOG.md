# Change Log
All notable changes to the "ms-vscode.azure-account" extension will be documented in this file.

## [0.12.0] - 2024-05-14

In preparation of the [Azure Account extension being deprecated](https://github.com/microsoft/vscode-azure-account/issues/964) at the end of the year, we've moved the Azure Cloud Shell feature to the [Azure Resources extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureresourcegroups). Apart from moving codebases, the feature is the same from a users perspective. Authentication for the Cloud Shell feature is now handled by the VS Code built-in Microsoft authentication provider, which means you may have to login upon first use of the migrated feature.

Additionally, we've fixed two longstanding Azure Cloud Shell bugs that caused issues launching the feature on Linux and macOS: [#719](https://github.com/microsoft/vscode-azure-account/issues/719) and [#959](https://github.com/microsoft/vscode-azure-account/issues/959).

### Changed
* [[958]](https://github.com/microsoft/vscode-azure-account/pull/958) Depend on Azure Resources extension for the Azure Cloud Shell feature 

### Fixed

* [[855]](https://github.com/microsoft/vscode-azureresourcegroups/pull/855) Stop using `--ms-enable-electron-run-as-node` flag to fix launching Cloud Shell on macOS
* [[854]](https://github.com/microsoft/vscode-azureresourcegroups/pull/854) Use `process.execPath` instead of `process.argv0` to fix launching Cloud Shell on Linux

## [0.11.7] - 2024-04-30

### Added
* Support ephemeral cloud shell sessions [#950](https://github.com/microsoft/vscode-azure-account/pull/950)

## [0.11.6] - 2023-10-06

### Fixed
* Fix 500 error when launching cloud shell by setting the referer header [#866](https://github.com/microsoft/vscode-azure-account/pull/866)

### Changed
* Add manage account command to make sign out easier to find in [#820](https://github.com/microsoft/vscode-azure-account/pull/820)
* Remove use of AAD Graph for cloud shell in [#851](https://github.com/microsoft/vscode-azure-account/pull/851)

## [0.11.5] - 2023-05-16

### Fixed
* Fix launching cloud console by @alexweininger in [#809](https://github.com/microsoft/vscode-azure-account/pull/809)

## [0.11.4] - 2023-05-02

### Added
* Add detailed logging  by @alexweininger in [#750](https://github.com/microsoft/vscode-azure-account/pull/750)

### Fixed
* Don't await nps survey by @alexweininger in [#709](https://github.com/microsoft/vscode-azure-account/pull/709)

### Dependencies
* Bump version post release by @alexweininger in [#701](https://github.com/microsoft/vscode-azure-account/pull/701)
* Bump webpack from 5.69.0 to 5.76.0 by @dependabot in [#736](https://github.com/microsoft/vscode-azure-account/pull/736)
* Bump xml2js and @azure/ms-rest-js in /sample by @dependabot in [#778](https://github.com/microsoft/vscode-azure-account/pull/778)

## [0.11.3] - 2023-01-18

### Fixed
* Fixed issues with Azure Cloud Shell terminal when connected to a remote host @alexweininger in https://github.com/microsoft/vscode-azure-account/pull/684

### Dependencies
* Bump @xmldom/xmldom from 0.7.5 to 0.7.8 by @dependabot in [#663](https://github.com/microsoft/vscode-azure-account/pull/663)
* Bump loader-utils from 1.4.0 to 1.4.1 by @dependabot in [#666](https://github.com/microsoft/vscode-azure-account/pull/666)
* Bump loader-utils from 1.4.1 to 1.4.2 by @dependabot in [#670](https://github.com/microsoft/vscode-azure-account/pull/670)
* Bump decode-uri-component from 0.2.0 to 0.2.2 by @dependabot in [#678](https://github.com/microsoft/vscode-azure-account/pull/678)
* Bump json5 from 1.0.1 to 1.0.2 by @dependabot in [#692](https://github.com/microsoft/vscode-azure-account/pull/692)
* Bump jsonwebtoken and @azure/msal-node by @dependabot in [#696](https://github.com/microsoft/vscode-azure-account/pull/696)

### Other
* Fix readme badges by @bwateratmsft in [#653](https://github.com/microsoft/vscode-azure-account/pull/653)

## [0.11.2] - 2022-10-07

### Added
- Add Support for Workspace Trust [#624](https://github.com/microsoft/vscode-azure-account/pull/624)

### Fixed
- Update http-proxy-agent and https-proxy-agent [#640](https://github.com/microsoft/vscode-azure-account/pull/640)

## [0.11.1] - 2022-08-03

### Fixed
- Don't prompt to sign out and reload on first run [#603](https://github.com/microsoft/vscode-azure-account/pull/603)
- Revert removal of prompt property in query string. [#595](https://github.com/microsoft/vscode-azure-account/pull/595)

## [0.11.0]

### Changed
- Log all URLs that the extension tries to reach [#520](https://github.com/microsoft/vscode-azure-account/pull/520)
- Use new redirect server [#546](https://github.com/microsoft/vscode-azure-account/pull/546)
- Update @vscode/extension-telemetry to 0.6.2 [#588](https://github.com/microsoft/vscode-azure-account/pull/588)

### Fixed
- Errors in cloud shell when switching authentication library [#380](https://github.com/microsoft/vscode-azure-account/pull/380)
- Show toast notification prompting to sign out/back in when changing settings [#511](https://github.com/microsoft/vscode-azure-account/pull/511)

## [0.10.1]

### Added
- A long-running notification is shown for the duration of the sign-in process which allows cancellation.
- MSAL support for sovereign clouds

### Fixed
- The `Azure: Tenant` setting was improperly configured when running the `Azure: Sign In to Azure Cloud` command.

## [0.10.0]

### Added
- Support for the Microsoft Authentication Library (MSAL) via the `Azure: Authentication Library` setting.
- The `Azure: Select Tenant` command allows you to view/select available tenants or enter a custom tenant.
- The extension now supports a [versioned API](https://github.com/microsoft/vscode-azure-account/blob/main/src/azure-account.api.d.ts) 
accessible by calling [`getApi`](https://github.com/microsoft/vscode-azuretools/blob/d38498f0085deb912675e4d2cb376f973c12f31e/utils/api.d.ts#L22)
on the extension's exports. A [legacy API](https://github.com/microsoft/vscode-azure-account/blob/main/src/azure-account.legacy.api.d.ts)
is still supported.

### Changed
- The `Azure: Open Bash in Cloud Shell` and `Azure: Open PowerShell in Cloud Shell` commands have been replaced with entry
points in the VS Code terminal view. See [README.md](https://github.com/microsoft/vscode-azure-account#azure-cloud-shell) for more details.
- `credentials2` (exported from the API) is now typed as `TokenCredentialsBase | TokenCredential` to accommodate Track 1 and 2 Azure SDKs.

## [0.9.11]
- Fix Cloud Shell failure introduced in VS Code v1.62.1 [#357](https://github.com/microsoft/vscode-azure-account/pull/357)

## [0.9.10]
- Fix experimentation framework initialization

## [0.9.9]
- Add experimentation framework

## [0.9.8]
- When signing into a different cloud than previously used, shows a prompt to enter tenant id.

## [0.9.7]
- Add "CustomCloud" as an available Azure Environemnt, and `customCloud.resourceManagerEndpointUrl` to set the endpoint to use for this
- Removes `azureStackApiProfile`
- Fix #231, open in powershell does not show directory list
- Fix #250, sign in does not work when PPE setting does not include `activeDirectoryEndpointUrl`
- Update dependencies

## [0.9.6]
- Add `azureStackApiProfile` property to environments.

## [0.9.5]
- Add support for Azure Stack.

## [0.9.4]
- Fix removal of old refresh tokens using previous environment names [#234](https://github.com/microsoft/vscode-azure-account/issues/234)
- Use cloud metadata for endpoint discovery [#188](https://github.com/microsoft/vscode-azure-account/issues/188)

## [0.9.3]
- Fix sign in to Azure clouds [#214](https://github.com/microsoft/vscode-azure-account/issues/214) [#215](https://github.com/microsoft/vscode-azure-account/issues/215)

## [0.9.2]
- Update callback urls for Codespaces

## [0.9.1]
- Update lodash dependency

## [0.9.0]
- Migrate to new Azure SDK packages and expose new credentials object [#140](https://github.com/microsoft/vscode-azure-account/issues/140)
- Fix sign in for ADFS based Azure Stack environment [#190](https://github.com/microsoft/vscode-azure-account/issues/190)
- Update sign in page styles to use new product icon [#184](https://github.com/microsoft/vscode-azure-account/issues/184)

## [0.8.11]
- Add support for codespaces

## [0.8.9]
- Update dependencies
- Change sign in notification text [#168](https://github.com/Microsoft/vscode-azure-account/issues/168)

## [0.8.8]
- Adopt vscode.env.asExternalUri API

## [0.8.7]
- Update dependencies
- Read formatted JSON in addition to refresh tokens stored in credential manager

## [0.8.6]
- Fix query state handling for url handler based authentication flow

## [0.8.5]
- Support url handler based authentication flow
- Log errors from checking online status [#147](https://github.com/Microsoft/vscode-azure-account/issues/147)

## [0.8.4]
- Fixes for ADFS ([#105](https://github.com/Microsoft/vscode-azure-account/issues/105)).
- Pass nonce through initial redirect ([#136](https://github.com/Microsoft/vscode-azure-account/issues/136)).

## [0.8.3]
- Telemetry now includes the Azure subscription IDs.

## [0.8.2]
- Detect when local server cannot be connected to ([#136](https://github.com/Microsoft/vscode-azure-account/issues/136)).
- Update dependencies.

## [0.8.1]
- Ignore errors from keytar ([#59](https://github.com/Microsoft/vscode-azure-account/issues/59)).
- Use openExternal API for opening URIs ([#110](https://github.com/Microsoft/vscode-azure-account/issues/110)).
- Use GET to see if login endpoint is reachable ([#121](https://github.com/Microsoft/vscode-azure-account/issues/121)).
- Use localhost for redirect with ADFS ([#105](https://github.com/Microsoft/vscode-azure-account/issues/105)).

## [0.8.0]
- Simplified sign in ([#75](https://github.com/Microsoft/vscode-azure-account/issues/75)).
- Setting for specifying PPE environment.

## [0.7.1]
- Update dependencies.
- Include generated ThirdPartyNotice.txt.

## [0.7.0]
- Test system proxy support ([#27](https://github.com/Microsoft/vscode-azure-account/issues/27)).

## [0.6.2]
- Update README with settings ([#107](https://github.com/Microsoft/vscode-azure-account/pull/107)).
- Add README and CHANGELOG back to packaged extension.

## [0.6.1]
- Check connection state before logging in ([#106](https://github.com/Microsoft/vscode-azure-account/issues/106)).

## [0.6.0]
- Bundle using Webpack ([#87](https://github.com/Microsoft/vscode-azure-account/issues/87)).

## [0.5.1]
- Unable to get the subscription list from Azure China ([#103](https://github.com/Microsoft/vscode-azure-account/issues/103)).
- Handle case where home tenant is not listed ([#102](https://github.com/Microsoft/vscode-azure-account/issues/102)).

## [0.5.0]
- Support national clouds ([#83](https://github.com/Microsoft/vscode-azure-account/issues/83)).
- Support user-supplied tenants ([#58](https://github.com/Microsoft/vscode-azure-account/issues/58)).
- Indicate when there are no subscriptions ([#51](https://github.com/Microsoft/vscode-azure-account/issues/51)).
- Update dependencies.

## [0.4.3]
- Setting to hide email ([#66](https://github.com/Microsoft/vscode-azure-account/issues/66)).
- Only offer tenants with at least one subscription  ([#47](https://github.com/Microsoft/vscode-azure-account/issues/47)).
- Ignore focus-out in tenant picker ([#77](https://github.com/Microsoft/vscode-azure-account/issues/77)).

## [0.4.2]
- Request PowerShell Core on Linux, replacing PowerShell on Windows.
- Fix reading initial size ([#76](https://github.com/Microsoft/vscode-azure-account/issues/76)).

## [0.4.1]
- Update icon to 'key' ([#55](https://github.com/Microsoft/vscode-azure-account/issues/55)).
- Add NPS user survey
- Update dependencies
- Check if there is a default domain ([#68](https://github.com/Microsoft/vscode-azure-account/issues/68)).

## [0.4.0]
- Add command to upload files to Cloud Shell
- Use multi-select picker for subscription filter ([Microsoft/vscode#45589](https://github.com/Microsoft/vscode/issues/45589)).
- Add timeout in promise race ([#46](https://github.com/Microsoft/vscode-azure-account/pull/46)).
- Keep going after signing in ([#45](https://github.com/Microsoft/vscode-azure-account/issues/45)).

## [0.3.3]
- Robustness against tenant details not resolving ([#33](https://github.com/Microsoft/vscode-azure-account/issues/33)).
- Promote API to create a Cloud Shell ([#34](https://github.com/Microsoft/vscode-azure-account/issues/34)).

## [0.3.2]
- Let the user pick the tenant to open a Cloud Shell for ([#33](https://github.com/Microsoft/vscode-azure-account/issues/33))
- Experimental API to create a Cloud Shell ([#34](https://github.com/Microsoft/vscode-azure-account/issues/34))
- Remove extraneous "Close" button ([#41](https://github.com/Microsoft/vscode-azure-account/issues/41))
- Update moment.js

## [0.3.1]
- Support for ASAR in preparation for [Microsoft/vscode#36997](https://github.com/Microsoft/vscode/issues/36997)

## [0.3.0]
- Cache subscriptions for faster startup
- Improved progress indication when starting Cloud Shell
- Bug fixes
	- Ignore failing tenants when signing in
	- Send ping on Cloud Shell websocket to keep alive
	- Supply graph and key vault tokens to Cloud Shell

## [0.2.2]
- Bug fix: Do not modify configuration object

## [0.2.1]
- Bug fixes
	- Avoid having to click 'Copy & Open' to advance the login
	- Retry resizing terminal on 503, 504

## [0.2.0]
- Cloud Shell integration
- API for subscriptions cache

## [0.1.3]
- API change: addFilter -> selectSubscriptions
- When no subscriptions found, suggest signing up for an account

## [0.1.0]
- Initial release
