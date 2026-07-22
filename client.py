import numpy as np
import sounddevice as sd
from pywhispercpp.model import Model
import base64
from io import BytesIO
import pyautogui
 

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
        img_b64 = base64.b64encode(buffer   .getvalue().decode('utf-8'))
        print("B64 encoded")
        return img_b64

if __name__ == "__main__" : 
    while True:
        text = rec_audio()
        print(f"Transcribed : {text}")

        if input("\nTry again? (y/n): ").lower() != 'y':
             print ("BYeeee")
             break
