

from utils import (
    load_from_pickle, save_to_pickle, generate_id, validate_section_format,
    calculate_activity_score, calculate_subject_grade, get_gpa,
    safe_string_input, safe_int_input, STUDENTS_FILE
)
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

EXAMS_FILE = "data/exams.pkl"
DISCIPLINE_FILE = "data/discipline.pkl"
ARCHIVE_FILE = "data/academic_archive.pkl"

class ExamSchedule:
    """Manages exam schedules for sections"""
    
    def __init__(self, exam_id: str, section: str, subject: str, exam_type: str,
                 exam_date: str, start_time: str, end_time: str, room: str):
        self.exam_id = exam_id
        self.section = section
        self.subject = subject
        self.exam_type = exam_type  # prelim, midterm, finals
        self.exam_date = exam_date
        self.start_time = start_time
        self.end_time = end_time
        self.room = room
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.exam_id,
            "section": self.section,
            "subject": self.subject,
            "exam_type": self.exam_type,
            "date": self.exam_date,
            "start": self.start_time,
            "end": self.end_time,
            "room": self.room
        }

class DisciplinaryRecord:
    """Records disciplinary actions and commendations for students"""
    
    def __init__(self, record_id: str, student_id: str, action_type: str,
                 description: str, date: str, recorded_by: str):
        self.record_id = record_id
        self.student_id = student_id
        self.action_type = action_type  # "discipline" or "commendation"
        self.description = description
        self.date = date
        self.recorded_by = recorded_by
        self.severity = None  # "minor", "major", "severe" for disciplines
        self.status = "active"  # "active", "resolved"
        self.resolution_notes = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.record_id,
            "student_id": self.student_id,
            "type": self.action_type,
            "description": self.description,
            "date": self.date,
            "recorded_by": self.recorded_by,
            "severity": self.severity,
            "status": self.status,
            "resolution_notes": self.resolution_notes
        }

class AcademicSnapshot:
    """Captures a snapshot of student's academic record at a point in time"""
    
    def __init__(self, student_id: str, section: str, subjects_data: Dict,
                 gpa: Optional[float], snapshot_date: str, semester: str):
        self.student_id = student_id
        self.section = section
        self.subjects_data = subjects_data  # Full subject data including grades, attendance
        self.gpa = gpa
        self.snapshot_date = snapshot_date
        self.semester = semester  # "sem1", "sem2", "year-end"
        self.archive_id = generate_id("ARC", {})
    
    def to_dict(self) -> Dict:
        return {
            "archive_id": self.archive_id,
            "student_id": self.student_id,
            "section": self.section,
            "subjects_data": self.subjects_data,
            "gpa": self.gpa,
            "snapshot_date": self.snapshot_date,
            "semester": self.semester
        }

class Student:

    def __init__(self, student_id: str, name: str, contact: str, section: str):
        self.student_id = student_id
        self.name = name
        self.contact = contact
        self.section = section  # Format: COURSE-YEAR-SECTION
        self.enrollment_date = None
        self.enrollment_status = "active"
        self.subjects = {}  # subject_name -> {attendance, exams, activities}
        self.dropped_subjects = {}  # subject_name -> reason
        self.disciplinary_records = []  # List of DisciplinaryRecord IDs
        self.academic_history = []  # List of AcademicSnapshot IDs for archived records
    
    def to_dict(self) -> Dict:

        return {
            "id": self.student_id,
            "name": self.name,
            "contact": self.contact,
            "section": self.section,
            "status": self.enrollment_status,
            "subjects": len(self.subjects),
            "disciplinary_count": len(self.disciplinary_records),
            "history_count": len(self.academic_history)
        }

