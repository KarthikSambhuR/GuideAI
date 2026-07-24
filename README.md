# GuideAI

GuideAI is a local voice-guided desktop assistant. It uses push-to-talk speech recognition, local llama.cpp vision inference, and a lightweight on-screen annotation overlay.

## Getting started

Install the Python dependencies and run the application:

```powershell
pip install -r requirements.txt
python app.py
```

GuideAI starts the bundled llama.cpp server automatically. It uses the Gemma GGUF configured in `config.py` and `mmproj-BF16.gguf` in this project folder to send a desktop screenshot alongside each question.

## Contributors

- joyelshajii
- EbenAbrahamChandy
- erenjoseph
- melizabyiju
