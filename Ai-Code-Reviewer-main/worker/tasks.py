# worker/tasks.py
import time

def run_review_job(repo: str, pr_number: int):
    print(f"[worker] Starting review job for {repo} PR #{pr_number}")
    time.sleep(2)

    review_results = {
        "summary": "No critical issues found",
        "issues": [
            {"file": "main.py", "line": 10, "message": "Consider adding error handling"},
            {"file": "utils.py", "line": 5, "message": "Function could be optimized"}
        ]
    }

    print(f"[worker] Finished review job for {repo} PR #{pr_number}")
    return review_results
