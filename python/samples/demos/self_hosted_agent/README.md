## Self Hosted Agents

This sample demonstrates how to create multi-agent group chat application where agents are hosted outside of the Semantic Kernel. `agents` folder contains `fastapi` server that hosts 2 agents and exposes them via REST apis. `app` folder contains the Semantic Kernel application that orchestrates between the agents using `AgentGroupChat`.

### Running the sample

You will need to deploy Azure OpenAI models in [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-studio/). Keep the endpoint and the key handy.

#### Running the server
1. Navigate to `agents` folder.
2. Create a virtual environment and install the dependencies.
```bash
uv venv --python=3.10
source .venv/bin/activate
```
3. Install the dependencies.
```bash
uv sync
```
4. Create `.env` file using `.env.example` as template.
5. Run the server.
```bash
fastapi run main.py
```

Note the address the fastapi server is running on. You will need it in the next step.

#### Running the app
1. In a different terminal, navigate to `app` folder.
2. Create `.env` file using `.env.example` as template. Replace `server_url` with the address of the fastapi server.
```bash
REVIEWER_AGENT_URL = "<server_url>/agent/reviewer"
COPYWRITER_AGENT_URL = "<server_url>/agent/copywriter"
```
3. Run the app.
```bash
python main.py
```