class StudentManager:

    def __init__(self):
        self.students = load_from_pickle(STUDENTS_FILE)
    
    def save_students(self):

        save_to_pickle(STUDENTS_FILE, self.students)
    
    def create_student(self, name: str, contact: str, section: str) -> Tuple[bool, str]:

        if not name or len(name) < 2:
            return False, "Student name must be at least 2 characters"
        
        if not contact:
            return False, "Contact information is required"
        
        if not validate_section_format(section):
            return False, f"Invalid section format. Use COURSE-YEAR-SECTION (e.g., BSIT-3-1)"
        
        student_id = generate_id("022", self.students)
        
        student = Student(student_id, name, contact, section)
        self.students[student_id] = student
        
        self.save_students()
        return True, student_id
    
    def get_student(self, student_id: str) -> Optional[Student]:

        return self.students.get(student_id)
    
    def get_students_by_section(self, section: str) -> List[Student]:

        return [s for s in self.students.values() if s.section == section]
    
    def list_students(self) -> List[Student]:

        return list(self.students.values())
    
    def update_student(self, student_id: str, name: str = None, contact: str = None, 
                      status: str = None) -> Tuple[bool, str]:

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

        if student_id not in self.students:
            return False, "Student not found"
        
        del self.students[student_id]
        self.save_students()
        return True, "Student deleted successfully"
    
    def enroll_subject(self, student_id: str, subject_name: str) -> Tuple[bool, str]:

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

        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return False, "Student not enrolled in this subject"
        
        del student.subjects[subject_name]
        self.save_students()
        return True, f"Student unenrolled from {subject_name}"
    
    def drop_subject(self, student_id: str, subject_name: str, reason: str) -> Tuple[bool, str]:
        if student_id not in self.students:
            return False, "Student not found"
        student = self.students[student_id]
        if subject_name in student.dropped_subjects:
            return False, "Student has already dropped this subject"
        student.dropped_subjects[subject_name] = reason
        self.save_students()
        return True, f"Student dropped {subject_name}. Reason: {reason}"
    
    def undo_drop_subject(self, student_id: str, subject_name: str) -> Tuple[bool, str]:
        if student_id not in self.students:
            return False, "Student not found"
        student = self.students[student_id]
        if subject_name not in student.dropped_subjects:
            return False, "Subject is not dropped for this student"
        del student.dropped_subjects[subject_name]
        self.save_students()
        return True, f"Drop removed for {subject_name}"
    
    def get_student_subjects(self, student_id: str) -> List[str]:
        if student_id not in self.students:
            return []
        return list(self.students[student_id].subjects.keys())
    
    def _ensure_subject_initialized(self, student_id: str, subject_name: str) -> Tuple[bool, str]:

        if student_id not in self.students:
            return False, "Student not found"
        
        student = self.students[student_id]
        
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

        success, msg = self._ensure_subject_initialized(student_id, subject_name)
        if not success:
            return False, msg
        
        student = self.students[student_id]
        
        if status not in ["present", "absent", "tardy"]:
            return False, "Invalid attendance status"
        
        attendance_list = student.subjects[subject_name]["attendance"]
        
        attendance_list = [(d, s) for d, s in attendance_list if d != date]
        attendance_list.append((date, status))
        
        student.subjects[subject_name]["attendance"] = attendance_list
        self.save_students()
        return True, f"Attendance marked as {status}"
    
    def get_attendance(self, student_id: str, subject_name: str) -> Optional[List[Tuple[str, str]]]:

        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        return student.subjects[subject_name]["attendance"]
    
    def get_attendance_summary(self, student_id: str, subject_name: str) -> Optional[Dict[str, int]]:

        attendance = self.get_attendance(student_id, subject_name)
        
        if attendance is None:
            return None
        
        summary = {"present": 0, "absent": 0, "tardy": 0}
        for date, status in attendance:
            if status in summary:
                summary[status] += 1
        
        return summary
    
    def record_exam(self, student_id: str, subject_name: str, 
                   exam_type: str, score: float) -> Tuple[bool, str]:

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

        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        return student.subjects[subject_name]["exams"]
    
    def add_activity(self, student_id: str, subject_name: str, 
                    total_items: int, correct_answers: int) -> Tuple[bool, str]:

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

        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        return student.subjects[subject_name]["activities"]
    
    def get_activity_average(self, student_id: str, subject_name: str) -> Optional[float]:

        activities = self.get_activities(student_id, subject_name)
        
        if activities is None or len(activities) == 0:
            return None
        
        avg = sum(a["score"] for a in activities) / len(activities)
        return round(avg, 2)
    
    def get_subject_grade(self, student_id: str, subject_name: str) -> Optional[float]:

        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        
        if subject_name not in student.subjects:
            return None
        
        activities = student.subjects[subject_name]["activities"]
        activity_scores = [a["score"] for a in activities]
        
        exam_scores = student.subjects[subject_name]["exams"]
        exam_scores = {k: v for k, v in exam_scores.items() if v is not None}
        
        attendance = student.subjects[subject_name]["attendance"]
        
        return calculate_subject_grade(activity_scores, exam_scores, attendance)
    
    def get_subject_grades(self, student_id: str) -> Dict[str, float]:

        if student_id not in self.students:
            return {}
        
        student = self.students[student_id]
        grades = {}
        for subject in self.get_student_subjects(student_id):
            if subject in getattr(student, 'dropped_subjects', {}):
                continue
            grade = self.get_subject_grade(student_id, subject)
            if grade is not None:
                grades[subject] = grade
        
        return grades
    
    def get_gpa(self, student_id: str) -> Optional[float]:

        subject_grades = self.get_subject_grades(student_id)
        return get_gpa(subject_grades) if subject_grades else None

