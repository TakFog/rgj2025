from typing import List

from google import genai
from google.genai import types

class Gemini:
    def __init__(self, model: str):
        self.model = model
        # The client gets the API key from the environment variable `GEMINI_API_KEY`.
        self.aiclient = genai.Client()
        self.system_prompt = None

    def load_prompt(self, step: int):
        with open(f"prompt/{step}.txt", "r", encoding="utf8") as f:
            self.system_prompt = f.read()

    def generate_content(self, contents: List[dict]) -> str:
        response = self.aiclient.models.generate_content(
            model=self.model,
            contents=[types.Content(role=c["role"], parts=[types.Part.from_text(text=c["parts"])]) for c in contents],
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
            ),
        )
        return response.text
