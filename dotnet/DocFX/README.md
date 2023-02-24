# DocFX

DocFX converts .NET assembly, XML code comment, REST API Swagger files and markdown into rendered
HTML pages, JSON model or PDF files.

## Links

- [docfx](https://dotnet.github.io/docfx/index.html)

## Setup

- Install [.NET 6 SDK](https://dotnet.microsoft.com/en-us/download) or higher.

2. Install DocFX

```bash
dotnet tool install -g docfx
```

## Running locally

To preview the documentation website on your local machine, run `docfx` and point it to the
`docfx.json` file in the `dotnet\DocFX` folder.

From the root of the repo, run:

```bash
docfx dotnet\DocFX\docfx.json --serve
```