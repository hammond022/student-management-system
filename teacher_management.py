

from utils import (
    load_from_pickle, save_to_pickle, generate_id, validate_section_format,
    safe_string_input, safe_int_input, TEACHERS_FILE
)
from typing import Dict, List, Optional, Tuple
import json

class Teacher:

    def __init__(self, teacher_id: str, name: str, email: str, phone: str):
        self.teacher_id = teacher_id
        self.name = name
        self.email = email
        self.phone = phone
        self.qualifications = []
        self.subjects_taught = []
        self.class_sessions = []  # List of section assignments (COURSE-YEAR-SECTION)
        self.leave_requests = []
        self.schedules = {}  # section -> [schedule objects]
    
    def to_dict(self) -> Dict:

        return {
            "id": self.teacher_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "subjects": len(self.subjects_taught),
            "sections": len(self.class_sessions)
        }

class Schedule:

    def __init__(self, subject: str, day: str, start_time: str, end_time: str, room: str):
        self.subject = subject
        self.day = day  # Monday-Friday or Saturday
        self.start_time = start_time  # HH:MM format (24-hour)
        self.end_time = end_time  # HH:MM format (24-hour)
        self.room = room
    
    def to_dict(self) -> Dict:

        return {
            "subject": self.subject,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "room": self.room
        }
    
    def overlaps_with(self, other: 'Schedule') -> bool:

        if self.day != other.day:
            return False
        
        self_start = int(self.start_time.split(":")[0]) * 60 + int(self.start_time.split(":")[1])
        self_end = int(self.end_time.split(":")[0]) * 60 + int(self.end_time.split(":")[1])
        other_start = int(other.start_time.split(":")[0]) * 60 + int(other.start_time.split(":")[1])
        other_end = int(other.end_time.split(":")[0]) * 60 + int(other.end_time.split(":")[1])
        
        return not (self_end <= other_start or self_start >= other_end)

