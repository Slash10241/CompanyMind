from __future__ import annotations
import json
import google.generativeai as genai
from backend.config import settings
from backend.gemini_keys import call_with_fallback
from backend.models.schemas import Entity

EXTRACTION_PROMPT = """You are a document entity extractor for an industrial and business knowledge platform. Extract all named entities from the text below.

Entity types to extract:
- EQUIPMENT_TAG: Equipment/asset identifiers (P-101, HE-201, V-301, C-401, T-101)
- PERSON: Named individuals (technicians, engineers, inspectors, employees, customers, contact names)
- DATE: Specific dates or date ranges
- REGULATION: Regulatory standards or codes (OISD-118, PESO, Factory Act, ISO 9001, API 650)
- PARAMETER: Measurements, values, or specifications (pressure 12 bar, temperature 180°C, quantity 12, unit price 14.0, total 440)
- LOCATION: Physical locations (plant areas, cities, countries, addresses, ship regions)
- FAILURE_MODE: Failure descriptions (bearing failure, seal leak, corrosion, vibration, cavitation)
- ORDER_ID: Order, invoice, or document identifiers (Order ID: 10248, Invoice #, PO-2024-001)
- PRODUCT: Product or material names (Queso Cabrales, spare parts, chemicals, raw materials)
- ORGANISATION: Company or organisation names (customer companies, suppliers, shippers, OEMs)

Return a JSON array of objects with fields: "text", "type", "context_snippet" (5-10 words of surrounding context).
Only return the JSON array, nothing else. No markdown, no explanation.

Text:
{text}"""


def extract_entities(text: str) -> list[Entity]:
    """Extract entities from a text chunk using Gemini Flash with key fallback."""
    if len(text.strip()) < 20:
        return []

    def fn(model: genai.GenerativeModel):
        return model.generate_content(
            EXTRACTION_PROMPT.format(text=text[:3000]),
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1024,
            ),
        )

    try:
        response = call_with_fallback(settings.extraction_model, fn)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return [Entity(**item) for item in data if isinstance(item, dict)]
    except Exception:
        return []
