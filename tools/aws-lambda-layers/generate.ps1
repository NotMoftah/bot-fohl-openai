# Ensure the python folder is empty
if (Test-Path -Path "layer/python") {
    Get-ChildItem -Path "layer/python" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Install the required packages into the python folder
pip install -r requirements.txt --target layer/python --platform manylinux2014_x86_64 --implementation cp --python-version 3.13 --only-binary=:all: --upgrade

# Ensure the existing zip file is deleted before creating a new one
if (Test-Path -Path "lambda_layer.zip") {
    Remove-Item -Path "lambda_layer.zip" -Force -ErrorAction SilentlyContinue
}

# Zip the lambda layer
Compress-Archive -Path layer/* -DestinationPath lambda_layer.zip