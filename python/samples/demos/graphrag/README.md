# Graphrag Sample

## Setup
To setup this demo, make sure you are rooted in this root folder.

Then run `setup-part-0` for the appropriate platform.
This install uv, creates a venv with python 3.12 in .venv, activates the venv, and installs the dependencies.

### Linux
```bash
./setup-part-0-linux.sh
```
### Windows
```powershell
setup-part-0-windows.ps1
```

Next, run `setup-part-1.sh`, this will create the setup directory, downloads a book into it, and then runs the init script, which creates a settings.yaml and .env file.

Next update the .env file with your OpenAI API key as the GRAPHRAG_API_KEY variable, if you want to use Azure OpenAI, then you need to update the settings.yaml accordingly, see the GraphRag docs for more info [here](https://github.com/microsoft/graphrag/blob/main/docs/get_started.md)

Finally, run the `setup-part-2.sh` script, this will run the indexer, this will take a couple of minutes.

Then run `python graphrag_chat.py` to chat with the book, inside that script are some options so feel free to change them to your liking.