class TeacherManager:

    def __init__(self):
        self.teachers = load_from_pickle(TEACHERS_FILE)
    
    def save_teachers(self):

        save_to_pickle(TEACHERS_FILE, self.teachers)
    
    def create_teacher(self, name: str, email: str, phone: str) -> Tuple[bool, str]:

        if not name or len(name) < 2:
            return False, "Teacher name must be at least 2 characters"
        
        if not email or "@" not in email:
            return False, "Valid email is required"
        
        if not phone:
            return False, "Phone number is required"
        
        teacher_id = generate_id("011", self.teachers)
        
        teacher = Teacher(teacher_id, name, email, phone)
        self.teachers[teacher_id] = teacher
        
        self.save_teachers()
        return True, teacher_id
    
    def get_teacher(self, teacher_id: str) -> Optional[Teacher]:

        return self.teachers.get(teacher_id)
    
    def list_teachers(self) -> List[Teacher]:

        return list(self.teachers.values())
    
    def update_teacher(self, teacher_id: str, name: str = None, email: str = None,
                      phone: str = None) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        teacher = self.teachers[teacher_id]
        
        if name:
            teacher.name = name
        if email:
            teacher.email = email
        if phone:
            teacher.phone = phone
        
        self.save_teachers()
        return True, "Teacher updated successfully"
    
    def delete_teacher(self, teacher_id: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        del self.teachers[teacher_id]
        self.save_teachers()
        return True, "Teacher deleted successfully"
    
    def add_qualification(self, teacher_id: str, qualification: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        teacher = self.teachers[teacher_id]
        
        if qualification in teacher.qualifications:
            return False, "Teacher already has this qualification"
        
        teacher.qualifications.append(qualification)
        self.save_teachers()
        return True, f"Qualification '{qualification}' added"
    
    def get_qualifications(self, teacher_id: str) -> Optional[List[str]]:

        if teacher_id not in self.teachers:
            return None
        
        return self.teachers[teacher_id].qualifications
    
    def add_subject(self, teacher_id: str, subject: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        teacher = self.teachers[teacher_id]
        
        if subject in teacher.subjects_taught:
            return False, "Teacher already teaches this subject"
        
        teacher.subjects_taught.append(subject)
        self.save_teachers()
        return True, f"Subject '{subject}' added"
    
    def get_subjects(self, teacher_id: str) -> Optional[List[str]]:

        if teacher_id not in self.teachers:
            return None
        
        return self.teachers[teacher_id].subjects_taught
    
    def _ensure_section_initialized(self, teacher_id: str, section: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        if not validate_section_format(section):
            return False, "Invalid section format. Use COURSE-YEAR-SECTION"
        
        teacher = self.teachers[teacher_id]
        
        if section not in teacher.class_sessions:
            teacher.class_sessions.append(section)
        
        if section not in teacher.schedules:
            teacher.schedules[section] = []
        
        self.save_teachers()
        return True, "Section initialized"
    
    def unassign_section(self, teacher_id: str, section: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        teacher = self.teachers[teacher_id]
        
        if section not in teacher.class_sessions:
            return False, "Teacher not assigned to this section"
        
        teacher.class_sessions.remove(section)
        if section in teacher.schedules:
            del teacher.schedules[section]
        
        self.save_teachers()
        return True, f"Teacher unassigned from section {section}"
    
    def get_sections(self, teacher_id: str) -> Optional[List[str]]:

        if teacher_id not in self.teachers:
            return None
        
        return self.teachers[teacher_id].class_sessions
    
    def check_teacher_scheduling_conflict(self, teacher_id: str, day: str, 
                                          start_time: str, end_time: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, ""
        
        teacher = self.teachers[teacher_id]
        new_schedule = Schedule("temp", day, start_time, end_time, "")
        
        for section, schedules in teacher.schedules.items():
            for existing_schedule in schedules:
                if new_schedule.overlaps_with(existing_schedule):
                    return True, f"Teacher has a conflict: {existing_schedule.subject} in {section} at {existing_schedule.start_time}-{existing_schedule.end_time} on {day}"
        
        return False, ""
    
    def add_schedule(self, teacher_id: str, section: str, subject: str,
                    day: str, start_time: str, end_time: str, room: str) -> Tuple[bool, str]:

        success, msg = self._ensure_section_initialized(teacher_id, section)
        if not success:
            return False, msg
        
        teacher = self.teachers[teacher_id]
        
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        if day not in valid_days:
            return False, f"Invalid day. Must be one of: {', '.join(valid_days)}"
        
        try:
            start_h, start_m = map(int, start_time.split(":"))
            end_h, end_m = map(int, end_time.split(":"))
            
            if not (0 <= start_h < 24 and 0 <= start_m < 60):
                return False, "Invalid start time"
            if not (0 <= end_h < 24 and 0 <= end_m < 60):
                return False, "Invalid end time"
            
            if start_time >= end_time:
                return False, "Start time must be before end time"
        except ValueError:
            return False, "Time must be in HH:MM format"
        
        has_conflict, conflict_msg = self.check_teacher_scheduling_conflict(teacher_id, day, start_time, end_time)
        if has_conflict:
            return False, conflict_msg
        
        schedule = Schedule(subject, day, start_time, end_time, room)
        teacher.schedules[section].append(schedule)
        
        self.save_teachers()
        return True, f"Schedule added: {subject} on {day} {start_time}-{end_time} in {room}"
    
    def get_schedules(self, teacher_id: str, section: str) -> Optional[List[Schedule]]:

        if teacher_id not in self.teachers:
            return None
        
        teacher = self.teachers[teacher_id]
        
        if section not in teacher.schedules:
            return None
        
        return teacher.schedules[section]
    
    def remove_schedule(self, teacher_id: str, section: str, schedule_index: int) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        teacher = self.teachers[teacher_id]
        
        if section not in teacher.schedules:
            return False, "Section not found"
        
        schedules = teacher.schedules[section]
        
        if schedule_index < 0 or schedule_index >= len(schedules):
            return False, "Schedule index out of range"
        
        removed = schedules.pop(schedule_index)
        self.save_teachers()
        return True, f"Schedule removed: {removed.subject} on {removed.day}"
    
    def request_leave(self, teacher_id: str, date_from: str, date_to: str, reason: str) -> Tuple[bool, str]:

        if teacher_id not in self.teachers:
            return False, "Teacher not found"
        
        teacher = self.teachers[teacher_id]
        
        leave_request = {
            "date_from": date_from,
            "date_to": date_to,
            "reason": reason,
            "status": "pending"
        }
        
        teacher.leave_requests.append(leave_request)
        self.save_teachers()
        return True, "Leave request submitted"
    
    def get_leave_requests(self, teacher_id: str) -> Optional[List[Dict]]:

        if teacher_id not in self.teachers:
            return None
        
        return self.teachers[teacher_id].leave_requests
