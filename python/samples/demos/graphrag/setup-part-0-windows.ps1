powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

uv venv --python 3.12

.venv\Scripts\activate

uv pip install -r requirements.txt

