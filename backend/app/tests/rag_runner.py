import json
import os
import argparse
from datetime import datetime

# python -m app.tests.rag_runner --case app/tests/rag_cases/little_prince.json
from app.services.rag_chat import ask_question


def load_case(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, help="Path to JSON case file")
    parser.add_argument("--output", default="app/tests/outputs", help="Output folder")
    args = parser.parse_args()

    case = load_case(args.case)
    questions = case["questions"]
    project_id = case.get("project_id")
    case_name = case.get("name", "rag_test")

    ensure_dir(args.output)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_txt = os.path.join(args.output, f"{case_name}_{timestamp}.txt")
    out_json = os.path.join(args.output, f"{case_name}_{timestamp}.json")

    results = []

    with open(out_txt, "w", encoding="utf-8") as txt_file:
        txt_file.write(f"CASE: {case_name}\n")
        txt_file.write(f"PROJECT_ID: {project_id}\n\n")

        for i, question in enumerate(questions, start=1):
            try:
                response = ask_question(project_id=project_id, question=question)

                # нагоди това според твоя return shape
                answer = response["answer"] if isinstance(response, dict) else str(response)

                results.append({
                    "index": i,
                    "question": question,
                    "answer": answer,
                    "status": "ok"
                })

                txt_file.write(f"[{i}] QUESTION:\n{question}\n")
                txt_file.write(f"[{i}] ANSWER:\n{answer}\n")
                txt_file.write("\n" + "-" * 80 + "\n\n")

                print(f"[OK] {i}/{len(questions)} {question}")

            except Exception as e:
                results.append({
                    "index": i,
                    "question": question,
                    "answer": None,
                    "status": "error",
                    "error": str(e)
                })

                txt_file.write(f"[{i}] QUESTION:\n{question}\n")
                txt_file.write(f"[{i}] ERROR:\n{e}\n")
                txt_file.write("\n" + "-" * 80 + "\n\n")

                print(f"[ERROR] {i}/{len(questions)} {question} -> {e}")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "case_name": case_name,
            "project_id": project_id,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\nSaved TXT: {out_txt}")
    print(f"Saved JSON: {out_json}")


if __name__ == "__main__":
    main()