$ErrorActionPreference = "Stop"

# Run from this folder in PowerShell.
# Install the app dependencies and test-only dependencies once if needed:
#   python -m pip install -r requirements.txt
#   python -m pip install pytest mongomock httpx

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Backend tests failed. Exit code: $LASTEXITCODE"
}
