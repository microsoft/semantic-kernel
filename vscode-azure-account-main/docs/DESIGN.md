# Azure Account Extension Design and Architecture

This document provides notes on the design and architecture of the Azure Account extension that may be helpful to maintainers.

> NOTE: This document contains Mermaid-based diagrams. Use the [VS Code Mermaid extension](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) for viewing and editing locally.

## Desktop Authentication Flow

For each authentication event, the extension starts a local HTTP server on a random port (`{port}`) and shares with it a random nonce (`{nonce}`) to ensure only its redirects will be accepted. The extension then asks VS Code to open a browser window and navigate to the local `/signin` endpoint. The extension then redirects the request to the OAuth provider, providing its `/callback` endpoint as the redirection URL. After authentication, the OAuth provider will redirect to the redirection URL and include the server code as a query parameter. Before returning a response, the extension will exchange the server code for access/refresh tokens, using the SDK for the selected OAuth provider. When complete, the extension will redirect the browser its `/` endpoint, which returns a final "you can close this page" HTML page. With that done, the server will be scheduled for shutdown (within 5s).

```mermaid {"id":"01J6KP0PGBBQBWJ15VTPFAJZXT"}
sequenceDiagram
    participant V as VSCode
    participant E as Extension
    participant B as Browser
    participant S as OAuth SDK
    participant P as OAuth Provider

    E->>E: Start server on localhost:{port} with nonce={nonce}
    E->>V: Open browser to http://localhost:{port}/signin?nonce={nonce}
    V->>B: Browse to http://localhost:{port}/signin?nonce={nonce}
    B->>E: GET http://localhost:{port}/signin?nonce={nonce}
    E-->>B: 302 (Redirect) https://{endpoint}/oauth2/authorize?redirect_uri=127.0.0.1:{port}/callback?nonce={nonce}
    B->>P: GET https://{endpoint}/oauth2/authorize?redirect_uri=127.0.0.1:{port}/callback?nonce={nonce}
    B->>B: User enters credentials
    P-->>B: 302 (Redirect) http://127.0.0.1:{port}/callback?nonce={nonce}&code={code}
    B->>E: GET https://127.0.0.1:{port}/callback?nonce={nonce}&code={code}
    Note over E, P: Authentication code acquired so swap for access/refresh tokens.
    E->>S: Get Access/Refresh Tokens
    S->>P: Get Access/Refresh Tokens
    P-->>S: Access/Refresh Tokens
    S-->>E: Access/Refresh Tokens
    Note over E, B: Authentication is complete so redirect to "can close page" page.
    E-->>B: 302 (Redirect) /
    B->>E: GET /
    E-->>B: 200 (OK) {index.html}
    B->>E: GET main.css
    E-->>B: 200 (OK) {main.css}
    E->>E: Stop server on localhost:{port}
```