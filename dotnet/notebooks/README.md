# Semantic Kernel C# Notebooks

The current folder contains a few C# Jupyter Notebooks that demonstrate how to get started with
the Semantic Kernel. The notebooks are organized in order of increasing complexity.

To run the notebooks, we recommend the following steps:

- [Install .NET 8](https://dotnet.microsoft.com/download/dotnet/7.0)
- [Install Visual Studio Code (VS Code)](https://code.visualstudio.com)
- Launch VS Code and [install the "Polyglot" extension](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.dotnet-interactive-vscode).
  Min version required: v1.0.4606021 (Dec 2023).

The steps above should be sufficient, you can now **open all the C# notebooks in VS Code**.

VS Code screenshot example:

![image](https://user-images.githubusercontent.com/371009/216761942-1861635c-b4b7-4059-8ecf-590d93fe6300.png)

## Set your OpenAI API key

To start using these notebooks, be sure to add the appropriate API keys to `config/settings.json`.

You can create the file manually or run [the Setup notebook](0-AI-settings.ipynb).

For Azure OpenAI:

```json
{
  "type": "azure",
  "model": "...", // Azure OpenAI Deployment Name
  "endpoint": "...", // Azure OpenAI endpoint
  "apikey": "..." // Azure OpenAI key
}
```

For OpenAI:

```json
{
  "type": "openai",
  "model": "gpt-3.5-turbo", // OpenAI model name
  "apikey": "...", // OpenAI API Key
  "org": "" // only for OpenAI accounts with multiple orgs
}
```

If you need an Azure OpenAI key, go [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?pivots=rest-api).
If you need an OpenAI key, go [here](https://platform.openai.com/account/api-keys)

# Topics

Before starting, make sure you configured `config/settings.json`,
see the previous section.

For a quick dive, look at the [getting started notebook](00-getting-started.ipynb).

1. [Loading and configuring Semantic Kernel](01-basic-loading-the-kernel.ipynb)
2. [Running AI prompts from file](02-running-prompts-from-file.ipynb)
3. [Creating Semantic Functions at runtime (i.e. inline functions)](03-semantic-function-inline.ipynb)
4. [Using Kernel Arguments to Build a Chat Experience](04-kernel-arguments-chat.ipynb)
5. [Creating and Executing Plans](05-using-the-planner.ipynb)
6. [Building Memory with Embeddings](06-memory-and-embeddings.ipynb)
7. [Creating images with DALL-E 2](07-DALL-E-2.ipynb)
8. [Chatting with ChatGPT and Images](08-chatGPT-with-DALL-E-2.ipynb)
9. [Building Semantic Memory with Chroma](09-memory-with-chroma.ipynb)
10. [BingSearch using Kernel](10-BingSearch-using-kernel.ipynb)

# Run notebooks in the browser with JupyterLab

You can run the notebooks also in the browser with JupyterLab. These steps
should be sufficient to start:

Install Python 3, Pip and .NET 7 in your system, then:

    pip install jupyterlab
    dotnet tool install -g Microsoft.dotnet-interactive
    dotnet tool update -g Microsoft.dotnet-interactive
    dotnet interactive jupyter install

This command will confirm that Jupyter now supports C# notebooks:

    jupyter kernelspec list

Enter the notebooks folder, and run this to launch the browser interface:

    jupyter-lab

![image](https://user-images.githubusercontent.com/371009/216756924-41657aa0-5574-4bc9-9bdb-ead3db7bf93a.png)

# Troubleshooting

## Nuget

If you are unable to get the Nuget package, first list your Nuget sources:

```sh
dotnet nuget list source
```

If you see `No sources found.`, add the NuGet official package source:

```sh
dotnet nuget add source "https://api.nuget.org/v3/index.json" --name "nuget.org"
```

Run `dotnet nuget list source` again to verify the source was added.

## Polyglot Notebooks

If somehow the notebooks don't work, run these commands:

- Install .NET Interactive: `dotnet tool install -g Microsoft.dotnet-interactive`
- Register .NET kernels into Jupyter: `dotnet interactive jupyter install` (this might return some errors, ignore them)
- If you are still stuck, read the following pages:
  - https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.dotnet-interactive-vscode
  - https://devblogs.microsoft.com/dotnet/net-core-with-juypter-notebooks-is-here-preview-1/
  - https://docs.servicestack.net/jupyter-notebooks-csharp
  - https://developers.refinitiv.com/en/article-catalog/article/using--net-core-in-jupyter-notebook

Note: ["Polyglot Notebooks" used to be called ".NET Interactive Notebooks"](https://devblogs.microsoft.com/dotnet/dotnet-interactive-notebooks-is-now-polyglot-notebooks/),
so you might find online some documentation referencing the old name.
