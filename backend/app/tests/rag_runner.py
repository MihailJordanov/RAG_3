import json
import os
import argparse
from datetime import datetime
import time
from typing import Any, Dict, List

# python -m app.tests.rag_runner --case app/tests/rag_cases/little_prince.json
from app.services.rag_chat import ask_question, RAG_CONFIG


FALLBACK_ANSWER = "I don't know based on the provided documents."


def load_case(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def contains_expected(answer: str, expected_contains: List[str]) -> bool:
    answer_norm = normalize_text(answer)
    return all(normalize_text(x) in answer_norm for x in expected_contains)


def evaluate_result(question_item: Dict[str, Any], answer: str) -> Dict[str, Any]:
    q_type = question_item.get("type", "answerable")
    expected_contains = question_item.get("expected_contains", [])

    is_fallback = normalize_text(answer) == normalize_text(FALLBACK_ANSWER)

    if q_type == "unanswerable":
        passed = is_fallback
        return {
            "passed": passed,
            "expected_behavior": "fallback",
            "actual_behavior": "fallback" if is_fallback else "answered",
            "reason": "Correctly refused unsupported question." if passed else "Hallucinated answer for unanswerable question.",
        }

    # answerable
    if is_fallback:
        return {
            "passed": False,
            "expected_behavior": "answer",
            "actual_behavior": "fallback",
            "reason": "Returned fallback for answerable question.",
        }

    if expected_contains:
        matched = contains_expected(answer, expected_contains)
        return {
            "passed": matched,
            "expected_behavior": "answer_with_keywords",
            "actual_behavior": "answer",
            "reason": "Answer contains expected keywords." if matched else "Answer missing expected keywords.",
        }

    return {
        "passed": True,
        "expected_behavior": "answer",
        "actual_behavior": "answer",
        "reason": "Answerable question answered and no keyword constraints were provided.",
    }


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

    total_start = time.time()

    passed_count = 0
    failed_count = 0
    error_count = 0

    answerable_total = 0
    unanswerable_total = 0
    answerable_passed = 0
    unanswerable_passed = 0

    with open(out_txt, "w", encoding="utf-8") as txt_file:
        txt_file.write(f"CASE: {case_name}\n")
        txt_file.write(f"PROJECT_ID: {project_id}\n\n")

        txt_file.write("RAG CONFIG:\n")
        for k, v in RAG_CONFIG.items():
            txt_file.write(f"{k}: {v}\n")

        txt_file.write("\n" + "=" * 80 + "\n\n")

        for i, question_item in enumerate(questions, start=1):
            question = question_item["question"]
            q_type = question_item.get("type", "answerable")
            expected_contains = question_item.get("expected_contains", [])

            if q_type == "answerable":
                answerable_total += 1
            elif q_type == "unanswerable":
                unanswerable_total += 1

            try:
                start = time.time()
                response = ask_question(project_id=project_id, question=question)
                latency = round(time.time() - start, 3)

                answer = response["answer"] if isinstance(response, dict) else str(response)
                evaluation = evaluate_result(question_item, answer)
                passed = evaluation["passed"]

                if passed:
                    passed_count += 1
                    if q_type == "answerable":
                        answerable_passed += 1
                    elif q_type == "unanswerable":
                        unanswerable_passed += 1
                else:
                    failed_count += 1

                result_item = {
                    "index": i,
                    "question": question,
                    "type": q_type,
                    "expected_contains": expected_contains,
                    "answer": answer,
                    "status": "ok",
                    "latency_sec": latency,
                    "passed": passed,
                    "expected_behavior": evaluation["expected_behavior"],
                    "actual_behavior": evaluation["actual_behavior"],
                    "reason": evaluation["reason"],
                }
                results.append(result_item)

                txt_file.write(f"[{i}] QUESTION:\n{question}\n")
                txt_file.write(f"[{i}] TYPE:\n{q_type}\n")
                if expected_contains:
                    txt_file.write(f"[{i}] EXPECTED_CONTAINS:\n{expected_contains}\n")
                txt_file.write(f"[{i}] ANSWER:\n{answer}\n")
                txt_file.write(f"[{i}] RESULT:\n{'PASS' if passed else 'FAIL'}\n")
                txt_file.write(f"[{i}] REASON:\n{evaluation['reason']}\n")
                txt_file.write(f"[{i}] LATENCY_SEC:\n{latency}\n")
                txt_file.write("\n" + "-" * 80 + "\n\n")

                print(f"[{'PASS' if passed else 'FAIL'}] {i}/{len(questions)} {question}")

            except Exception as e:
                error_count += 1
                failed_count += 1

                result_item = {
                    "index": i,
                    "question": question,
                    "type": q_type,
                    "expected_contains": expected_contains,
                    "answer": None,
                    "status": "error",
                    "error": str(e),
                    "passed": False,
                }
                results.append(result_item)

                txt_file.write(f"[{i}] QUESTION:\n{question}\n")
                txt_file.write(f"[{i}] TYPE:\n{q_type}\n")
                if expected_contains:
                    txt_file.write(f"[{i}] EXPECTED_CONTAINS:\n{expected_contains}\n")
                txt_file.write(f"[{i}] ERROR:\n{e}\n")
                txt_file.write(f"[{i}] RESULT:\nFAIL\n")
                txt_file.write(f"[{i}] REASON:\nExecution error.\n")
                txt_file.write("\n" + "-" * 80 + "\n\n")

                print(f"[ERROR] {i}/{len(questions)} {question} -> {e}")

        total_time_sec = round(time.time() - total_start, 3)
        avg_latency_sec = round(
            sum(r.get("latency_sec", 0) for r in results if r.get("status") == "ok") / max(1, len([r for r in results if r.get("status") == "ok"])),
            3,
        )

        txt_file.write("=" * 80 + "\n")
        txt_file.write("SUMMARY\n")
        txt_file.write("=" * 80 + "\n")
        txt_file.write(f"TOTAL_QUESTIONS: {len(questions)}\n")
        txt_file.write(f"PASSED: {passed_count}\n")
        txt_file.write(f"FAILED: {failed_count}\n")
        txt_file.write(f"ERRORS: {error_count}\n")
        txt_file.write(f"ANSWERABLE_TOTAL: {answerable_total}\n")
        txt_file.write(f"ANSWERABLE_PASSED: {answerable_passed}\n")
        txt_file.write(f"UNANSWERABLE_TOTAL: {unanswerable_total}\n")
        txt_file.write(f"UNANSWERABLE_PASSED: {unanswerable_passed}\n")
        txt_file.write(f"TOTAL_TIME_SEC: {total_time_sec}\n")
        txt_file.write(f"AVG_LATENCY_SEC: {avg_latency_sec}\n")

    total_time_sec = round(time.time() - total_start, 3)
    ok_results = [r for r in results if r.get("status") == "ok"]
    avg_latency_sec = round(
        sum(r.get("latency_sec", 0) for r in ok_results) / max(1, len(ok_results)),
        3,
    )

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "case_name": case_name,
            "project_id": project_id,
            "rag_config": RAG_CONFIG,
            "summary": {
                "total_questions": len(questions),
                "passed": passed_count,
                "failed": failed_count,
                "errors": error_count,
                "answerable_total": answerable_total,
                "answerable_passed": answerable_passed,
                "unanswerable_total": unanswerable_total,
                "unanswerable_passed": unanswerable_passed,
                "total_time_sec": total_time_sec,
                "avg_latency_sec": avg_latency_sec,
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"TOTAL QUESTIONS: {len(questions)}")
    print(f"PASSED: {passed_count}")
    print(f"FAILED: {failed_count}")
    print(f"ERRORS: {error_count}")
    print(f"ANSWERABLE: {answerable_passed}/{answerable_total}")
    print(f"UNANSWERABLE: {unanswerable_passed}/{unanswerable_total}")
    print(f"TOTAL TIME: {total_time_sec}s")
    print(f"AVG LATENCY: {avg_latency_sec}s")

    print(f"\nSaved TXT: {out_txt}")
    print(f"Saved JSON: {out_json}")


if __name__ == "__main__":
    main()