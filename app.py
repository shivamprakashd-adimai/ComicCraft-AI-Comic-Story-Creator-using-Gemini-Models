import os
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
import google.generativeai as genai
from fpdf import FPDF

app = FastAPI(title="ComicCraft - AI Comic Creator")

# Gemini API Key அமைத்தல் (இலவச API Key பெற: https://aistudio.google.com/)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=GEMINI_API_KEY)

class ComicPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'ComicCraft - AI Generated Comic', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_comic_story(prompt, character, setting, tone, art_style):
    try:
        model_flash = genai.GenerativeModel('gemini-1.5-flash')
        system_prompt = f"""
        You are a comic writer. Create a 4-panel comic script for:
        Character: {character}, Setting: {setting}, Tone: {tone}, Art Style: {art_style}, Story Prompt: {prompt}.
        Return strict JSON array of 4 panels with keys "panel_number", "scene_description", "dialogue".
        """
        response = model_flash.generate_content(
            system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        # API Key அமைக்காவிட்டாலும் டெமோ காண்பிக்க மாதிரி கதை
        return [
            {"panel_number": 1, "scene_description": f"{character} arrives at {setting}.", "dialogue": f"{character}: Wow, this place looks amazing!"},
            {"panel_number": 2, "scene_description": f"A strange mystery appears in {setting}.", "dialogue": f"{character}: What could this be?"},
            {"panel_number": 3, "scene_description": f"An adventurous {tone} moment occurs.", "dialogue": f"{character}: I must solve this mystery!"},
            {"panel_number": 4, "scene_description": f"Conclusion of the {art_style} style comic story.", "dialogue": f"{character}: That was an epic journey!"}
        ]

def build_pdf(title, panels, filename="comic_output.pdf"):
    pdf = ComicPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, f"Title: {title}", ln=True)
    pdf.ln(5)

    for panel in panels:
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, f"Panel {panel.get('panel_number', '')}", ln=True)
        pdf.set_font("Helvetica", '', 10)
        pdf.multi_cell(0, 6, f"Scene: {panel.get('scene_description', '')}")
        pdf.set_font("Helvetica", 'I', 10)
        pdf.multi_cell(0, 6, f"Dialogue: {panel.get('dialogue', '')}")
        pdf.ln(5)

    pdf.output(filename)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ComicCraft - AI Comic Story Creator</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 750px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { font-weight: bold; display: block; margin-bottom: 5px; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
        button { background-color: #3498db; color: white; padding: 12px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }
        button:hover { background-color: #2980b9; }
        .panel-card { background: #f8f9fa; border-left: 5px solid #3498db; padding: 15px; margin-top: 15px; border-radius: 4px; }
        .download-btn { background-color: #2ecc71; margin-top: 20px; display: block; text-align: center; text-decoration: none; padding: 12px; color: white; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 ComicCraft - AI Comic Creator</h1>
        <form action="/generate" method="post">
            <div class="form-group">
                <label>Story Prompt:</label>
                <textarea name="prompt" rows="3" required placeholder="A brave fox exploring an enchanted forest"></textarea>
            </div>
            <div class="form-group">
                <label>Main Character Name:</label>
                <input type="text" name="character" value="Felix" required>
            </div>
            <div class="form-group">
                <label>Setting:</label>
                <input type="text" name="setting" value="Enchanted Forest" required>
            </div>
            <div class="form-group">
                <label>Story Tone:</label>
                <select name="tone">
                    <option value="Dramatic">Dramatic</option>
                    <option value="Funny">Funny</option>
                    <option value="Adventurous">Adventurous</option>
                </select>
            </div>
            <div class="form-group">
                <label>Art Style:</label>
                <select name="art_style">
                    <option value="Anime">Anime</option>
                    <option value="Classic Comic Book">Classic Comic Book</option>
                    <option value="Watercolor">Watercolor</option>
                </select>
            </div>
            <button type="submit">🚀 Generate Comic Story</button>
        </form>

        {% if panels %}
        <hr style="margin-top:30px;">
        <h2>📖 Generated Comic Panels</h2>
        {% for panel in panels %}
        <div class="panel-card">
            <h3>Panel {{ panel.panel_number }}</h3>
            <p><strong>Scene:</strong> {{ panel.scene_description }}</p>
            <p><strong>Dialogue:</strong> <em>{{ panel.dialogue }}</em></p>
        </div>
        {% endfor %}
        <a href="/download" class="download-btn">📥 Download Comic PDF</a>
        {% endif %}
    </div>
</body>
</html>
"""

current_panels = []
current_title = "Comic Story"

@app.get("/", response_class=HTMLResponse)
async def index():
    from jinja2 import Template
    return Template(HTML_TEMPLATE).render(panels=None)

@app.post("/generate", response_class=HTMLResponse)
async def generate(
    prompt: str = Form(...),
    character: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):
    global current_panels, current_title
    current_title = f"{character}'s {tone} Story"
    current_panels = generate_comic_story(prompt, character, setting, tone, art_style)
    build_pdf(current_title, current_panels)
    
    from jinja2 import Template
    return Template(HTML_TEMPLATE).render(panels=current_panels)

@app.get("/download")
async def download():
    return FileResponse("comic_output.pdf", filename="ComicCraft_Story.pdf", media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)