import json
import os
import sys
from typing import Dict, List, Any

# Ensure project root is in sys.path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.redactor import PIIRedactor
except ModuleNotFoundError:
    from redactor import PIIRedactor


DEFAULT_EVALUATION_DATASET = [
    {
        "id": 1,
        "text": "Rashi Patil submitted ticket #402 from rashi.patil@gmail.com on 15th August 1990.",
        "ground_truth": [
            {"text": "Rashi Patil", "type": "PERSON"},
            {"text": "rashi.patil@gmail.com", "type": "EMAIL"},
            {"text": "15th August 1990", "type": "DATE_OF_BIRTH"}
        ]
    },
    {
        "id": 2,
        "text": "Contact Rohan Dey at rohan.dey@gmail.com or call +91 9876543210 for Acme Corp India Pvt Ltd.",
        "ground_truth": [
            {"text": "Rohan Dey", "type": "PERSON"},
            {"text": "rohan.dey@gmail.com", "type": "EMAIL"},
            {"text": "+91 9876543210", "type": "PHONE"},
            {"text": "Acme Corp India Pvt Ltd", "type": "COMPANY"}
        ]
    },
    {
        "id": 3,
        "text": "Send physical mail to 123 MG Road, Bengaluru, KA. Server IP address is 192.168.1.50.",
        "ground_truth": [
            {"text": "123 MG Road, Bengaluru, KA", "type": "ADDRESS"},
            {"text": "192.168.1.50", "type": "IP_ADDRESS"}
        ]
    },
    {
        "id": 4,
        "text": "Tax identification PAN is ABCDE1234F and SSN is 123-45-6789. Card: 4532-1123-4567-8901.",
        "ground_truth": [
            {"text": "ABCDE1234F", "type": "PAN"},
            {"text": "123-45-6789", "type": "SSN"},
            {"text": "4532-1123-4567-8901", "type": "CREDIT_CARD"}
        ]
    },
    {
        "id": 5,
        "text": "Ticket #9843 and Order #1002 are not sensitive, but John Doe born on 1995-01-01 is.",
        "ground_truth": [
            {"text": "John Doe", "type": "PERSON"},
            {"text": "1995-01-01", "type": "DATE_OF_BIRTH"}
        ]
    }
]


class PIIEvaluator:
    """
    Evaluation benchmarking suite for calculating Precision, Recall, F1-Score,
    and Accuracy across all PII entity types.
    """

    def __init__(self, redactor: PIIRedactor = None):
        self.redactor = redactor or PIIRedactor()

    def evaluate(self, dataset: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if dataset is None:
            dataset = DEFAULT_EVALUATION_DATASET

        metrics_by_type: Dict[str, Dict[str, int]] = {}
        all_types = ["PERSON", "EMAIL", "PHONE", "COMPANY", "ADDRESS", "SSN", "PAN", "CREDIT_CARD", "DATE_OF_BIRTH", "IP_ADDRESS"]

        for t in all_types:
            metrics_by_type[t] = {"TP": 0, "FP": 0, "FN": 0}

        total_samples = len(dataset)
        total_tokens_evaluated = 0

        for sample in dataset:
            text = sample["text"]
            ground_truth = sample["ground_truth"]
            gt_texts = {gt["text"].strip().lower(): gt["type"] for gt in ground_truth}

            detected = self.redactor.detect_entities(text)
            detected_texts = {d["text"].strip().lower(): d["type"] for d in detected}

            # Calculate TPs, FPs, FNs
            for dt_text, dt_type in detected_texts.items():
                if dt_text in gt_texts:
                    metrics_by_type[dt_type]["TP"] += 1
                else:
                    if dt_type not in metrics_by_type:
                        metrics_by_type[dt_type] = {"TP": 0, "FP": 0, "FN": 0}
                    metrics_by_type[dt_type]["FP"] += 1

            for gt_text, gt_type in gt_texts.items():
                if gt_text not in detected_texts:
                    if gt_type not in metrics_by_type:
                        metrics_by_type[gt_type] = {"TP": 0, "FP": 0, "FN": 0}
                    metrics_by_type[gt_type]["FN"] += 1

        # Calculate Overall Metrics
        summary: Dict[str, Any] = {}
        total_tp = sum(m["TP"] for m in metrics_by_type.values())
        total_fp = sum(m["FP"] for m in metrics_by_type.values())
        total_fn = sum(m["FN"] for m in metrics_by_type.values())

        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
        overall_f1 = (2 * overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
        overall_accuracy = total_tp / (total_tp + total_fp + total_fn) if (total_tp + total_fp + total_fn) > 0 else 1.0

        per_type_report = {}
        for ent_type, counts in metrics_by_type.items():
            tp, fp, fn = counts["TP"], counts["FP"], counts["FN"]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            per_type_report[ent_type] = {
                "TP": tp, "FP": fp, "FN": fn,
                "Precision": round(prec, 4),
                "Recall": round(rec, 4),
                "F1_Score": round(f1, 4)
            }

        return {
            "overall": {
                "precision": round(overall_precision, 4),
                "recall": round(overall_recall, 4),
                "f1_score": round(overall_f1, 4),
                "accuracy": round(overall_accuracy, 4),
                "total_tp": total_tp,
                "total_fp": total_fp,
                "total_fn": total_fn
            },
            "per_entity_type": per_type_report
        }


if __name__ == "__main__":
    evaluator = PIIEvaluator()
    results = evaluator.evaluate()
    print(json.dumps(results, indent=2))
