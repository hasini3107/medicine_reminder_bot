# MediAssist LoRA Integration Guide

You have created a script (`train_lora.py`) that successfully outputs a fine-tuned LoRA adapter in PyTorch format. However, Ollama uses the `GGUF` format, so it cannot read the raw PyTorch adapter.

Follow these steps to complete your integration and make your setup perfect.

## Step 1: Run the Training Script
If you haven't already, run your training script to generate the adapter.
```bash
python model/train_lora.py
```
This will create a folder named `lora_adapter/` in your project root containing the PyTorch adapter weights.

## Step 2: Download `llama.cpp`
To convert your PyTorch adapter to GGUF, you need a utility from the `llama.cpp` project.
1. Clone the `llama.cpp` repository into a separate folder on your machine:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   ```
2. Install the required Python dependencies for the conversion scripts:
   ```bash
   pip install -r requirements.txt
   ```

## Step 3: Convert the Adapter to GGUF
Run the `llama.cpp` conversion script, pointing it to your `lora_adapter` folder:
```bash
python convert_lora_to_gguf.py /path/to/your/chatbot_ollama/lora_adapter --outfile /path/to/your/chatbot_ollama/lora_adapter/ggml-adapter-model.gguf
```
*Note: Replace `/path/to/your/chatbot_ollama/` with the actual path to this project folder.*

This will create `ggml-adapter-model.gguf` inside your `lora_adapter/` folder.

## Step 4: Build the Ollama Model
Now that you have the `.gguf` adapter, you can merge it with the base Qwen model using the `Modelfile` that has been added to the root of your project.

Ensure your terminal is inside the `chatbot_ollama/` folder and run:
```bash
ollama create mediassist-finetuned -f Modelfile
```

## Step 5: Test It!
Your `config.py` file has already been updated to point to `MODEL_NAME = "mediassist-finetuned"`. 

Start your Flask server:
```bash
python app.py
```
Your chatbot will now perfectly utilize your custom fine-tuned LoRA model!
