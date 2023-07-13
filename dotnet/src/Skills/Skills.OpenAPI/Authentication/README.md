# Authentication for the OpenAPI Skill

The Semantic Kernel OpenAPI Skill enables developers to take any REST API that follows the OpenAPI specification and import it as a skill to the Semantic Kernel. However, the Kernel needs to be able to authenticate outgoing requests per the requirements of the target API. This document outlines the authentication model for the OpenAPI skill as well as the reference implementations provided by the Semantic Kernel.

## The `AuthenticateRequestAsyncCallback` delegate

[`AuthenticateRequestAsyncCallback`](AuthenticateRequestAsyncCallback.cs) is a delegate type that serves as a callback function for adding authentication information to HTTP requests sent by the OpenAPI skill.

```csharp
public delegate Task AuthenticateRequestAsyncCallback(HttpRequestMessage request);
```

Developers may optionally provide an implementation of this delegate when importing an OpenAPI skill to the Kernel. The delegate is then passed through to the `RestApiOperationRunner`, which is responsible for building the HTTP payload and sending the request for each REST API operation. Before the API request is sent, the delegate is executed with the HTTP request message as the parameter, allowing the request message to be updated with any necessary authentication information.

This pattern was designed to be flexible enough to support a wide variety of authentication frameworks. Developers can provide the delegate function directly or define a class or interface that exposes one or more implementations. They have the option of writing their own custom implementation or using one of the Semantic Kernel's reference authentication providers as a starting point.

## Reference Authentication Providers

### [`BasicAuthenticationProvider`](./BasicAuthenticationProvider.cs)
This class implements the HTTP "basic" authentication scheme. The constructor accepts a `Func` which defines how to retrieve the user's credentials. When the `AuthenticateRequestAsync` method is called, it retrieves the credentials, encodes them as a UTF-8 encoded Base64 string, and adds them to the `HttpRequestMessage`'s authorization header.

The following code demonstrates how to use this provider:
```csharp
var basicAuthProvider = new BasicAuthenticationProvider(() =>
{
    // JIRA API expects credentials in the format "email:apikey"
    return Task.FromResult(
        Env.Var("MY_EMAIL_ADDRESS") + ":" + Env.Var("JIRA_API_KEY")
    );
});
var skill = kernel.ImportOpenApiSkillFromResource(SkillResourceNames.Jira, new OpenApiSkillExecutionParameters { AuthCallback = basicAuthProvider.AuthenticateRequestAsync } );
```

### [`BearerAuthenticationProvider`](./BearerAuthenticationProvider.cs)
This class implements the HTTP "bearer" authentication scheme. The constructor accepts a `Func` which defines how to retrieve the bearer token. When the `AuthenticateRequestAsync` method is called, it retrieves the token and adds it to the `HttpRequestMessage`'s authorization header. 

The following code demonstrates how to use this provider:
```csharp
var bearerAuthProvider = new BearerAuthenticationProvider(() =>
{
    return Task.FromResult(Env.Var("AZURE_KEYVAULT_TOKEN"));
});
var skill = kernel.ImportOpenApiSkillFromResource(SkillResourceNames.AzureKeyVault, new OpenApiSkillExecutionParameters { AuthCallback =  bearerAuthProvider.AuthenticateRequestAsync } )
```

### [`InteractiveMsalAuthenticationProvider`](./InteractiveMsalAuthenticationProvider.cs)

This class uses the [Microsoft Authentication Library (MSAL)](https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-overview)'s .NET library to authenticate the user and acquire an OAuth token. It follows the interactive [authorization code flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow), requiring the user to sign in with a Microsoft or Azure identity. This is particularly useful for authenticating requests to the Microsoft Graph or Azure APIs.

Once the token is acquired, it is added to the HTTP authentication header via the `AuthenticateRequestAsync` method, which is inherited from `BearerAuthenticationProvider`.

To construct this provider, the caller must specify:
- *Client ID* – identifier of the calling application. This is acquired by [registering your application with the Microsoft Identity platform](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).
- *Tenant ID* – identifier of the target service tenant, or “common”
- *Scopes* – permissions being requested
- *Redirect URI* – for redirecting the user back to the application. (When running locally, this is typically  http://localhost.)

```csharp
var msalAuthProvider = new InteractiveMsalAuthenticationProvider(
    Env.Var("AZURE_KEYVAULT_CLIENTID"), // clientId
    Env.Var("AZURE_KEYVAULT_TENANTID"), // tenantId
    new string[] { ".default" },        // scopes
    new Uri("http://localhost")         // redirectUri
);
var skill = kernel.ImportOpenApiSkillFromResource(SkillResourceNames.AzureKeyVault, new OpenApiSkillExecutionParameters { AuthCallback =  msalAuthProvider.AuthenticateRequestAsync } )
```