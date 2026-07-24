import os
import json
import time
from src.redactor import PIIRedactor
from src.docx_processor import DocxRedactor
from src.evaluator import PIIEvaluator


def main():
    print("==================================================")
    print("      PII REDACTION ENGINE & EVALUATION TOOL      ")
    print("==================================================")

    input_file = "Red Herring Prospectus.docx"
    output_file = "Red Herring Prospectus_Redacted.docx"

    if not os.path.exists(input_file):
        print(f"Error: Input document '{input_file}' not found.")
        return

    print(f"\n[1/3] Initializing Hybrid PII Engine...")
    start_time = time.time()
    redactor = PIIRedactor()
    docx_processor = DocxRedactor(redactor=redactor)

    print(f"[2/3] Processing '{input_file}'...")
    results = docx_processor.redact_document(input_file, output_file)
    elapsed_time = round(time.time() - start_time, 2)

    print(f"\n[+] Redaction Complete in {elapsed_time} seconds!")
    print(f"[*] Output Document Saved: {output_file}")
    print(f"[*] Total PII Entities Redacted: {results['total_entities_redacted']}")
    print("\n--- Breakdown by Entity Type ---")
    for ent_type, count in results['stats_by_type'].items():
        print(f"  - {ent_type:<15}: {count}")

    print("\n[3/3] Running Evaluation Benchmark Suite...")
    evaluator = PIIEvaluator(redactor=redactor)
    eval_results = evaluator.evaluate()

    print("\n--- Benchmark Evaluation Summary ---")
    ov = eval_results["overall"]
    print(f"  - Precision: {ov['precision'] * 100:.2f}%")
    print(f"  - Recall   : {ov['recall'] * 100:.2f}%")
    print(f"  - F1 Score : {ov['f1_score'] * 100:.2f}%")
    print(f"  - Accuracy : {ov['accuracy'] * 100:.2f}%")

    print("\n==================================================")


if __name__ == "__main__":
    main()
