from dataclasses import dataclass, asdict
from typing import List, Optional
import pickle
import os
from datetime import date
from utils import generate_id

EVALUATIONS_FILE = "data/faculty_evaluations.pkl"

@dataclass
class Evaluation:
    evaluation_id: str
    student_id: str
    teacher_id: str
    rating: int  # 1-5
    comment: str
    date: str

class FacultyEvaluationManager:

    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.evaluations = self._load()

    def _load(self) -> List[Evaluation]:
        try:
            with open(EVALUATIONS_FILE, "rb") as f:
                data = pickle.load(f)
                return [Evaluation(**item) for item in data]
        except Exception:
            return []

    def _save(self):
        with open(EVALUATIONS_FILE, "wb") as f:
            pickle.dump([asdict(e) for e in self.evaluations], f)

    def add_evaluation(self, student_id: str, teacher_id: str, rating: int, comment: str) -> Optional[str]:
        if rating < 1 or rating > 5:
            return None

        eval_id = generate_id("FEV", {e.evaluation_id: e for e in self.evaluations})
        evaluation = Evaluation(eval_id, student_id, teacher_id, rating, comment or "", date.today().isoformat())
        self.evaluations.append(evaluation)
        self._save()
        return eval_id

    def get_evaluations_for_teacher(self, teacher_id: str) -> List[Evaluation]:
        return [e for e in self.evaluations if e.teacher_id == teacher_id]

    def get_average_rating(self, teacher_id: str) -> Optional[float]:
        evals = self.get_evaluations_for_teacher(teacher_id)
        if not evals:
            return None
        return sum(e.rating for e in evals) / len(evals)

    def get_count(self, teacher_id: str) -> int:
        return len(self.get_evaluations_for_teacher(teacher_id))
