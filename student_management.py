"""
Student & Academic Management module for the College Academic Management System.
Handles student profiles, enrollment, attendance, exams, and grades.
"""

from utils import (
    load_from_pickle, save_to_pickle, generate_id, validate_section_format,
    calculate_activity_score, calculate_subject_grade, get_gpa,
    safe_string_input, safe_int_input, STUDENTS_FILE
)
from typing import Dict, List, Optional, Tuple


class Student:
    """Student profile object."""
    
    def __init__(self, student_id: str, name: str, contact: str, section: str):
        self.student_id = student_id
        self.name = name
        self.contact = contact
        self.section = section  # Format: COURSE-YEAR-SECTION
        self.enrollment_date = None
        self.enrollment_status = "active"
        self.subjects = {}  # subject_name -> {attendance, exams, activities}
        self.exempted_subjects = []  # List of subjects student is exempted from
    
    def to_dict(self) -> Dict:
        """Convert student to dictionary for display."""
        return {
            "id": self.student_id,
            "name": self.name,
            "contact": self.contact,
            "section": self.section,
            "status": self.enrollment_status,
            "subjects": len(self.subjects)
        }


class StudentManager:
    """Manages student profiles and academic records."""
    
    def __init__(self):
        self.students = load_from_pickle(STUDENTS_FILE)
    
    def save_students(self):
        """Save students to pickle file."""
        save_to_pickle(STUDENTS_FILE, self.students)
    
    def create_student(self, name: str, contact: str, section: str) -> Tuple[bool, str]:
        """
        Create a new student and auto-generate ID (022-xxxxxxx).
        
        Returns: (success, student_id_or_error)
        """
        if not name or len(name) < 2:
            return False, "Student name must be at least 2 characters"
        
        if not contact:
            return False, "Contact information is required"
        
        if not validate_section_format(section):
            return False, f"Invalid section format. Use COURSE-YEAR-SECTION (e.g., BSIT-3-1)"
        
        # Generate student ID
        student_id = generate_id("022", self.students)
        
        # Create student
        student = Student(student_id, name, contact, section)
        self.students[student_id] = student
        
        self.save_students()
        return True, student_id
    
    def get_student(self, student_id: str) -> Optional[Student]:
        """Get student by ID."""
        return self.students.get(student_id)
    
    def get_students_by_section(self, section: str) -> List[Student]:
        """Get all students in a section."""
        return [s for s in self.students.values() if s.section == section]
    
    def list_students(self) -> List[Student]:
        """Get all students."""
        return list(self.students.values())
    
    def update_student(self, student_id: str, name: str = None, contact: str = None, 
                      status: str = None) -> Tuple[bool, str]:
        """Update student information."""
        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        if name:
            student.name = name
        if contact:
            student.contact = contact
        if status:
            student.enrollment_status = status
        
        self.save_students()
        return True, "Student updated successfully"
    
    def delete_student(self, student_id: str) -> Tuple[bool, str]:
        """Delete a student."""
        if student_id not in self.students:
            return False, "Student not found"
        
        del self.students[student_id]
        self.save_students()
        return True, "Student deleted successfully"
    
    # Subject Enrollment Methods
    def enroll_subject(self, student_id: str, subject_name: str) -> Tuple[bool, str]:
        """Enroll student in a subject."""
        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        if subject_name in student.subjects:
            return False, "Student already enrolled in this subject"
        
        student.subjects[subject_name] = {
            "attendance": [],  # List of (date, status: present/absent/tardy)
            "exams": {
                "prelim": None,
                "midterm": None,
                "finals": None
            },
            "activities": []  # List of {total_items, correct_answers}
        }
        
        self.save_students()
        return True, f"Student enrolled in {subject_name}"
    
    def unenroll_subject(self, student_id: str, subject_name: str) -> Tuple[bool, str]:
        """Unenroll student from a subject."""
        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return False, "Student not enrolled in this subject"
        
        del student.subjects[subject_name]
        self.save_students()
        return True, f"Student unenrolled from {subject_name}"
    
    def exempt_subject(self, student_id: str, subject_name: str) -> Tuple[bool, str]:
        """Exempt a student from a subject (excludes from attendance, grades, etc.)."""
        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        if subject_name in student.exempted_subjects:
            return False, "Student is already exempted from this subject"
        
        student.exempted_subjects.append(subject_name)
        self.save_students()
        return True, f"Student exempted from {subject_name}"
    
    def unexempt_subject(self, student_id: str, subject_name: str) -> Tuple[bool, str]:
        """Remove exemption from a subject."""
        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        if subject_name not in student.exempted_subjects:
            return False, "Student is not exempted from this subject"
        
        student.exempted_subjects.remove(subject_name)
        self.save_students()
        return True, f"Student exemption removed from {subject_name}"
    
    def get_student_subjects(self, student_id: str) -> List[str]:
        """Get list of subjects a student is enrolled in."""
        if student_id not in self.students:
            return []
        
        return list(self.students[student_id].subjects.keys())
    
    # Attendance Methods
    def _ensure_subject_initialized(self, student_id: str, subject_name: str) -> Tuple[bool, str]:
        """
        Ensure a subject is initialized in student.subjects.
        Auto-initializes if not already present (for section-based curriculum).
        Returns (success, message)
        """
        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        # Auto-initialize if subject not yet in student.subjects
        if subject_name not in student.subjects:
            student.subjects[subject_name] = {
                "attendance": [],
                "exams": {
                    "prelim": None,
                    "midterm": None,
                    "finals": None
                },
                "activities": []
            }
            self.save_students()
        
        return True, "Subject initialized"
    
    def mark_attendance(self, student_id: str, subject_name: str, 
                       date: str, status: str) -> Tuple[bool, str]:
        """
        Mark attendance for a student in a subject.
        Status: present, absent, tardy
        """
        # Ensure subject is initialized
        success, msg = self._ensure_subject_initialized(student_id, subject_name)
        if not success:
            return False, msg
        
        student = self.students[student_id]
        
        if status not in ["present", "absent", "tardy"]:
            return False, "Invalid attendance status"
        
        # Add or update attendance record
        attendance_list = student.subjects[subject_name]["attendance"]
        
        # Remove existing record for this date if any
        attendance_list = [(d, s) for d, s in attendance_list if d != date]
        attendance_list.append((date, status))
        
        student.subjects[subject_name]["attendance"] = attendance_list
        self.save_students()
        return True, f"Attendance marked as {status}"
    
    def get_attendance(self, student_id: str, subject_name: str) -> Optional[List[Tuple[str, str]]]:
        """Get attendance records for a student in a subject."""
        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        return student.subjects[subject_name]["attendance"]
    
    def get_attendance_summary(self, student_id: str, subject_name: str) -> Optional[Dict[str, int]]:
        """Get attendance summary (present, absent, tardy counts)."""
        attendance = self.get_attendance(student_id, subject_name)
        
        if attendance is None:
            return None
        
        summary = {"present": 0, "absent": 0, "tardy": 0}
        for date, status in attendance:
            if status in summary:
                summary[status] += 1
        
        return summary
    
    # Exam Methods
    def record_exam(self, student_id: str, subject_name: str, 
                   exam_type: str, score: float) -> Tuple[bool, str]:
        """
        Record exam score for a student in a subject.
        exam_type: prelim, midterm, finals
        score: 0-100
        """
        # Ensure subject is initialized
        success, msg = self._ensure_subject_initialized(student_id, subject_name)
        if not success:
            return False, msg
        
        student = self.students[student_id]
        
        if exam_type not in ["prelim", "midterm", "finals"]:
            return False, "Invalid exam type"
        
        if not (0 <= score <= 100):
            return False, "Exam score must be between 0 and 100"
        
        student.subjects[subject_name]["exams"][exam_type] = score
        self.save_students()
        return True, f"{exam_type.capitalize()} exam recorded: {score}"
    
    def get_exam_scores(self, student_id: str, subject_name: str) -> Optional[Dict[str, float]]:
        """Get all exam scores for a student in a subject."""
        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        return student.subjects[subject_name]["exams"]
    
    # Activity Methods
    def add_activity(self, student_id: str, subject_name: str, 
                    total_items: int, correct_answers: int) -> Tuple[bool, str]:
        """
        Add activity score for a student in a subject.
        Automatically calculates score as percentage.
        """
        # Ensure subject is initialized
        success, msg = self._ensure_subject_initialized(student_id, subject_name)
        if not success:
            return False, msg
        
        student = self.students[student_id]
        
        if total_items <= 0:
            return False, "Total items must be greater than 0"
        
        if correct_answers < 0 or correct_answers > total_items:
            return False, "Correct answers must be between 0 and total items"
        
        score = calculate_activity_score(total_items, correct_answers)
        
        student.subjects[subject_name]["activities"].append({
            "total_items": total_items,
            "correct_answers": correct_answers,
            "score": score
        })
        
        self.save_students()
        return True, f"Activity recorded: {correct_answers}/{total_items} ({score:.2f}%)"
    
    def get_activities(self, student_id: str, subject_name: str) -> Optional[List[Dict]]:
        """Get all activity records for a student in a subject."""
        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        return student.subjects[subject_name]["activities"]
    
    def get_activity_average(self, student_id: str, subject_name: str) -> Optional[float]:
        """Get average activity score for a student in a subject."""
        activities = self.get_activities(student_id, subject_name)
        
        if activities is None or len(activities) == 0:
            return None
        
        avg = sum(a["score"] for a in activities) / len(activities)
        return round(avg, 2)
    
    # Grade Calculation Methods
    def get_subject_grade(self, student_id: str, subject_name: str) -> Optional[float]:
        """
        Calculate final grade for a student in a subject.
        Formula: 50% activities average + 40% exam average + 10% attendance
        Attendance scoring: Present=100%, Tardy=50%, Absent=0%
        """
        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        # Get activity scores
        activities = student.subjects[subject_name]["activities"]
        activity_scores = [a["score"] for a in activities]
        
        # Get exam scores
        exam_scores = student.subjects[subject_name]["exams"]
        exam_scores = {k: v for k, v in exam_scores.items() if v is not None}
        
        # Get attendance records
        attendance = student.subjects[subject_name]["attendance"]
        
        return calculate_subject_grade(activity_scores, exam_scores, attendance)
    
    def get_subject_grades(self, student_id: str) -> Dict[str, float]:
        """Get all subject grades for a student (excluding exempted subjects)."""
        if student_id not in self.students:
            return {}
        
        student = self.students[student_id]
        grades = {}
        for subject in self.get_student_subjects(student_id):
            # Skip exempted subjects
            if subject in student.exempted_subjects:
                continue
            grade = self.get_subject_grade(student_id, subject)
            if grade is not None:
                grades[subject] = grade
        
        return grades
    
    def get_gpa(self, student_id: str) -> Optional[float]:
        """Get GPA for a student (average of all non-exempted subject grades)."""
        subject_grades = self.get_subject_grades(student_id)
        return get_gpa(subject_grades) if subject_grades else None