class ExamScheduleManager:
    """Manages exam schedules for the entire system"""
    
    def __init__(self):
        self.exams = load_from_pickle(EXAMS_FILE)
    
    def save_exams(self):
        save_to_pickle(EXAMS_FILE, self.exams)
    
    def create_exam_schedule(self, section: str, subject: str, exam_type: str,
                            exam_date: str, start_time: str, end_time: str,
                            room: str) -> Tuple[bool, str]:
        """Create a new exam schedule"""
        if not section or not subject or not exam_type or not exam_date:
            return False, "Missing required exam details"
        
        if exam_type not in ["prelim", "midterm", "finals"]:
            return False, "Invalid exam type"
        
        exam_id = generate_id("EXM", self.exams)
        exam = ExamSchedule(exam_id, section, subject, exam_type, exam_date,
                           start_time, end_time, room)
        self.exams[exam_id] = exam
        self.save_exams()
        return True, f"Exam schedule created: {exam_id}"
    
    def get_exam_schedule(self, exam_id: str) -> Optional[ExamSchedule]:
        return self.exams.get(exam_id)
    
    def get_schedules_by_section(self, section: str) -> List[ExamSchedule]:
        """Get all exam schedules for a section"""
        return [e for e in self.exams.values() if e.section == section]
    
    def get_schedules_by_subject(self, subject: str) -> List[ExamSchedule]:
        """Get all exam schedules for a subject"""
        return [e for e in self.exams.values() if e.subject == subject]
    
    def get_schedules_by_date(self, exam_date: str) -> List[ExamSchedule]:
        """Get all exam schedules for a specific date"""
        return [e for e in self.exams.values() if e.exam_date == exam_date]
    
    def update_exam_schedule(self, exam_id: str, exam_date: str = None,
                            start_time: str = None, end_time: str = None,
                            room: str = None) -> Tuple[bool, str]:
        """Update an exam schedule"""
        if exam_id not in self.exams:
            return False, "Exam schedule not found"
        
        exam = self.exams[exam_id]
        if exam_date:
            exam.exam_date = exam_date
        if start_time:
            exam.start_time = start_time
        if end_time:
            exam.end_time = end_time
        if room:
            exam.room = room
        
        self.save_exams()
        return True, "Exam schedule updated"
    
    def delete_exam_schedule(self, exam_id: str) -> Tuple[bool, str]:
        """Delete an exam schedule"""
        if exam_id not in self.exams:
            return False, "Exam schedule not found"
        
        del self.exams[exam_id]
        self.save_exams()
        return True, "Exam schedule deleted"
    
    def list_all_exams(self) -> List[ExamSchedule]:
        return list(self.exams.values())
    
    def check_exam_conflict(self, section: str, exam_date: str, start_time: str,
                           end_time: str) -> Tuple[bool, str]:
        """Check if there's a scheduling conflict for an exam"""
        for exam in self.get_schedules_by_section(section):
            if exam.exam_date == exam_date:
                exam_start = exam.start_time.split(":")
                exam_end = exam.end_time.split(":")
                new_start = start_time.split(":")
                new_end = end_time.split(":")
                
                exam_start_mins = int(exam_start[0]) * 60 + int(exam_start[1])
                exam_end_mins = int(exam_end[0]) * 60 + int(exam_end[1])
                new_start_mins = int(new_start[0]) * 60 + int(new_start[1])
                new_end_mins = int(new_end[0]) * 60 + int(new_end[1])
                
                if not (new_end_mins <= exam_start_mins or new_start_mins >= exam_end_mins):
                    return True, f"Conflict with {exam.subject} exam"
        
        return False, "No conflict"


