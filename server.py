import subprocess
from langchain.tools import tool
 
@tool()
def highligter(x:int , y:int , width:int , height:int) -> str:
    """
    Draws a hollow red highlight box on the user's screen at the specified coordinates.
    Call this tool when the user asks you to locate or point out a specific UI element.
    """
    print(f"\n [ACTION]: Drawing hollow highlight at x={x}, y={y}...")


    real_width, real_height = pyautogui.size() 

    ai_width, ai_height = 1024, 576 

    scale_x = real_width / ai_width
    scale_y = real_height / ai_height

    if match:
        ai_x, ai_y, ai_w, ai_h = map(int, match.groups())
    
        real_x = int(ai_x * scale_x)
        real_y = int(ai_y * scale_y)
        real_w = int(ai_w * scale_x)
        real_h = int(ai_h * scale_y)
    
    
    tk_script = f"""import tkinter as tk

    x, y, w, h, t = {x}, {y}, {width}, {height}, {thickness}

    # Calculate exact coordinates for the 4 edges (Top, Bottom, Left, Right)
    edges = [
    f"{{w}}x{{t}}+{{x}}+{{y}}",                  
    f"{{w}}x{{t}}+{{x}}+{{y + h - t}}",          
    f"{{t}}x{{h}}+{{x}}+{{y}}",                  
    f"{{t}}x{{h}}+{{x + w - t}}+{{y}}"           
]

   root = tk.Tk()
   root.withdraw() # Hide the main window

   # Spawn the 4 border walls
   for geo in edges:
     win = tk.Toplevel(root)
     win.geometry(geo)
     win.overrideredirect(True)
     win.attributes("-topmost", True)
     win.configure(bg="red")

    root.after(3000, root.destroy) 
    root.mainloop()
    """
    script_pth = "/tmp/guideai_highlight.py"
    with open(script_path, "w") as f:
        f.write(tka_script)
        
    subprocess.Popen(["python", script_path])

 


