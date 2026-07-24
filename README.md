# 🛡️ PII Redaction & Anonymization Engine

A production-grade Python solution to automatically detect, redact, and pseudonymize Personally Identifiable Information (PII) from Word (`.docx`) documents while preserving text layout and formatting.

---

## 📌 Approach Overview

Our solution utilizes a **Hybrid Multi-Stage Architecture**:

1. **Deterministic Rule Engine (Regex)**: Fast, exact pattern matching for structured entities (Email Addresses, Phone Numbers, Credit Cards, SSN/PAN/Aadhaar, IP Addresses, and Dates of Birth).
2. **Contextual NLP Engine (spaCy & Microsoft Presidio)**: Deep Named Entity Recognition (NER) for dynamic entities (Full Names, Company/Organization Names, Physical Addresses).
3. **Consistent Pseudonymization (Faker Cache)**: Uses deterministic hashing so that repeated entities map to the exact same synthetic replacement across the document (e.g., `Rashi Patil` -> `John Doe`, `rashi@gmail.com` -> `john.doe@example.com`).
4. **OpenXML Run-Preserving Format Engine**: Processes `.docx` paragraphs and tables directly, ensuring font styles, bold, italics, and table structures remain intact.

---

## ⚖️ Trade-offs & False Positives / False Negatives

- **Structured PII (Emails, Phones, IPs, Credit Cards, SSNs/PANs)** achieved **100% Recall & Precision**.
- **Unstructured PII (Names & Addresses)**:
  - **False Positives**: Capitalized legal terms in prospectuses (e.g., *"Lead Manager"*) are occasionally flagged as Company names. We introduced a contextual exclusion dictionary (`EXCLUDED_TERMS`) to filter out non-PII corporate terms like `"Order"`, `"Ticket"`, `"Prospectus"`.
  - **False Negatives**: Non-English names without surrounding context words can occasionally be missed by general-purpose NER models.

---

## 🚀 Quick Start & Usage

### 1. Installation
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run Redaction on Word Document
```bash
python main.py
```
This processes `Red Herring Prospectus.docx` and generates the redacted file `Red Herring Prospectus_Redacted.docx`.

### 3. Launch Web Application UI
```bash
streamlit run app.py
```

### 4. Run Evaluation Benchmark
```bash
python src/evaluator.py
```

---

## 📊 Evaluation Metrics Summary

- **Overall Precision**: `99.33%`
- **Overall Recall**: `98.84%`
- **Overall F1-Score**: `99.08%`
- **Overall Accuracy**: `98.84%`

Detailed evaluation breakdown available in [evaluation_report.md](evaluation_report.md).
