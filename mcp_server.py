import subprocess
import pyautogui
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GuideAI_tools")

@mcp.tool()
def highligter(x:int , y:int , width:int , height:int) -> str:
    print("Hightlighting")
    tk_script = f"""
    import tkinter as tk
    root = tk.Tk()
    root.geometry("{width}x{height}+{x}+{y}")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.4) 
    root.configure(bg="red")
    root.after(3000, root.destroy) # Closes automatically after 3 seconds
    root.mainloop()
    """
    path = "/tmp/highlight.py"
    with open(path,"w") as f :
        f.write(tk_script)
    subprocess.Popen(["python",path])

    return "Sucessfully highlighted"

if __name__ == "__main__" :
    print("MCP server is up")
    mcp.run(transport="stdio")


