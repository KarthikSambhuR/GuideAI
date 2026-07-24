import numpy as np
import sounddevice as sd
from pywhispercpp.model import Model
import base64
from io import BytesIO
import pyautogui
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from server import highligter
import pyautogui
import re
 

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
    image.thumbnail((1024, 576))
    buffer = BytesIO()
    image.save(buffer,format="JPEG",quality=50)
    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    print("B64 encoded")
    return img_b64  

def input_audio():
    try :
        while True:
            command = rec_audio()
            print("Transcribed :",command)
            if input("Are you satisfied with the audio (y/n):") == 'y':
                return command
    except Exception as e:
        print(e)
    

if __name__ == "__main__" : 
    print("Connecting to the VL Model")
    vlm = ChatOpenAI(
        model="qwen2.5vl:3b",  
        api_key="lm-studio",      
        base_url="http://127.0.0.1:1234/v1",
        temperature=0.0 
    )

    print("The lang graph agent is set up")

    ai_width, ai_height = 1024, 576 

    while True:
        command = 'Where is the application exit button of the current application.'
        img = screenshot()
        message = HumanMessage(
             content=[
                {"type": "text", "text": f"""You are a precise computer vision UI locator.
                The user requested to find: '{command}'.

                CONTEXT:
                - You are looking at a computer screen scaled to {ai_width}x{ai_height} pixels.
                - The origin (0,0) is the top-left corner.

                EXAMPLE OUTPUT:
                ```json
                {{
                    "bbox_2d": {{
                    "left": 150,
                    "top": 45,
                    "width": 200,
                    "height": 30
                    }}
                }}
                ```
                CRITICAL INSTRUCTION:
                Reply ONLY with the structured JSON bounding box coordinates. Do not write any other text."""},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                ]
            )
        try:
         print("🧠 Qwen is analyzing the screen...")
         result = vlm.invoke([message])
         final_text = result.content
         print(f"GuideAI Output: {final_text}\n")

         # Hunt for the JSON block in the text
         json_match = re.search(r'\{.*\}', final_text, re.DOTALL)
         
         if json_match:
             data = json.loads(json_match.group(0))
             if "bbox_2d" in data:
                 bbox = data["bbox_2d"]
                 ai_x = int(bbox["left"])
                 ai_y = int(bbox["top"])
                 ai_w = int(bbox["width"])
                 ai_h = int(bbox["height"])
                 
                 print("🎯 Coordinates found! Firing tool...")
                 
                 # Fire the tool manually using the parsed data
                 highligter.invoke({"x": ai_x, "y": ai_y, "width": ai_w, "height": ai_h})
             else:
                 print("⚠️ JSON found, but 'bbox_2d' was missing.")
         else:
             print("⚠️ No JSON found in response.")
             
         if input("\nAll good ? (y/n): ").strip().lower() == 'y':
            break
             
        except Exception as e:
            print(f"\n❌ ERROR: {e}\n")
        