class DisciplineManager:
    """Manages disciplinary records and commendations for students"""
    
    def __init__(self, student_manager: StudentManager):
        self.records = load_from_pickle(DISCIPLINE_FILE)
        self.student_mgr = student_manager
    
    def save_records(self):
        save_to_pickle(DISCIPLINE_FILE, self.records)
    
    def add_discipline(self, student_id: str, description: str, severity: str,
                      recorded_by: str) -> Tuple[bool, str]:
        """Record a disciplinary action"""
        if student_id not in self.student_mgr.students:
            return False, "Student not found"
        
        if severity not in ["minor", "major", "severe"]:
            return False, "Invalid severity level"
        
        record_id = generate_id("DIS", self.records)
        record = DisciplinaryRecord(record_id, student_id, "discipline",
                                   description, datetime.now().strftime("%Y-%m-%d"), recorded_by)
        record.severity = severity
        
        self.records[record_id] = record
        self.student_mgr.students[student_id].disciplinary_records.append(record_id)
        
        self.save_records()
        self.student_mgr.save_students()
        return True, f"Disciplinary record created: {record_id}"
    
    def add_commendation(self, student_id: str, description: str,
                        recorded_by: str) -> Tuple[bool, str]:
        """Record a commendation for a student"""
        if student_id not in self.student_mgr.students:
            return False, "Student not found"
        
        record_id = generate_id("COM", self.records)
        record = DisciplinaryRecord(record_id, student_id, "commendation",
                                   description, datetime.now().strftime("%Y-%m-%d"), recorded_by)
        
        self.records[record_id] = record
        self.student_mgr.students[student_id].disciplinary_records.append(record_id)
        
        self.save_records()
        self.student_mgr.save_students()
        return True, f"Commendation recorded: {record_id}"
    
    def get_record(self, record_id: str) -> Optional[DisciplinaryRecord]:
        return self.records.get(record_id)
    
    def get_student_records(self, student_id: str) -> List[DisciplinaryRecord]:
        """Get all disciplinary records and commendations for a student"""
        if student_id not in self.student_mgr.students:
            return []
        
        student = self.student_mgr.students[student_id]
        return [self.records[rid] for rid in student.disciplinary_records if rid in self.records]
    
    def get_student_disciplines(self, student_id: str) -> List[DisciplinaryRecord]:
        """Get only disciplinary actions for a student"""
        records = self.get_student_records(student_id)
        return [r for r in records if r.action_type == "discipline"]
    
    def get_student_commendations(self, student_id: str) -> List[DisciplinaryRecord]:
        """Get only commendations for a student"""
        records = self.get_student_records(student_id)
        return [r for r in records if r.action_type == "commendation"]
    
    def resolve_discipline(self, record_id: str, resolution_notes: str) -> Tuple[bool, str]:
        """Mark a disciplinary record as resolved"""
        if record_id not in self.records:
            return False, "Record not found"
        
        record = self.records[record_id]
        if record.action_type != "discipline":
            return False, "Only disciplinary records can be marked as resolved"
        
        record.status = "resolved"
        record.resolution_notes = resolution_notes
        self.save_records()
        return True, "Disciplinary record marked as resolved"
    
    def list_all_records(self) -> List[DisciplinaryRecord]:
        return list(self.records.values())
    
    def get_unresolved_disciplines(self) -> List[DisciplinaryRecord]:
        """Get all unresolved disciplinary records"""
        return [r for r in self.records.values() 
                if r.action_type == "discipline" and r.status == "active"]


class AcademicArchiveManager:
    """Manages historical academic record snapshots"""
    
    def __init__(self, student_manager: StudentManager):
        self.archives = load_from_pickle(ARCHIVE_FILE)
        self.student_mgr = student_manager
    
    def save_archives(self):
        save_to_pickle(ARCHIVE_FILE, self.archives)
    
    def create_snapshot(self, student_id: str, semester: str) -> Tuple[bool, str]:
        """Create a snapshot of a student's current academic record"""
        if student_id not in self.student_mgr.students:
            return False, "Student not found"
        
        student = self.student_mgr.students[student_id]
        gpa = self.student_mgr.get_gpa(student_id)
        
        snapshot = AcademicSnapshot(
            student_id,
            student.section,
            student.subjects.copy(),
            gpa,
            datetime.now().strftime("%Y-%m-%d"),
            semester
        )
        
        self.archives[snapshot.archive_id] = snapshot
        self.student_mgr.students[student_id].academic_history.append(snapshot.archive_id)
        
        self.save_archives()
        self.student_mgr.save_students()
        return True, f"Academic snapshot created: {snapshot.archive_id}"
    
    def get_snapshot(self, archive_id: str) -> Optional[AcademicSnapshot]:
        return self.archives.get(archive_id)
    
    def get_student_history(self, student_id: str) -> List[AcademicSnapshot]:
        """Get all historical snapshots for a student"""
        if student_id not in self.student_mgr.students:
            return []
        
        student = self.student_mgr.students[student_id]
        return [self.archives[aid] for aid in student.academic_history if aid in self.archives]
    
    def get_history_by_semester(self, student_id: str, semester: str) -> List[AcademicSnapshot]:
        """Get historical snapshots for a specific semester"""
        history = self.get_student_history(student_id)
        return [s for s in history if s.semester == semester]
    
    def compare_snapshots(self, archive_id1: str, archive_id2: str) -> Dict:
        """Compare two academic snapshots"""
        snap1 = self.get_snapshot(archive_id1)
        snap2 = self.get_snapshot(archive_id2)
        
        if not snap1 or not snap2:
            return {}
        
        return {
            "snapshot1": snap1.to_dict(),
            "snapshot2": snap2.to_dict(),
            "gpa_change": (snap2.gpa or 0) - (snap1.gpa or 0) if snap1.gpa and snap2.gpa else None
        }
    
    def list_all_archives(self) -> List[AcademicSnapshot]:
        return list(self.archives.values())
    
    def get_archives_by_date_range(self, start_date: str, end_date: str) -> List[AcademicSnapshot]:
        """Get all snapshots within a date range"""
        return [s for s in self.archives.values()
                if start_date <= s.snapshot_date <= end_date]