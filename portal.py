

import sys
from utils import (
    clear_screen, print_header, print_section, safe_string_input, safe_int_input,
    validate_password, generate_id, load_from_pickle, save_to_pickle
)
from student_management import (StudentManager, DisciplineManager, 
                                 AcademicArchiveManager, ExamScheduleManager)
from teacher_management import TeacherManager
from communication import CommunicationManager
from fee_management import FeeManager
from faculty_evaluation import FacultyEvaluationManager
import hashlib
import pickle

class UserAccount:

    def __init__(self, user_id: str, user_type: str, password_hash: str):
        self.user_id = user_id
        self.user_type = user_type  # "student", "teacher", or "parent"
        self.password_hash = password_hash
    
    @staticmethod
    def hash_password(password: str) -> str:

        return hashlib.sha256(password.encode()).hexdigest()

class UserPortal:

    ACCOUNTS_FILE = "data/user_accounts.pkl"
    
    def __init__(self):
        self.student_mgr = StudentManager()
        self.teacher_mgr = TeacherManager()
        self.comm_mgr = CommunicationManager()
        self.fee_mgr = FeeManager()
        self.discipline_mgr = DisciplineManager(self.student_mgr)
        self.archive_mgr = AcademicArchiveManager(self.student_mgr)
        self.exam_mgr = ExamScheduleManager()
        self.eval_mgr = FacultyEvaluationManager()
        self.accounts = self._load_accounts()
        self.current_user = None
        self.current_role = None
        self.current_id = None
    
    def _load_accounts(self):

        try:
            with open(self.ACCOUNTS_FILE, "rb") as f:
                return pickle.load(f)
        except:
            return {}
    
    def _save_accounts(self):

        import os
        os.makedirs("data", exist_ok=True)
        with open(self.ACCOUNTS_FILE, "wb") as f:
            pickle.dump(self.accounts, f)
    
    def show_auth_menu(self):

        clear_screen()
        print("=" * 60)
        print("  UNIFIED USER PORTAL")
        print("=" * 60)
        print("\n1. Login")
        print("2. Create New Account")
        print("0. Exit")
        print("\n" + "-" * 60)
        return safe_string_input("Choose option: ")
    
    def show_role_selection(self):

        clear_screen()
        print_header("CREATE NEW ACCOUNT - SELECT ROLE")
        print("\n1. Student")
        print("2. Teacher")
        print("3. Parent")
        print("0. Back")
        print("\n" + "-" * 60)
        return safe_string_input("Select your role: ")
    
    def create_account(self):

        role_choice = self.show_role_selection()
        
        if role_choice == "1":
            self._create_student_account()
        elif role_choice == "2":
            self._create_teacher_account()
        elif role_choice == "3":
            self._create_parent_account()
        elif role_choice != "0":
            print("Invalid option.")
            input("Press Enter to continue...")
    
    def _create_student_account(self):

        clear_screen()
        print_header("CREATE STUDENT ACCOUNT")
        
        student_id = safe_string_input("\nEnter your Student ID: ")
        if not student_id:
            print("Student ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        student = self.student_mgr.get_student(student_id)
        if not student:
            print(f"✗ Student ID {student_id} not found in system.")
            print("Please contact administration to register as a student.")
            input("Press Enter to continue...")
            return
        
        account_key = f"student_{student_id}"
        if account_key in self.accounts:
            print("✗ Account already exists for this student ID.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("CONFIRM YOUR INFORMATION")
        print(f"\nStudent ID: {student.student_id}")
        print(f"Name: {student.name}")
        print(f"Section: {student.section}")
        print(f"Contact: {student.contact}")
        print(f"Status: {student.enrollment_status}")
        
        confirm = safe_string_input("\nIs this information correct? (yes/no): ")
        if not (confirm and confirm.lower() == "yes"):
            print("Cancelled.")
            input("Press Enter to continue...")
            return
        
        print("\n--- Set Password ---")
        while True:
            password = safe_string_input("Enter password: ")
            if not password:
                continue
            
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                print(f"✗ {error_msg}")
                continue
            
            confirm_pwd = safe_string_input("Confirm password: ")
            if password != confirm_pwd:
                print("✗ Passwords do not match.")
                continue
            
            break
        
        password_hash = UserAccount.hash_password(password)
        account = UserAccount(student_id, "student", password_hash)
        
        self.accounts[account_key] = {
            "account": account,
            "name": student.name,
            "contact": student.contact
        }
        
        self._save_accounts()
        print(f"\n✓ Student account created successfully!")
        print(f"Student ID: {student_id}")
        print(f"Name: {student.name}")
        input("Press Enter to continue...")
    
    def _create_teacher_account(self):

        clear_screen()
        print_header("CREATE TEACHER ACCOUNT")
        
        teacher_id = safe_string_input("\nEnter your Teacher ID: ")
        if not teacher_id:
            print("Teacher ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print(f"✗ Teacher ID {teacher_id} not found in system.")
            print("Please contact administration to register as a teacher.")
            input("Press Enter to continue...")
            return
        
        account_key = f"teacher_{teacher_id}"
        if account_key in self.accounts:
            print("✗ Account already exists for this teacher ID.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("CONFIRM YOUR INFORMATION")
        print(f"\nTeacher ID: {teacher.teacher_id}")
        print(f"Name: {teacher.name}")
        print(f"Email: {teacher.email}")
        print(f"Phone: {teacher.phone}")
        if teacher.subjects_taught:
            print(f"Subjects: {', '.join(teacher.subjects_taught)}")
        
        confirm = safe_string_input("\nIs this information correct? (yes/no): ")
        if not (confirm and confirm.lower() == "yes"):
            print("Cancelled.")
            input("Press Enter to continue...")
            return
        
        print("\n--- Set Password ---")
        while True:
            password = safe_string_input("Enter password: ")
            if not password:
                continue
            
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                print(f"✗ {error_msg}")
                continue
            
            confirm_pwd = safe_string_input("Confirm password: ")
            if password != confirm_pwd:
                print("✗ Passwords do not match.")
                continue
            
            break
        
        password_hash = UserAccount.hash_password(password)
        account = UserAccount(teacher_id, "teacher", password_hash)
        
        self.accounts[account_key] = {
            "account": account,
            "name": teacher.name,
            "email": teacher.email
        }
        
        self._save_accounts()
        print(f"\n✓ Teacher account created successfully!")
        print(f"Teacher ID: {teacher_id}")
        print(f"Name: {teacher.name}")
        input("Press Enter to continue...")
    
    def _create_parent_account(self):

        clear_screen()
        print_header("CREATE PARENT ACCOUNT")
        
        parent_id = safe_string_input("\nEnter your Parent ID: ")
        if not parent_id:
            print("Parent ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        account_key = f"parent_{parent_id}"
        if account_key in self.accounts:
            print("✗ Account already exists for this Parent ID.")
            print("If you forgot your password, contact administration.")
            input("Press Enter to continue...")
            return
        
        parent = self.comm_mgr.get_parent(parent_id)
        if parent:
            clear_screen()
            print_header("CONFIRM YOUR INFORMATION")
            print(f"\nParent ID: {parent_id}")
            print(f"Name: {parent.name}")
            print(f"Email: {parent.email}")
            print(f"Phone: {parent.phone}")
            
            linked_students = parent.student_ids
            if linked_students:
                print(f"\nLinked Children:")
                for sid in linked_students:
                    student = self.student_mgr.get_student(sid)
                    if student:
                        print(f"  - {student.name}")
            
            confirm = safe_string_input("\nIs this information correct? (yes/no): ")
            if not (confirm and confirm.lower() == "yes"):
                print("Cancelled.")
                input("Press Enter to continue...")
                return
            
            print("\n--- Set Password ---")
            while True:
                password = safe_string_input("Enter password: ")
                if not password:
                    continue
                
                is_valid, error_msg = validate_password(password)
                if not is_valid:
                    print(f"✗ {error_msg}")
                    continue
                
                confirm_pwd = safe_string_input("Confirm password: ")
                if password != confirm_pwd:
                    print("✗ Passwords do not match.")
                    continue
                
                break
            
            password_hash = UserAccount.hash_password(password)
            account = UserAccount(parent_id, "parent", password_hash)
            
            self.accounts[account_key] = {
                "account": account,
                "name": parent.name,
                "email": parent.email
            }
            
            self._save_accounts()
            print(f"\n✓ Parent account created successfully!")
            print(f"Parent ID: {parent_id}")
            print(f"Name: {parent.name}")
            input("Press Enter to continue...")
            return
        else:
            print(f"✗ Parent ID {parent_id} not found in the system.")
            print("Please contact administration to register as a parent.")
            print("An admin must create your parent account first.")
            input("Press Enter to continue...")
            return
    
    def login(self) -> bool:

        clear_screen()
        print_header("LOGIN")
        
        print("\nSelect your role:")
        print("1. Student")
        print("2. Teacher")
        print("3. Parent")
        print("0. Back")
        print("\n" + "-" * 60)
        
        role_choice = safe_string_input("Choose role: ")
        
        role_map = {
            "1": "student",
            "2": "teacher",
            "3": "parent"
        }
        
        if role_choice not in role_map:
            if role_choice == "0":
                return False
            print("Invalid role selection.")
            input("Press Enter to continue...")
            return False
        
        user_type = role_map[role_choice]
        
        user_id = safe_string_input(f"\nEnter your {user_type.capitalize()} ID: ")
        if not user_id:
            return False
        
        password = safe_string_input("Password: ")
        if not password:
            return False
        
        account_key = f"{user_type}_{user_id}"
        
        if account_key not in self.accounts:
            print("✗ Invalid ID or password.")
            input("Press Enter to continue...")
            return False
        
        account_data = self.accounts[account_key]
        password_hash = UserAccount.hash_password(password)
        
        if account_data["account"].password_hash != password_hash:
            print("✗ Invalid ID or password.")
            input("Press Enter to continue...")
            return False
        
        self.current_user = account_data["name"]
        self.current_role = user_type
        self.current_id = user_id
        return True

    def student_main_menu(self):

        clear_screen()
        print_header(f"STUDENT PORTAL - {self.current_user}")
        print(f"\nStudent ID: {self.current_id}")
        print("\n1. View My Information")
        print("2. View My Grades & GPA")
        print("3. View My Attendance")
        print("4. View My Disciplinary Records")
        print("5. View Exam Schedules")
        print("6. View Academic History")
        print("7. Change Password")
        print("8. Evaluate a Teacher")
        print("0. Logout")
        print("\n" + "-" * 60)
    
    def student_view_info(self):

        student = self.student_mgr.get_student(self.current_id)
        if not student:
            print("Student information not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("MY INFORMATION")
        print(f"\nName: {student.name}")
        print(f"Student ID: {student.student_id}")
        print(f"Section: {student.section}")
        print(f"Status: {student.enrollment_status}")
        print(f"Contact: {student.contact}")
        
        if student.subjects:
            print(f"\nEnrolled Subjects: {len(student.subjects)}")
            for subject in student.subjects.keys():
                print(f"  - {subject}")
        
        input("\nPress Enter to continue...")
    
    def student_view_grades(self):

        student = self.student_mgr.get_student(self.current_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        subjects = self.student_mgr.get_student_subjects(self.current_id)
        
        if not subjects:
            print("\nNot enrolled in any subjects yet.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("MY GRADES & GPA")
        print("\nSubject Grades:")
        print("-" * 50)
        
        for subject in subjects:
            grade = self.student_mgr.get_subject_grade(self.current_id, subject)
            exams = self.student_mgr.get_exam_scores(self.current_id, subject)
            activity_avg = self.student_mgr.get_activity_average(self.current_id, subject)
            
            print(f"\n{subject}:")
            if exams:
                for exam_type, score in exams.items():
                    if score is not None:
                        print(f"  {exam_type.capitalize()}: {score:.2f}")
            if activity_avg is not None:
                print(f"  Activities Average: {activity_avg:.2f}")
            if grade is not None:
                print(f"  Final Grade: {grade:.2f}")
        
        gpa = self.student_mgr.get_gpa(self.current_id)
        if gpa is not None:
            print(f"\n{'=' * 50}")
            print(f"Overall GPA: {gpa:.2f}")
        
        input("\nPress Enter to continue...")
    
    def student_view_attendance(self):

        subjects = self.student_mgr.get_student_subjects(self.current_id)
        
        if not subjects:
            print("\nNot enrolled in any subjects yet.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("MY ATTENDANCE")
        print("\nSubjects:")
        for i, subject in enumerate(subjects, 1):
            print(f"{i}. {subject}")
        
        choice = safe_int_input("\nSelect subject: ", 1, len(subjects))
        if choice is None:
            return
        
        subject = subjects[choice - 1]
        attendance = self.student_mgr.get_attendance(self.current_id, subject)
        
        clear_screen()
        print_header(f"ATTENDANCE - {subject}")
        
        if attendance:
            summary = self.student_mgr.get_attendance_summary(self.current_id, subject)
            print(f"\nSummary:")
            print(f"  Present: {summary['present']}")
            print(f"  Absent: {summary['absent']}")
            print(f"  Tardy: {summary['tardy']}")
            print(f"  Total Classes: {len(attendance)}")
            
            if len(attendance) > 0:
                attendance_percentage = (summary['present'] / len(attendance)) * 100
                print(f"  Attendance %: {attendance_percentage:.1f}%")
        else:
            print("\nNo attendance records yet.")
        
        input("\nPress Enter to continue...")
    
    def student_change_password(self):

        print_section("CHANGE PASSWORD")
        
        old_password = safe_string_input("Current password: ")
        if not old_password:
            return
        
        account_key = f"student_{self.current_id}"
        password_hash = UserAccount.hash_password(old_password)
        
        if self.accounts[account_key]["account"].password_hash != password_hash:
            print("✗ Current password is incorrect.")
            input("Press Enter to continue...")
            return
        
        new_password = safe_string_input("New password: ")
        if not new_password:
            return
        
        confirm = safe_string_input("Confirm new password: ")
        if new_password != confirm:
            print("✗ Passwords do not match.")
            input("Press Enter to continue...")
            return
        
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            print(f"✗ {error_msg}")
            input("Press Enter to continue...")
            return
        
        new_hash = UserAccount.hash_password(new_password)
        self.accounts[account_key]["account"].password_hash = new_hash
        self._save_accounts()
        
        print("✓ Password changed successfully.")
        input("Press Enter to continue...")
    
    def student_evaluate_teacher(self):

        print_section("EVALUATE A TEACHER")
        teachers = self.teacher_mgr.list_teachers()
        if not teachers:
            print("\nNo teachers available.")
            input("Press Enter to continue...")
            return

        print("\nTeachers:")
        for i, teacher in enumerate(teachers, 1):
            print(f"{i}. {teacher.name} ({teacher.teacher_id})")

        choice = safe_int_input("\nSelect teacher: ", 1, len(teachers))
        if choice is None:
            return

        teacher = teachers[choice - 1]

        rating = safe_int_input("Rating (1-5): ", 1, 5)
        if rating is None:
            return

        comment = safe_string_input("Comment (optional): ")

        eval_id = self.eval_mgr.add_evaluation(self.current_id, teacher.teacher_id, rating, comment)
        if eval_id:
            print(f"\n✓ Evaluation submitted. ID: {eval_id}")
        else:
            print("\n✗ Failed to submit evaluation. Rating must be 1-5.")

        input("Press Enter to continue...")

    def student_view_discipline(self):
        """View disciplinary records and commendations"""
        clear_screen()
        print_header("MY DISCIPLINARY RECORDS & COMMENDATIONS")
        
        records = self.discipline_mgr.get_student_records(self.current_id)
        disciplines = self.discipline_mgr.get_student_disciplines(self.current_id)
        commendations = self.discipline_mgr.get_student_commendations(self.current_id)
        
        print(f"\nDisciplinary Records: {len(disciplines)}")
        print(f"Commendations: {len(commendations)}")
        
        if not records:
            print("\n✓ No records found.")
            input("Press Enter to continue...")
            return
        
        print("\n" + "-" * 60)
        
        for record in sorted(records, key=lambda r: r.date, reverse=True):
            if record.action_type == "discipline":
                print(f"\n[DISCIPLINE - {record.severity.upper()}]")
            else:
                print(f"\n[COMMENDATION]")
            
            print(f"Date: {record.date}")
            print(f"Description: {record.description}")
            if record.status == "resolved":
                print(f"Status: RESOLVED")
                if record.resolution_notes:
                    print(f"Resolution: {record.resolution_notes}")
            print()
        
        input("Press Enter to continue...")
    
    def student_view_exam_schedules(self):
        """View upcoming exam schedules"""
        clear_screen()
        print_header("MY EXAM SCHEDULES")
        
        student = self.student_mgr.get_student(self.current_id)
        if not student:
            print("✗ Student not found.")
            input("Press Enter to continue...")
            return
        
        # Get all exams for student's section
        exams = self.exam_mgr.get_schedules_by_section(student.section)
        
        if not exams:
            print(f"\nNo exam schedules found for section {student.section}.")
            input("Press Enter to continue...")
            return
        
        print(f"\nSection: {student.section}")
        print(f"Total Exams: {len(exams)}\n")
        
        for exam in sorted(exams, key=lambda e: e.exam_date):
            print(f"Subject: {exam.subject}")
            print(f"  Type: {exam.exam_type.capitalize()}")
            print(f"  Date: {exam.exam_date}")
            print(f"  Time: {exam.start_time} - {exam.end_time}")
            print(f"  Room: {exam.room}")
            print()
        
        input("Press Enter to continue...")
    
    def student_view_academic_history(self):
        """View academic history and snapshots"""
        clear_screen()
        print_header("MY ACADEMIC HISTORY")
        
        history = self.archive_mgr.get_student_history(self.current_id)
        
        if not history:
            print("\nNo academic history available yet.")
            input("Press Enter to continue...")
            return
        
        print(f"\nTotal Snapshots: {len(history)}\n")
        
        for i, snapshot in enumerate(sorted(history, key=lambda s: s.snapshot_date, reverse=True), 1):
            print(f"{i}. {snapshot.semester.upper()} - {snapshot.snapshot_date}")
            print(f"   GPA: {snapshot.gpa:.2f if snapshot.gpa else 'N/A'}")
            print(f"   Subjects: {len(snapshot.subjects_data)}")
            
            # Show choice to view details
            if i == 1:
                view = safe_string_input("   View details? (yes/no): ")
                if view.lower() == "yes":
                    self._show_snapshot_details(snapshot)
            print()
        
        input("Press Enter to continue...")
    
    def _show_snapshot_details(self, snapshot):
        """Display detailed information about an academic snapshot"""
        clear_screen()
        print_header(f"ACADEMIC SNAPSHOT - {snapshot.semester.upper()}")
        
        print(f"\nDate: {snapshot.snapshot_date}")
        print(f"Section: {snapshot.section}")
        print(f"GPA: {snapshot.gpa:.2f if snapshot.gpa else 'N/A'}")
        
        print(f"\nSubjects ({len(snapshot.subjects_data)}):")
        for subject, data in snapshot.subjects_data.items():
            print(f"\n  {subject}")
            exams = data.get("exams", {})
            if exams:
                exam_scores = [v for v in exams.values() if v is not None]
                if exam_scores:
                    print(f"    Exams: {exam_scores}")
            
            attendance = data.get("attendance", [])
            if attendance:
                print(f"    Attendance Records: {len(attendance)}")
            
            activities = data.get("activities", [])
            if activities:
                print(f"    Activities: {len(activities)}")
        
        input("\nPress Enter to continue...")

    def teacher_main_menu(self):

        clear_screen()
        print_header(f"TEACHER PORTAL - {self.current_user}")
        print(f"\nTeacher ID: {self.current_id}")
        print("\n1. View My Schedule")
        print("2. Input Grades")
        print("3. Input Attendance")
        print("4. Change Password")
        print("5. View My Evaluations")
        print("0. Logout")
        print("\n" + "-" * 60)
    
    def teacher_view_schedule(self):

        teacher = self.teacher_mgr.get_teacher(self.current_id)
        if not teacher:
            print("Teacher information not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("MY SCHEDULE")
        print(f"\nName: {teacher.name}")
        print(f"Teacher ID: {teacher.teacher_id}")
        
        if not teacher.class_sessions:
            print("\nNo class sessions assigned.")
            input("Press Enter to continue...")
            return
        
        print(f"\nAssigned Sections: {len(teacher.class_sessions)}")
        for i, section in enumerate(teacher.class_sessions, 1):
            print(f"{i}. {section}")
        
        print("\nSchedules:")
        if teacher.schedules:
            for section, schedules in teacher.schedules.items():
                print(f"\n{section}:")
                for sched in schedules:
                    print(f"  {sched.day}: {sched.subject}")
                    print(f"    {sched.start_time} - {sched.end_time}, Room: {sched.room}")
        else:
            print("No schedules set yet.")
        
        input("\nPress Enter to continue...")
    
    def teacher_input_grades(self):

        print_section("INPUT GRADES")
        
        teacher = self.teacher_mgr.get_teacher(self.current_id)
        if not teacher or not teacher.class_sessions:
            print("No classes assigned.")
            input("Press Enter to continue...")
            return
        
        print("Select section:")
        for i, section in enumerate(teacher.class_sessions, 1):
            print(f"{i}. {section}")
        
        choice = safe_int_input("\nSelect section: ", 1, len(teacher.class_sessions))
        if choice is None:
            return
        
        section = teacher.class_sessions[choice - 1]
        
        section_students = self.student_mgr.get_students_by_section(section)
        if not section_students:
            print("No students in this section.")
            input("Press Enter to continue...")
            return
        
        print(f"\nStudents in {section}:")
        for i, student in enumerate(section_students, 1):
            print(f"{i}. {student.name} ({student.student_id})")
        
        choice = safe_int_input("\nSelect student: ", 1, len(section_students))
        if choice is None:
            return
        
        student = section_students[choice - 1]
        subjects = self.student_mgr.get_student_subjects(student.student_id)
        
        if not subjects:
            print("Student not enrolled in any subjects.")
            input("Press Enter to continue...")
            return
        
        print(f"\nSubjects:")
        for i, subject in enumerate(subjects, 1):
            print(f"{i}. {subject}")
        
        choice = safe_int_input("\nSelect subject: ", 1, len(subjects))
        if choice is None:
            return
        
        subject = subjects[choice - 1]
        
        print(f"\nEnter grade for {student.name} in {subject}:")
        print("Exam types: midterm, final, quiz")
        
        exam_type = safe_string_input("Exam type (midterm/final/quiz): ").lower()
        if exam_type not in ["midterm", "final", "quiz"]:
            print("Invalid exam type.")
            input("Press Enter to continue...")
            return
        
        score = safe_int_input(f"Score (0-100): ", 0, 100)
        if score is None:
            return
        
        print(f"✓ Grade recorded: {student.name} - {subject} ({exam_type}): {score}")
        input("Press Enter to continue...")
    
    def teacher_input_attendance(self):

        print_section("INPUT ATTENDANCE")
        
        teacher = self.teacher_mgr.get_teacher(self.current_id)
        if not teacher or not teacher.class_sessions:
            print("No classes assigned.")
            input("Press Enter to continue...")
            return
        
        print("Select section:")
        for i, section in enumerate(teacher.class_sessions, 1):
            print(f"{i}. {section}")
        
        choice = safe_int_input("\nSelect section: ", 1, len(teacher.class_sessions))
        if choice is None:
            return
        
        section = teacher.class_sessions[choice - 1]
        section_students = self.student_mgr.get_students_by_section(section)
        
        if not section_students:
            print("No students in this section.")
            input("Press Enter to continue...")
            return
        
        print(f"\nStudents in {section}:")
        for i, student in enumerate(section_students, 1):
            print(f"{i}. {student.name} ({student.student_id})")
        
        choice = safe_int_input("\nSelect student: ", 1, len(section_students))
        if choice is None:
            return
        
        student = section_students[choice - 1]
        subjects = self.student_mgr.get_student_subjects(student.student_id)
        
        if not subjects:
            print("Student not enrolled in any subjects.")
            input("Press Enter to continue...")
            return
        
        print(f"\nSubjects:")
        for i, subject in enumerate(subjects, 1):
            print(f"{i}. {subject}")
        
        choice = safe_int_input("\nSelect subject: ", 1, len(subjects))
        if choice is None:
            return
        
        subject = subjects[choice - 1]
        
        print(f"\nRecord attendance for {student.name} in {subject}:")
        status = safe_string_input("Status (present/absent/tardy): ").lower()
        
        if status not in ["present", "absent", "tardy"]:
            print("Invalid status.")
            input("Press Enter to continue...")
            return
        
        print(f"✓ Attendance recorded: {student.name} - {subject}: {status}")
        input("Press Enter to continue...")
    
    def teacher_change_password(self):

        print_section("CHANGE PASSWORD")
        
        old_password = safe_string_input("Current password: ")
        if not old_password:
            return
        
        account_key = f"teacher_{self.current_id}"
        password_hash = UserAccount.hash_password(old_password)
        
        if self.accounts[account_key]["account"].password_hash != password_hash:
            print("✗ Current password is incorrect.")
            input("Press Enter to continue...")
            return
        
        new_password = safe_string_input("New password: ")
        if not new_password:
            return
        
        confirm = safe_string_input("Confirm new password: ")
        if new_password != confirm:
            print("✗ Passwords do not match.")
            input("Press Enter to continue...")
            return
        
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            print(f"✗ {error_msg}")
            input("Press Enter to continue...")
            return
        
        new_hash = UserAccount.hash_password(new_password)
        self.accounts[account_key]["account"].password_hash = new_hash
        self._save_accounts()
        
        print("✓ Password changed successfully.")
        input("Press Enter to continue...")

    def teacher_view_evaluations(self):

        print_section("MY EVALUATIONS")
        evals = self.eval_mgr.get_evaluations_for_teacher(self.current_id)

        if not evals:
            print("\nNo evaluations yet.")
            input("Press Enter to continue...")
            return

        avg = self.eval_mgr.get_average_rating(self.current_id)
        print(f"\nTotal evaluations: {len(evals)}")
        if avg is not None:
            print(f"Average rating: {avg:.2f}")

        print("\nRecent evaluations:")
        for e in sorted(evals, key=lambda x: x.date, reverse=True):
            print(f"\nDate: {e.date}")
            print(f"From: {e.student_id}")
            print(f"Rating: {e.rating}")
            if e.comment:
                print(f"Comment: {e.comment}")

        input("\nPress Enter to continue...")

        clear_screen()
        print_header(f"PARENT PORTAL - {self.current_user}")
        print(f"\nParent ID: {self.current_id}")
        
        parent = self.comm_mgr.get_parent(self.current_id)
        if parent:
            print(f"Children: {len(parent.student_ids)}")
        
        print("\n1. View Child's Information")
        print("2. View Grades & Attendance")
        print("3. View Fee Balance")
        print("4. View Exam Schedules")
        print("5. View Disciplinary Records")
        print("6. View Academic History")
        print("7. View Notifications")
        print("8. Request Meeting with Teacher")
        print("9. Send Message to Teacher/Staff")
        print("10. Change Password")
        print("0. Logout")
        print("\n" + "-" * 60)
    
    def parent_view_child_info(self):

        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        if len(parent.student_ids) == 1:
            student_id = parent.student_ids[0]
        else:
            print("\nYour Children:")
            for i, sid in enumerate(parent.student_ids, 1):
                student = self.student_mgr.get_student(sid)
                if student:
                    print(f"{i}. {student.name} ({sid})")
            
            choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
            if choice is None:
                return
            
            student_id = parent.student_ids[choice - 1]
        
        student = self.student_mgr.get_student(student_id)
        
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"CHILD'S INFORMATION - {student.name}")
        print(f"\nStudent ID: {student.student_id}")
        print(f"Section: {student.section}")
        print(f"Status: {student.enrollment_status}")
        print(f"Contact on file: {student.contact}")
        
        if student.subjects:
            print(f"\nEnrolled Subjects: {len(student.subjects)}")
            for subject in student.subjects.keys():
                print(f"  - {subject}")
        
        input("\nPress Enter to continue...")
    
    def parent_view_academics(self):

        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        if len(parent.student_ids) == 1:
            student_id = parent.student_ids[0]
        else:
            print("\nYour Children:")
            for i, sid in enumerate(parent.student_ids, 1):
                student = self.student_mgr.get_student(sid)
                if student:
                    print(f"{i}. {student.name} ({sid})")
            
            choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
            if choice is None:
                return
            
            student_id = parent.student_ids[choice - 1]
        
        student = self.student_mgr.get_student(student_id)
        
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"ACADEMIC RECORDS - {student.name}")
        
        subjects = self.student_mgr.get_student_subjects(student_id)
        
        if not subjects:
            print("\nStudent not enrolled in any subjects yet.")
            input("Press Enter to continue...")
            return
        
        print("\nSubject Grades & Attendance:")
        print("-" * 60)
        
        for subject in subjects:
            grade = self.student_mgr.get_subject_grade(student_id, subject)
            attendance = self.student_mgr.get_attendance(student_id, subject)
            
            print(f"\n{subject}:")
            
            if grade is not None:
                print(f"  Grade: {grade:.2f}")
            
            if attendance:
                summary = self.student_mgr.get_attendance_summary(student_id, subject)
                total = len(attendance)
                attendance_pct = (summary['present'] / total * 100) if total > 0 else 0
                print(f"  Attendance: {summary['present']}/{total} ({attendance_pct:.1f}%)")
        
        gpa = self.student_mgr.get_gpa(student_id)
        if gpa is not None:
            print(f"\n{'=' * 60}")
            print(f"Overall GPA: {gpa:.2f}")
        
        input("\nPress Enter to continue...")
    
    def parent_view_fee_balance(self):

        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("FEE BALANCE")
        
        total_balance = 0.0
        
        for i, student_id in enumerate(parent.student_ids, 1):
            student = self.student_mgr.get_student(student_id)
            if student:
                print(f"\n{i}. {student.name} ({student_id})")
                
                invoices = self.fee_mgr.get_student_invoices(student_id)
                
                if not invoices:
                    print("   No invoices generated")
                    continue
                
                student_balance = 0.0
                for invoice in invoices:
                    total_paid = self.fee_mgr.get_total_paid(invoice.invoice_id)
                    balance = invoice.amount - total_paid
                    student_balance += balance
                
                if student_balance > 0:
                    print(f"   Fee Balance: ₨ {student_balance:,.2f}")
                else:
                    print(f"   Fee Balance: ₨ 0 (All fees paid)")
                
                total_balance += student_balance
        
        if parent.student_ids:
            print(f"\n{'=' * 60}")
            if total_balance > 0:
                print(f"Total Family Balance: ₨ {total_balance:,.2f}")
            else:
                print(f"Total Family Balance: ₨ 0 (All fees paid)")
        
        input("\nPress Enter to continue...")
    
    def parent_view_notifications(self):

        notifications = self.comm_mgr.get_parent_notifications(self.current_id)
        
        if not notifications:
            print("\nNo notifications yet.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("NOTIFICATIONS")
        
        notifications_sorted = sorted(notifications, key=lambda n: n.sent_date, reverse=True)
        
        print(f"\nYou have {len(notifications)} notification(s)")
        print(f"Unread: {sum(1 for n in notifications if not n.read)}")
        print("\nRecent Notifications:")
        print("-" * 60)
        
        for i, notif in enumerate(notifications_sorted[:10], 1):
            status = "[NEW]" if not notif.read else "[READ]"
            print(f"\n{i}. {status} {notif.subject}")
            print(f"   Type: {notif.notification_type}")
            print(f"   Date: {notif.sent_date}")
        
        if len(notifications_sorted) > 10:
            print(f"\n... and {len(notifications_sorted) - 10} more")
        
        input("\nPress Enter to continue...")
    
    def parent_request_meeting(self):

        print_section("REQUEST MEETING WITH TEACHER")
        
        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        print("For which child?")
        for i, student_id in enumerate(parent.student_ids, 1):
            student = self.student_mgr.get_student(student_id)
            if student:
                print(f"{i}. {student.name}")
        
        choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
        if choice is None:
            return
        
        student_id = parent.student_ids[choice - 1]
        student = self.student_mgr.get_student(student_id)
        
        subject = safe_string_input(f"\nPurpose of meeting: ")
        if not subject:
            return
        
        message = safe_string_input("Brief description: ")
        
        teachers = self.teacher_mgr.list_teachers()
        if teachers:
            notif_msg = f"{parent.name} (Parent of {student.name}) has requested a meeting.\n\nPurpose: {subject}\n\nDescription: {message}"
            print(f"✓ Meeting request sent to all teachers")
        else:
            print(f"✗ No teachers available in the system")
        
        input("Press Enter to continue...")
    
    def parent_send_message(self):

        print_section("SEND MESSAGE TO TEACHER/STAFF")
        
        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        print("Message regarding which child?")
        for i, student_id in enumerate(parent.student_ids, 1):
            student = self.student_mgr.get_student(student_id)
            if student:
                print(f"{i}. {student.name}")
        
        choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
        if choice is None:
            return
        
        student_id = parent.student_ids[choice - 1]
        
        student = self.student_mgr.get_student(student_id)
        teachers = self.teacher_mgr.list_teachers()
        
        if not teachers:
            print("\nNo teachers available in the system.")
            input("Press Enter to continue...")
            return
        
        print(f"\nTeachers in System:")
        for i, teacher in enumerate(teachers, 1):
            print(f"{i}. {teacher.name}")
        
        choice = safe_int_input("\nSelect recipient: ", 1, len(teachers))
        if choice is None:
            return
        
        teacher = teachers[choice - 1]
        
        message = safe_string_input("\nEnter your message: ")
        if not message:
            return
        
        print(f"\n✓ Message sent to {teacher.name}")
        print("Teacher will receive a notification about your inquiry.")
        input("Press Enter to continue...")
    
    def parent_view_exam_schedules(self):
        """View child's exam schedules"""
        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        if len(parent.student_ids) == 1:
            student_id = parent.student_ids[0]
        else:
            print("\nYour Children:")
            for i, sid in enumerate(parent.student_ids, 1):
                student = self.student_mgr.get_student(sid)
                if student:
                    print(f"{i}. {student.name} ({sid})")
            
            choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
            if choice is None:
                return
            
            student_id = parent.student_ids[choice - 1]
        
        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"EXAM SCHEDULES - {student.name}")
        
        exams = self.exam_mgr.get_schedules_by_section(student.section)
        
        if not exams:
            print(f"\nNo exam schedules found for section {student.section}.")
            input("Press Enter to continue...")
            return
        
        print(f"\nSection: {student.section}")
        print(f"Total Exams: {len(exams)}\n")
        
        for exam in sorted(exams, key=lambda e: e.exam_date):
            print(f"Subject: {exam.subject}")
            print(f"  Type: {exam.exam_type.capitalize()}")
            print(f"  Date: {exam.exam_date}")
            print(f"  Time: {exam.start_time} - {exam.end_time}")
            print(f"  Room: {exam.room}")
            print()
        
        input("Press Enter to continue...")
    
    def parent_view_disciplinary_records(self):
        """View child's disciplinary records and commendations"""
        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        if len(parent.student_ids) == 1:
            student_id = parent.student_ids[0]
        else:
            print("\nYour Children:")
            for i, sid in enumerate(parent.student_ids, 1):
                student = self.student_mgr.get_student(sid)
                if student:
                    print(f"{i}. {student.name} ({sid})")
            
            choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
            if choice is None:
                return
            
            student_id = parent.student_ids[choice - 1]
        
        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"DISCIPLINARY RECORDS & COMMENDATIONS - {student.name}")
        
        records = self.discipline_mgr.get_student_records(student_id)
        disciplines = self.discipline_mgr.get_student_disciplines(student_id)
        commendations = self.discipline_mgr.get_student_commendations(student_id)
        
        print(f"\nDisciplinary Records: {len(disciplines)}")
        print(f"Commendations: {len(commendations)}")
        
        if not records:
            print("\n✓ No records found.")
            input("Press Enter to continue...")
            return
        
        print("\n" + "-" * 60)
        
        for record in sorted(records, key=lambda r: r.date, reverse=True):
            if record.action_type == "discipline":
                print(f"\n[DISCIPLINE - {record.severity.upper()}]")
            else:
                print(f"\n[COMMENDATION]")
            
            print(f"Date: {record.date}")
            print(f"Description: {record.description}")
            if record.status == "resolved":
                print(f"Status: RESOLVED")
                if record.resolution_notes:
                    print(f"Resolution: {record.resolution_notes}")
            print()
        
        input("Press Enter to continue...")
    
    def parent_view_academic_history(self):
        """View child's academic history"""
        parent = self.comm_mgr.get_parent(self.current_id)
        
        if not parent or not parent.student_ids:
            print("\nNo children linked to your account.")
            input("Press Enter to continue...")
            return
        
        if len(parent.student_ids) == 1:
            student_id = parent.student_ids[0]
        else:
            print("\nYour Children:")
            for i, sid in enumerate(parent.student_ids, 1):
                student = self.student_mgr.get_student(sid)
                if student:
                    print(f"{i}. {student.name} ({sid})")
            
            choice = safe_int_input("\nSelect child: ", 1, len(parent.student_ids))
            if choice is None:
                return
            
            student_id = parent.student_ids[choice - 1]
        
        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"ACADEMIC HISTORY - {student.name}")
        
        history = self.archive_mgr.get_student_history(student_id)
        
        if not history:
            print("\nNo academic history available yet.")
            input("Press Enter to continue...")
            return
        
        print(f"\nTotal Snapshots: {len(history)}\n")
        
        for i, snapshot in enumerate(sorted(history, key=lambda s: s.snapshot_date, reverse=True), 1):
            print(f"{i}. {snapshot.semester.upper()} - {snapshot.snapshot_date}")
            print(f"   GPA: {snapshot.gpa:.2f if snapshot.gpa else 'N/A'}")
            print(f"   Subjects: {len(snapshot.subjects_data)}")
            print()
        
        input("Press Enter to continue...")
    
    def parent_change_password(self):

        print_section("CHANGE PASSWORD")
        
        old_password = safe_string_input("Current password: ")
        if not old_password:
            return
        
        account_key = f"parent_{self.current_id}"
        password_hash = UserAccount.hash_password(old_password)
        
        if self.accounts[account_key]["account"].password_hash != password_hash:
            print("✗ Current password is incorrect.")
            input("Press Enter to continue...")
            return
        
        new_password = safe_string_input("New password: ")
        if not new_password:
            return
        
        confirm = safe_string_input("Confirm new password: ")
        if new_password != confirm:
            print("✗ Passwords do not match.")
            input("Press Enter to continue...")
            return
        
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            print(f"✗ {error_msg}")
            input("Press Enter to continue...")
            return
        
        new_hash = UserAccount.hash_password(new_password)
        self.accounts[account_key]["account"].password_hash = new_hash
        self._save_accounts()
        
        print("✓ Password changed successfully.")
        input("Press Enter to continue...")

    def run(self):

        while True:
            choice = self.show_auth_menu()
            
            if choice == "1":
                if self.login():
                    print(f"\n✓ Welcome, {self.current_user}!")
                    input("Press Enter to continue...")
                    self._run_role_portal()
            elif choice == "2":
                self.create_account()
            elif choice == "0":
                print("\n✓ Thank you for using the portal. Goodbye!")
                break
            else:
                print("Invalid option.")
                input("Press Enter to continue...")
    
    def _run_role_portal(self):

        if self.current_role == "student":
            self._run_student_portal()
        elif self.current_role == "teacher":
            self._run_teacher_portal()
        elif self.current_role == "parent":
            self._run_parent_portal()
    
    def _run_student_portal(self):

        while True:
            self.student_main_menu()
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                self.current_user = None
                self.current_role = None
                self.current_id = None
                break
            elif choice == "1":
                self.student_view_info()
            elif choice == "2":
                self.student_view_grades()
            elif choice == "3":
                self.student_view_attendance()
            elif choice == "4":
                self.student_view_discipline()
            elif choice == "5":
                self.student_view_exam_schedules()
            elif choice == "6":
                self.student_view_academic_history()
            elif choice == "7":
                self.student_change_password()
            elif choice == "8":
                self.student_evaluate_teacher()
            else:
                print("Invalid option.")
                input("Press Enter to continue...")
    
    def _run_teacher_portal(self):

        while True:
            self.teacher_main_menu()
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                self.current_user = None
                self.current_role = None
                self.current_id = None
                break
            elif choice == "1":
                self.teacher_view_schedule()
            elif choice == "2":
                self.teacher_input_grades()
            elif choice == "3":
                self.teacher_input_attendance()
            elif choice == "4":
                self.teacher_change_password()
            elif choice == "5":
                self.teacher_view_evaluations()
            else:
                print("Invalid option.")
                input("Press Enter to continue...")
    
    def _run_parent_portal(self):

        while True:
            self.parent_main_menu()
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                self.current_user = None
                self.current_role = None
                self.current_id = None
                break
            elif choice == "1":
                self.parent_view_child_info()
            elif choice == "2":
                self.parent_view_academics()
            elif choice == "3":
                self.parent_view_fee_balance()
            elif choice == "4":
                self.parent_view_exam_schedules()
            elif choice == "5":
                self.parent_view_disciplinary_records()
            elif choice == "6":
                self.parent_view_academic_history()
            elif choice == "7":
                self.parent_view_notifications()
            elif choice == "8":
                self.parent_request_meeting()
            elif choice == "9":
                self.parent_send_message()
            elif choice == "10":
                self.parent_change_password()
            else:
                print("Invalid option.")
                input("Press Enter to continue...")

if __name__ == "__main__":
    portal = UserPortal()
    try:
        portal.run()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        input("Press Enter to continue...")
