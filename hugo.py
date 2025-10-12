from game_state import GameState
import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from google import generativeai
from google.generativeai.types import GenerationConfig


# --- 1. Definizione dello Schema Pydantic

class Insight(BaseModel):
    key: str = Field(description="The unique key (e.g., 'product_interest').")

    # Campo chiave per i dettagli
    outcome: str = Field(
        description="A rich, detailed string describing the insight based on the conversation.")

    # Questi campi spesso vengono omessi, quindi li rendiamo opzionali
    boolean_outcome: Optional[bool] = Field(
        False,  # Default a False
        description="A concise boolean representation of the outcome: true or false.")

    # Forziamo l'intero (il modello dovrebbe rispettarlo quando ha lo schema)
    confidence: int = Field(
        description="Confidence level (0-5) where 5 is certain.")

    # Forziamo l'intero
    detail: int = Field(
        description="Detail level (0-3) based on how much the topic was discussed.")


BASE_HUGO_PROMPT = """
You have a series of user insights that you need to gather during a conversation between a user and an AI agent.
You can also guess these insights by giving them a low confidence score.
Each insight must be returned as a JSON object with **exactly** these fields:

[
  {{
    "key": "string (the unique key, e.g., 'product_interest')",
    "outcome": "string (a detailed description of the user's intent or insight)",
    "boolean_outcome": "boolean (true or false, default false if not clear)",
    "confidence": "integer (0-5, where 5 = very sure)",
    "detail": "integer (0-3, describing how much the topic was discussed)"
  }}
]

All numeric values must be integers (not floats).
Do not include extra fields such as 'description' or 'insight_name'.

The insights to be collected are:
{questions_formatted}

Reply ONLY with a valid JSON array matching this structure.
"""


def get_gemini_api_key() -> str:
    # L'SDK Gemini di solito cerca GEMINI_API_KEY o GOOGLE_API_KEY
    # Ho lasciato HUGO_API_KEY come hai tu, ma verifica che la variabile sia impostata!
    key = os.getenv("HUGO_API_KEY")
    if not key:
        raise ValueError("HUGO_API_KEY environment variable not set.")
    return key


# --- 4. La Funzione Principale (equivalente di GatherInsights) ---

def gather_insights(history: List[Dict[str, str]], questions_list: str) -> List[Insight]:
    try:
        generativeai.configure(api_key=get_gemini_api_key())
    except ValueError as e:
        print(e)
        return []

    system_prompt_text = BASE_HUGO_PROMPT.format(questions_formatted=questions_list)

    model = generativeai.GenerativeModel(
        model_name="gemini-2.0-flash-lite",  # Manteniamo il tuo modello attuale
        system_instruction=system_prompt_text
    )

    generation_config = GenerationConfig(
        response_mime_type="application/json",
    )
    contents = []
    try:
        contents = [
            {'role': msg['role'], 'parts': [{'text': msg['parts']}]}
            for msg in history
        ]
    except KeyError as e:
        return []

    print("gathering insights...")

    try:
        chat_completion = model.generate_content(
            contents=contents,
            generation_config=generation_config,
        )

        print("got response")

        raw_response_text = chat_completion.text
        if not raw_response_text.strip():
            print("empty or whitespace-only reply received")
            return []

        print("--- DEBUG RAW JSON RESPONSE ---")
        print(raw_response_text)
        print("-------------------------------")
        # ✅ LA CORREZIONE FINALE: Usa json.loads e Insight.model_validate
        raw_insights_list = json.loads(raw_response_text)

        # Convalida e cast a List[Insight]
        insights: List[Insight] = [
            Insight.model_validate(raw_item)
            for raw_item in raw_insights_list
        ]

        return insights  # Restituisce la lista convalidata

    except Exception as e:
        print(f"failed to call Gemini API or parse response: {e}")
        # Aggiungiamo un debug utile
        if 'chat_completion' in locals() and hasattr(chat_completion,
                                                     'candidates') and not chat_completion.candidates:
            print(
                f"Debug Info: La risposta è stata bloccata. Causa: {chat_completion.prompt_feedback.block_reason.name}")
        return []


# --- Esempio di Utilizzo ---

if __name__ == "__main__":
    # --- Dati di Test ---

    # Le 'questions' (insights) che vengono iniettate nel prompt di sistema
    INSIGHT_QUESTIONS = """
    Prodotto di Interesse (product_interest): Quale prodotto sta cercando l'utente.
    Budget Massimo (max_budget): Qual è il budget massimo che l'utente è disposto a spendere.
    Urgenza Acquisto (purchase_urgency): Entro quanto tempo l'utente desidera acquistare.
    Utente Computer (user_pc):L'utente, vuole comprare un computer?
    """

    # Cronologia della conversazione (history)
    CHAT_HISTORY = [
        {"role": "user", "content": "Ciao, stavo cercando un nuovo stereo."},
        {"role": "model",
         "content": "Perfetto! Ha già in mente un modello o una fascia di prezzo?"},
        {"role": "user",
         "content": "Sì, mi servirebbe qualcosa di potente per il lavoro, non vorrei superare i 1500 euro. L'ideale sarebbe averlo entro fine mese."},
    ]

    # Esecuzione
    insights = gather_insights(CHAT_HISTORY, INSIGHT_QUESTIONS)

    print("\n==================================")
    if insights:
        print(f"✅ Trovati {len(insights)} Insights:")
        for i in insights:
            print(f"  - Chiave: {i.key}")
            print(f"    Esito: {i.outcome}")
            print(f"    Confidenza: {i.confidence}/5, Dettaglio: {i.detail}/3")
    else:
        print("❌ Nessun insight raccolto o errore API/parsificazione.")
    print("==================================")