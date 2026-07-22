import numpy as np
import sounddevice as sd
from pywhispercpp.model import Model
import base64
from io import BytesIO
import pyautogui
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
 

print("Loading the whisper model...")
stt_model = Model("base.en", print_realtime=False, print_progress=False)
def rec_audio(duration_max=10,sample_rate=16000) -> str :
    input("Press Enter")
    print("RECORDING\n")
    audio = sd.rec(
        int(duration_max * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'   
    )
    sd.wait()
    sd.stop()
    audio_array = np.squeeze(audio)
    audio_array = np.nan_to_num(audio_array, nan=0.0, posinf=1.0, neginf=-1.0)

    max_val = np.max(np.abs(audio_array))
    if max_val > 0:
        audio_array = audio_array / max_val
    segments = stt_model.transcribe(audio_array)
    return " ".join([segment.text for segment in segments]).strip()

def screenshot():
    image = pyautogui.screenshot()
    print("Screenshot Secured")
    buffer = BytesIO()
    image.save(buffer,format="JPEG",quality=80)
    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    print("B64 encoded")
    return img_b64  

def input_audio():
    try :
        while True:
            command = rec_audio()
            print("Transcribed :",command)
            if input("Are you satisfied with the audio (y/n) : ") == 'y':
                return command
    except Exception as e:
        print(e)
    

if __name__ == "__main__" : 
    print("Connecting to the VL Model")
    vlm = ChatOpenAI(
        model="qwen2.5vl:3b",  
        api_key="ollama",      
        base_url="http://localhost:11434/v1" 
    )
    tools = []
    agent = create_agent(vlm,tools)

    print("The langgraph agent is set up")

    while True:
        text = input_audio()
        img = screenshot()
        message = HumanMessage(
            content = [
                {"type": "text", "text": f"Look at this screenshot. The user asked: {text}. Describe what you see that matches their request."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
            ]
        )
        for event in agent.stream({"messages": [message]}):
            for key, value in event.items():
                if key == "agent":
                    print(f"\n🤖 GuideAI: {value['messages'][-1].content}\n")
        
        if input("Try another command? (y/n): ").lower() != 'y':
            break
            
        