---
status: accepted
contact: markwallace
date: 2024-023-2706
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk
consulted: matthewbolanos
informed: matthewbolanos
---

# Semantic Kernel Release Versioning

## Context and Problem Statement

This ADR summarizes the approach used to change the package version numbers when releasing a new version of the Semantic Kernel.

The ADR is relevant to the .Net, Java and Python releases of the Semantic Kernel (once the packages reach v1.0).

1. [Semantic Kernel on NuGet](https://www.nuget.org/packages/Microsoft.SemanticKernel/)
1. [Semantic Kernel on Python Package Index](https://pypi.org/project/semantic-kernel/)
1. [Semantic Kernel on Maven Central](https://central.sonatype.com/search?q=com.microsoft.semantic-kernel)

## Decision Drivers

### Semantic Versioning & Documentation

- We will not adhere to strict [semantic versioning](https://semver.org/) because this is not  strictly followed by NuGet packages.
- We will document trivial incompatible API changes in the release notes
- We expect most regular updates to the Semantic Kernel will include new features and will be backward compatible
 
### Packages Versioning

- We will use the same version number on all packages when we create a new release
- All packages are included in every release and version numbers are incremented even if a specific package has not been changed
- We will test each release to ensure all packages are compatible
- We recommend customers use the same version of packages and this is the configuration we will support

### Major Version

- We will not increment the MAJOR version for low impact incompatible API changes <sup>1</sup>
- We will not increment the MAJOR version for API changes to experimental features or alpha packages
  
<sup>1</sup> Low impact incompatible API changes typically only impact the Semantic Kernel internal implementation or unit tests. We are not expecting to make any significant changes to the API surface of the Semantic Kernel.
  
### Minor Version

- We will increment the MINOR version when we add functionality in a backward compatible manner
  
### Patch Version

- We will increment the PATCH version when by the time of release we only made backward compatible bug fixes.

### Version Suffixes

The following version suffixes are used:

- `preview` or `beta` - This suffix is used for packages which are close to release e.g. version `1.x.x-preview` will be used for a package which is close to it's version 1.x release. Packages will be feature complete and interfaces will be very close to the release version. The `preview` suffix is used with .Net releases and `beta` is used with Python releases.
- `alpha` - This suffix is used for packages which are not feature complete and where the public interfaces are still under development and are expected to change.
