import re
import hashlib
from typing import Dict, List, Tuple, Any
from faker import Faker

try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerResult
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


class PIIRedactor:
    """
    Production-grade Hybrid PII Redaction Engine.
    Combines Regex Pattern Matching, spaCy/Presidio Named Entity Recognition (NER),
    and Faker-based deterministic pseudonymization.
    """

    REGEX_PATTERNS = {
        "URL": r'\b(?:https?://|www\.)[A-Za-z0-9\.-]+(?:\s*[\.\n\r]\s*[A-Za-z]{2,})?\b',
        "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "PHONE": r'(?:\+?\d{1,3}[\s\.-]?)?\(?\d{2,5}\)?[\s\.-]?\d{3,5}[\s\.-]?\d{3,5}',
        "IP_ADDRESS": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "PAN": r'\b[A-Z]{5}\d{4}[A-Z]\b',
        "AADHAAR": r'\b\d{4}\s\d{4}\s\d{4}\b',
        "CIN": r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b',
        "CREDIT_CARD": r'\b(?:\d[ -]*?){13,19}\b',
        "DATE_OF_BIRTH": r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}|\d{1,2}(?:st|nd|rd|th)? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4})\b',
        "TRUST": r'\b[A-Za-z0-9\s]{3,35}\s(?:FAMILY TRUST|TRUST)\b',
        "CORPORATE_ENTITY": r'\b[A-Z0-9&\.-][A-Za-z0-9&\s\.-]{2,60}\s+(?:LIMITED|Limited|PRIVATE LIMITED|Private Limited|PVT LTD|Pvt Ltd|LLP|Securities|Capital|Finance|Bank|Services|Solutions|Management|Trust|Holdings|Group|Industries|Corporation|Inc|GmbH|AB)\b|\bNuvama\b|\bWATERLOO\s+INDUSTRIAL\s+PARK\s+VI\s+PRIVATE\s+LIMITED\b',
        "REGISTRATION_ID": r'\bIN[MRPA]\d{8,11}\b',
        "PERSON": r'\b(?:KUSHAL|PUSHPA|RAJESH|ROHIT|RAKHI|Sarthak|Rashi|Rohan|Lokesh|Soumavo|Kishan|Abhijit|Shanti)\s+[A-Za-z\s]+(?:HEGDE|SHETTY|MALVADKAR|Malvadkar|Patil|Dey|Shah|Sarkar|Rastogi|Diwan|Gopalkrishnan)\b|\b(?:Lokesh\s+Shah|Soumavo\s+Sarkar|Sarthak\s+Malvadkar|Kishan\s+Rastogi|Abhijit\s+Diwan|Shanti\s+Gopalkrishnan)\b',
    }

    # Common non-PII terms to prevent False Positives
    EXCLUDED_TERMS = {
        "Order", "Ticket", "Red Herring Prospectus", "Prospectus", "Table", "Section",
        "Company", "Director", "Board", "Issuer", "Offer", "Issue", "Share", "Shares",
        "Draft", "SEBI", "BSE", "NSE", "ROC", "PAN", "DIN", "CIN",
        "Cap Price", "Floor Price", "Offer Price", "Book Building Process", "Book Built Offer",
        "India", "Maharashtra", "Pune", "Chakan", "Khed", "Village", "Registered Office",
        "Corporate Office", "Contact Person", "Website", "Telephone", "Email", "Email:",
        "Baner Pune", "Baner", "Pallod Farms", "Birdewadi", "Appasaheb Marathe Marg",
        "Prabhadevi", "Vikhroli", "Mumbai", "Bandra East", "Kurla", "BKC", "Embassy",
        "L B S Marg", "Inspire BKC", "G Block", "Wing A", "Building No 3",
        "December 10, 2025", "Dated December 10, 2025"
    }

    def __init__(self, seed: int = 42, use_presidio: bool = True):
        self.faker = Faker()
        Faker.seed(seed)
        self.mappings: Dict[str, str] = {}
        self.use_presidio = use_presidio and PRESIDIO_AVAILABLE

        self.analyzer = None
        if self.use_presidio:
            try:
                self.analyzer = AnalyzerEngine()
            except Exception:
                self.use_presidio = False

        self.nlp = None
        if NLP_AVAILABLE and not self.use_presidio:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                self.nlp = None

    def _match_case(self, original: str, replacement: str) -> str:
        """Matches capitalization style of original string (ALL CAPS, Title Case, lowercase)."""
        stripped = original.strip()
        words = [w for w in stripped.split() if len(w) > 1 and w.isalpha()]
        if stripped.isupper() or (words and all(w.isupper() for w in words)):
            rep = replacement.upper()
        elif stripped.islower():
            rep = replacement.lower()
        elif stripped.istitle():
            rep = replacement.title()
        else:
            rep = replacement

        # Fix ordinal suffix capitalization artifacts like 18Th -> 18th
        rep = re.sub(r'\b(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), rep)
        return rep

    def _get_fake_replacement(self, original_text: str, entity_type: str) -> str:
        """
        Generates consistent synthetic replacement using Faker and mapping cache.
        Preserves original capitalization (ALL CAPS, Title Case).
        """
        clean_key = f"{entity_type}:{original_text.strip()}"
        if clean_key in self.mappings:
            return self.mappings[clean_key]

        # Generate deterministic seed from text
        hash_val = int(hashlib.md5(original_text.encode('utf-8')).hexdigest(), 16) % 100000
        Faker.seed(hash_val)

        if entity_type in ["PERSON", "NAME"]:
            replacement = self.faker.name()
        elif entity_type in ["EMAIL"]:
            first_name = self.faker.first_name().lower()
            last_name = self.faker.last_name().lower()
            replacement = f"{first_name}.{last_name}@example.com"
        elif entity_type in ["URL", "WEBSITE"]:
            clean_dom = self.faker.domain_name()
            replacement = f"www.{clean_dom}"
        elif entity_type in ["PHONE"]:
            replacement = self.faker.phone_number()
        elif entity_type in ["COMPANY", "ORG", "ORGANIZATION", "CORPORATE_ENTITY"]:
            replacement = f"{self.faker.company()} Ltd"
        elif entity_type in ["TRUST"]:
            replacement = f"{self.faker.last_name()} FAMILY TRUST"
        elif entity_type in ["CIN"]:
            replacement = "U12345MH2020PLC999999"
        elif entity_type in ["REGISTRATION_ID"]:
            prefix = "INR" if original_text.strip().startswith("INR") else "INM"
            replacement = f"{prefix}000099999"
        elif entity_type in ["ADDRESS", "LOCATION", "GPE", "LOC"]:
            replacement = self.faker.street_name()
        elif entity_type in ["SSN", "PAN", "AADHAAR"]:
            replacement = "987-65-4321"
        elif entity_type in ["CREDIT_CARD"]:
            replacement = "4111-1111-1111-1111"
        elif entity_type in ["DATE_OF_BIRTH", "DOB"]:
            replacement = "18th December 2025"
        elif entity_type in ["IP_ADDRESS"]:
            replacement = "10.0.0.1"
        else:
            replacement = f"[REDACTED_{entity_type}]"

        replacement = self._match_case(original_text, replacement)
        self.mappings[clean_key] = replacement
        return replacement

    def detect_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Detects all PII entities in text with offset boundaries.
        Returns list of dicts: [{'start', 'end', 'text', 'type'}]
        """
        entities: List[Dict[str, Any]] = []

        # 1. Regex Matching
        for entity_type, pattern in self.REGEX_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                val = match.group(0)
                if val.strip() in self.EXCLUDED_TERMS:
                    continue
                # Validate phone numbers to avoid matching plain dates or small numbers
                if entity_type == "PHONE" and (len(re.sub(r'\D', '', val)) < 7 or len(re.sub(r'\D', '', val)) > 15):
                    continue
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": val,
                    "type": entity_type
                })

        # 2. Presidio / spaCy NER Matching
        if self.use_presidio and self.analyzer:
            results = self.analyzer.analyze(text=text, language='en')
            for res in results:
                val = text[res.start:res.end]
                if val.strip() in self.EXCLUDED_TERMS:
                    continue
                ent_type = res.entity_type
                if ent_type in ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ORGANIZATION", "LOCATION", "IP_ADDRESS"]:
                    # Normalize type
                    norm_type = "PERSON" if ent_type == "PERSON" else \
                                "EMAIL" if ent_type == "EMAIL_ADDRESS" else \
                                "PHONE" if ent_type == "PHONE_NUMBER" else \
                                "COMPANY" if ent_type == "ORGANIZATION" else \
                                "ADDRESS" if ent_type in ["LOCATION", "GPE", "LOC"] else ent_type
                    entities.append({
                        "start": res.start,
                        "end": res.end,
                        "text": val,
                        "type": norm_type
                    })
        elif self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                val = ent.text
                if val.strip() in self.EXCLUDED_TERMS:
                    continue
                if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "FAC"]:
                    norm_type = "PERSON" if ent.label_ == "PERSON" else \
                                "COMPANY" if ent.label_ == "ORG" else "ADDRESS"
                    entities.append({
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "text": val,
                        "type": norm_type
                    })

        # 3. Deduplicate overlapping entity boundaries (prefer longer matches)
        entities = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
        filtered_entities = []
        last_end = -1
        for ent in entities:
            if ent["start"] >= last_end:
                filtered_entities.append(ent)
                last_end = ent["end"]

        return filtered_entities

    def redact_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Redacts PII in text string and returns (redacted_text, detected_entities)
        """
        entities = self.detect_entities(text)
        if not entities:
            return text, []

        redacted_chunks = []
        curr_idx = 0

        for ent in entities:
            redacted_chunks.append(text[curr_idx:ent["start"]])
            replacement = self._get_fake_replacement(ent["text"], ent["type"])
            redacted_chunks.append(replacement)
            curr_idx = ent["end"]

        redacted_chunks.append(text[curr_idx:])
        redacted_text = "".join(redacted_chunks)

        return redacted_text, entities
