from google import genai

class Gemini:
    def __init__(self, model: str):
        self.model = model
        # The client gets the API key from the environment variable `GEMINI_API_KEY`.
        self.aiclient = genai.Client()

    def generate_content(self, contents: str) -> str:
        response = self.aiclient.models.generate_content(
            model=self.model, contents=contents
        )
        return response.text
