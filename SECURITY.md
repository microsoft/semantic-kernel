---
runme:
  id: 01J0HG23MK8EA26SRB61JJZTCW
  version: v3
---

# Security

```sh {"id":"01J0HG3K604AMB4ENKGM0P421C"}

```

<!-- BEGIN MICROSOFT SECURITY.MD V0.0.8 BLOCK -->

Microsoft takes the security of our software products and services seriously, which includes all source code repositories managed through our GitHub organizations, which include [Microsoft](https://github.com/microsoft), [Azure](https://github.com/Azure), [DotNet](https://github.com/dotnet), [AspNet](https://github.com/aspnet), [Xamarin](https://github.com/xamarin), and [our GitHub organizations](https://opensource.microsoft.com/).

If you believe you have found a security vulnerability in any Microsoft-owned repository that meets [Microsoft's definition of a security vulnerability](https://www.microsoft.com/en-us/msrc/definition-of-a-security-vulnerability?rtc=1), please report it to us as described below.
<!-- BEGIN MICROSOFT SECURITY.MD V0.0.8 BLOCK -->

## Security

Microsoft takes the security of our software products and services seriously, which includes all source code repositories managed through our GitHub organizations, which include [Microsoft](https://github.com/microsoft), [Azure](https://github.com/Azure), [DotNet](https://github.com/dotnet), [AspNet](https://github.com/aspnet), [Xamarin](https://github.com/xamarin), and [our GitHub organizations](https://opensource.microsoft.com/).

If you believe you have found a security vulnerability in any Microsoft-owned repository that meets [Microsoft's definition of a security vulnerability](https://aka.ms/opensource/security/definition), please report it to us as described below.

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them to the Microsoft Security Response Center (MSRC) at [https://msrc.microsoft.com/create-report](https://aka.ms/opensource/security/create-report).

If you prefer to submit without logging in, send email to [secure@microsoft.com](mailto:secure@microsoft.com).  If possible, encrypt your message with our PGP key; please download it from the [Microsoft Security Response Center PGP Key page](https://www.microsoft.com/en-us/msrc/pgp-key-msrc?rtc=2).

You should receive a response within 24 hours. If for some reason you do not, please follow up via email to ensure we received your original message. Additional information can be found at [microsoft.com/msrc](https://www.microsoft.com/en-us/msrc?rtc=2).

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

* Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

If you are reporting for a bug bounty, more complete reports can contribute to a higher bounty award. Please visit our [Microsoft Bug Bounty Program](https://www.microsoft.com/en-us/msrc/bounty?rtc=2) page for more details about our active programs.

If you prefer to submit without logging in, send email to [secure@microsoft.com](mailto:secure@microsoft.com). If possible, encrypt your message with our PGP key; please download it from the [Microsoft Security Response Center PGP Key page](https://aka.ms/opensource/security/pgpkey).

You should receive a response within 24 hours. If for some reason you do not, please follow up via email to ensure we received your original message. Additional information can be found at [microsoft.com/msrc](https://aka.ms/opensource/security/msrc).

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

* Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

If you are reporting for a bug bounty, more complete reports can contribute to a higher bounty award. Please visit our [Microsoft Bug Bounty Program](https://www.microsoft.com/en-us/msrc/bounty?rtc=2) page for more details about our active programs.

## Preferred Languages

We prefer all communications to be in English.

## Policy

Microsoft follows the principle of [Coordinated Vulnerability Disclosure](https://www.microsoft.com/en-us/msrc/cvd?rtc=2).

<!-- END MICROSOFT SECURITY.MD BLOCK -->
Microsoft follows the principle of [Coordinated Vulnerability Disclosure](https://aka.ms/opensource/security/cvd).
<!-- END MICROSOFT SECURITY.MD BLOCK -->

## Security Policies and Best Practices

To ensure the security of our project, we have implemented the following security policies and best practices:

### Secure Coding Guidelines

* Follow secure coding practices to prevent common vulnerabilities such as SQL injection, cross-site scripting (XSS), and buffer overflows.
* Validate and sanitize all user inputs to prevent injection attacks.
* Use parameterized queries or prepared statements for database interactions.
* Avoid using hard-coded credentials or sensitive information in the codebase.
* Implement proper error handling and logging to avoid exposing sensitive information.

### Regular Security Reviews

* Conduct regular security reviews of the codebase to identify and address potential vulnerabilities.
* Perform code reviews to ensure adherence to secure coding practices.
* Use automated security scanning tools to detect vulnerabilities in the code and dependencies.
* Stay updated with the latest security patches and updates for all dependencies and libraries used in the project.

### Mandatory Security Training

* Ensure that all developers and contributors undergo mandatory security training.
* Provide training on secure coding practices, common vulnerabilities, and how to mitigate them.
* Encourage developers to stay informed about the latest security trends and best practices.

## Monitoring and Responding to Security Alerts

We have established a process for monitoring and responding to security alerts generated by our automated security tools. This process includes:

* Regularly monitoring security alerts from tools such as CodeQL, Dependabot, and Frogbot.
* Triaging and prioritizing security alerts based on their severity and potential impact.
* Assigning responsible team members to investigate and address security alerts promptly.
* Implementing fixes for identified vulnerabilities and ensuring they are thoroughly tested before deployment.
* Communicating with the community and stakeholders about any security incidents and the steps taken to address them.
