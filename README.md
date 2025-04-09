# Smart Home Virtual Assistant
 A function calling llm for smarthome by function calling


## Running llama model server
```bash
python -m llama_cpp.server --model .\models\functionary-7b-v2.q8_0.gguf --chat_format functionary-v2 --hf_pretrained_model_name_or_path ./models
```

## Pretrained model
Model path: <a url="https://huggingface.co/meetkai/functionary-7b-v2-GGUF/tree/main">Link</a>

You will need to download all the followings and save them in models:
![img.png](img.png)

For the model, you can change between q4 (4bits), q8 or q16 for examining different performances.