

import sys
import os
from utils import (
    clear_screen, print_header, print_section, safe_string_input, safe_int_input, safe_float_input,
    display_page, get_full_name, STUDENTS_FILE, TEACHERS_FILE, COURSES_FILE
)
from auth import setup_first_admin, admin_login_prompt, AuthManager
from student_management import StudentManager
from teacher_management import TeacherManager
from fee_management import FeeManager
from communication import CommunicationManager

class CourseManager:
    
    def __init__(self):
        import pickle
        self.courses_file = COURSES_FILE
        try:
            with open(self.courses_file, "rb") as f:
                self.courses = pickle.load(f)
        except:
            self.courses = {}
    
    def save_courses(self):
        import pickle
        os.makedirs("data", exist_ok=True)
        with open(self.courses_file, "wb") as f:
            pickle.dump(self.courses, f)
    
    def create_course(self, code: str, name: str, description: str = "") -> tuple:
        if code in self.courses:
            return False, "Course code already exists"
        
        self.courses[code] = {
            "name": name,
            "description": description,
            "sections": {}  
        }
        self.save_courses()
        return True, f"Course {code} created"
    
    def create_section(self, course_code: str, year: int) -> tuple:
        if course_code not in self.courses:
            return False, "Course not found"
        
        if year < 1 or year > 4:
            return False, "Year must be between 1-4"
        
        year_str = str(year)
        if year_str not in self.courses[course_code]["sections"]:
            self.courses[course_code]["sections"][year_str] = {}
        
        existing_sections = self.courses[course_code]["sections"][year_str]
        section_num = len(existing_sections) + 1
        
        section_key = str(section_num)
        self.courses[course_code]["sections"][year_str][section_key] = {
            "subjects": [],
            "students": [],
            "schedules": []  
        }
        self.save_courses()
        return True, f"Section {section_num} created for {course_code} Year {year}"
    
    def get_section(self, course_code: str, year: int, section_num: int) -> dict:
        if course_code not in self.courses:
            return None
        
        year_str = str(year)
        section_key = str(section_num)
        
        if year_str not in self.courses[course_code]["sections"]:
            return None
        
        return self.courses[course_code]["sections"][year_str].get(section_key)
    
    def list_courses(self) -> list:
   
        return list(self.courses.items())
    
    def add_subject_to_section(self, course_code: str, year: int, section_num: int,
                              subject: str) -> tuple:
      
        section = self.get_section(course_code, year, section_num)
        if section is None:
            return False, "Section not found"
        
        if subject in section["subjects"]:
            return False, "Subject already exists in section"
        
        section["subjects"].append(subject)
        self.save_courses()
        return True, f"Subject {subject} added to section"
    
    def add_subject_to_year(self, course_code: str, year: int, subject: str) -> tuple:

        if course_code not in self.courses:
            return False, "Course not found"
        
        year_str = str(year)
        if year_str not in self.courses[course_code]["sections"]:
            return False, f"No sections found for {course_code} Year {year}"
        
        sections = self.courses[course_code]["sections"][year_str]
        if not sections:
            return False, f"No sections found for {course_code} Year {year}"
        
        added_count = 0
        for section_num, section in sections.items():
            if subject not in section["subjects"]:
                section["subjects"].append(subject)
                added_count += 1
        
        self.save_courses()
        return True, f"Subject {subject} added to {added_count} section(s) in {course_code} Year {year}"
    
    def check_section_scheduling_conflict(self, course_code: str, year: int, section_num: int,
                                          day: str, start_time: str, end_time: str) -> tuple:

        section = self.get_section(course_code, year, section_num)
        if section is None:
            return False, ""
        
        schedules = section.get("schedules", [])
        
        try:
            new_start = int(start_time.split(":")[0]) * 60 + int(start_time.split(":")[1])
            new_end = int(end_time.split(":")[0]) * 60 + int(end_time.split(":")[1])
        except (ValueError, IndexError):
            return False, ""
        
        for sched in schedules:
            if sched.get("day") != day:
                continue
            
            try:
                existing_start = int(sched.get("start_time", "").split(":")[0]) * 60 + int(sched.get("start_time", "").split(":")[1])
                existing_end = int(sched.get("end_time", "").split(":")[0]) * 60 + int(sched.get("end_time", "").split(":")[1])
            except (ValueError, IndexError):
                continue
            
            if not (new_end <= existing_start or new_start >= existing_end):
                return True, f"Section has a conflict: {sched.get('subject')} at {sched.get('start_time')}-{sched.get('end_time')} on {day}"
        
        return False, ""

class AdminPortal:

    def __init__(self):
        self.student_mgr = StudentManager()
        self.teacher_mgr = TeacherManager()
        self.fee_mgr = FeeManager()
        self.comm_mgr = CommunicationManager()
        self.course_mgr = CourseManager()
        self.auth = AuthManager()
        self.admin_id = None
        self.admin_username = None
    
    def login(self) -> bool:

        if not self.auth.admin_exists():
            print("\n✓ No admin account found. Setting up first admin account...\n")
            success, result = setup_first_admin()
            if not success:
                print(f"✗ Setup failed: {result}")
                return False
            self.admin_id = result
            return True
        
        self.admin_id = admin_login_prompt()
        
        if self.admin_id is None:
            return False
        
        return True
    
    def show_main_menu(self):

        clear_screen()
        print_header("COLLEGE ACADEMIC MANAGEMENT SYSTEM - ADMIN PORTAL")
        print("\n1. Student & Academic Management")
        print("2. Teacher & Timetable Management")
        print("3. Fee & Finance Management")
        print("4. Course & Section Management")
        print("5. Parent & Communication Portal")
        print("6. System Settings")
        print("0. Logout")
        print("\n" + "-" * 60)
    
    def get_student_subjects_from_section(self, student_id: str):

        student = self.student_mgr.get_student(student_id)
        if not student:
            return []
        
        section_parts = student.section.split('-')
        if len(section_parts) != 3:
            return []
        
        try:
            course_code = section_parts[0]
            year = int(section_parts[1])
            section_num = int(section_parts[2])
            
            section = self.course_mgr.get_section(course_code, year, section_num)
            if section is None:
                return []
            
            return section.get("subjects", [])
        except (ValueError, TypeError):
            return []
    
    def student_menu(self):

        while True:
            clear_screen()
            print_header("STUDENT & ACADEMIC MANAGEMENT")
            print("\n1. Create Student")
            print("2. View All Students")
            print("3. View Student Details")
            print("0. Back to Main Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.create_student()
            elif choice == "2":
                self.view_all_students_and_manage()
            elif choice == "3":
                self.view_student_details_and_manage()
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
    
    def view_all_students_and_manage(self):

        students = self.student_mgr.list_students()
        
        if not students:
            print("\nNo students found.")
            input("Press Enter to continue...")
            return
        
        page = 1
        items_per_page = 9
        while True:
            clear_screen()
            print_header("ALL STUDENTS")
            
            items = [f"{s.student_id} - {s.name} ({s.section})" for s in students]
            page, selected = display_page(items, page, "Students")
            
            if selected == -1:
                break
            
            if selected is not None:
                start_idx = (page - 1) * items_per_page
                global_idx = start_idx + selected
                
                if 0 <= global_idx < len(students):
                    student_id = students[global_idx].student_id
                    self.student_operations_menu(student_id)

    def view_student_details_and_manage(self):

        student_id = safe_string_input("Enter student ID: ")
        if not student_id:
            return
        
        student = self.student_mgr.get_student(student_id)
        
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        self.display_student_details(student)
        self.student_operations_menu(student_id)
    
    def display_student_details(self, student):

        clear_screen()
        print_header(f"STUDENT DETAILS - {student.name}")
        print(f"\nID: {student.student_id}")
        print(f"Name: {student.name}")
        print(f"Contact: {student.contact}")
        print(f"Section: {student.section}")
        print(f"Status: {student.enrollment_status}")
        print(f"\nSubjects Enrolled: {len(student.subjects)}")
        
        if student.subjects:
            print("\nSubjects:")
            for subject in student.subjects.keys():
                grade = self.student_mgr.get_subject_grade(student.student_id, subject)
                if grade is not None:
                    print(f"  - {subject}: {grade:.2f}")
                else:
                    print(f"  - {subject}: No grade yet")
        
        gpa = self.student_mgr.get_gpa(student.student_id)
        if gpa:
            print(f"\nGPA: {gpa:.2f}")
        
        input("\nPress Enter to continue...")
    
    def student_operations_menu(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            return
        
        while True:
            clear_screen()
            print_header(f"MANAGE STUDENT - {student.name}")
            print(f"ID: {student.student_id}")
            print(f"Section: {student.section}")
            print("\n1. Manage Student Subjects")
            print("2. Mark Attendance")
            print("3. Record Grades & Exams")
            print("4. View Grades & GPA")
            print("5. View Attendance")
            print("6. Update Student Info")
            print("7. Delete Student")
            print("0. Back to Student Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.manage_student_subjects(student_id)
            elif choice == "2":
                self.mark_attendance(student_id)
            elif choice == "3":
                self.record_grades(student_id)
            elif choice == "4":
                self.view_grades(student_id)
            elif choice == "5":
                self.view_attendance(student_id)
            elif choice == "6":
                self.update_student_info(student_id)
            elif choice == "7":
                self.delete_student(student_id)
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
    
    def create_student(self):

        print_section("CREATE NEW STUDENT")
        
        name = get_full_name()
        if not name:
            return
        
        contact = safe_string_input("Contact information (email/phone): ")
        if not contact:
            return
        
        section = safe_string_input("Section (COURSE-YEAR-SECTION, e.g., BSIT-3-1): ")
        if not section:
            return
        
        success, result = self.student_mgr.create_student(name, contact, section)
        
        if success:
            print(f"\n✓ Student created successfully!")
            print(f"Student ID: {result}")
            print(f"Name: {name}")
            print(f"Section: {section}")
            
            print("\nParent/Guardian Information:")
            parent_name = get_full_name()
            if not parent_name:
                print("Parent account creation cancelled.")
                input("Press Enter to continue...")
                return
            parent_email = safe_string_input("Parent email: ")
            parent_phone = safe_string_input("Parent phone: ")
            
            if parent_name and parent_email and parent_phone:
                p_success, parent_id = self.comm_mgr.create_parent_account(
                    parent_name, parent_email, parent_phone, [result]
                )
                if p_success:
                    print(f"✓ Parent account created automatically!")
                    print(f"Parent ID: {parent_id}")
        else:
            print(f"\n✗ Error: {result}")
        
        input("\nPress Enter to continue...")
    
    def view_all_students(self):

        students = self.student_mgr.list_students()
        
        if not students:
            print("\nNo students found.")
            input("Press Enter to continue...")
            return
        
        page = 1
        while True:
            clear_screen()
            print_header("ALL STUDENTS")
            
            items = [f"{s.student_id} - {s.name} ({s.section})" for s in students]
            page, selected = display_page(items, page, "Students")
            
            if selected == -1:
                break
    
    def view_student_details(self):

        student_id = safe_string_input("Enter student ID: ")
        if not student_id:
            return
        
        student = self.student_mgr.get_student(student_id)
        
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"STUDENT DETAILS - {student.name}")
        print(f"\nID: {student.student_id}")
        print(f"Name: {student.name}")
        print(f"Contact: {student.contact}")
        print(f"Section: {student.section}")
        print(f"Status: {student.enrollment_status}")
        print(f"\nSubjects Enrolled: {len(student.subjects)}")
        
        if student.subjects:
            print("\nSubjects:")
            for subject in student.subjects.keys():
                grade = self.student_mgr.get_subject_grade(student_id, subject)
                if grade is not None:
                    print(f"  - {subject}: {grade:.2f}")
                else:
                    print(f"  - {subject}: No grade yet")
        
        gpa = self.student_mgr.get_gpa(student_id)
        if gpa:
            print(f"\nGPA: {gpa:.2f}")
        
        input("\nPress Enter to continue...")
    
    def manage_student_subjects(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        section_parts = student.section.split('-')
        if len(section_parts) != 3:
            print("Invalid student section format.")
            input("Press Enter to continue...")
            return
        
        course_code = section_parts[0]
        year = int(section_parts[1])
        section_num = int(section_parts[2])
        
        section = self.course_mgr.get_section(course_code, year, section_num)
        if section is None:
            print(f"Section {student.section} not found in course database.")
            input("Press Enter to continue...")
            return
        
        section_subjects = section.get("subjects", [])
        
        if not section_subjects:
            print(f"\nNo subjects defined for {student.section}.")
            print("Please add subjects to this section in Course Management first.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"SUBJECT MANAGEMENT - {student.name}")
            print(f"Section: {student.section}")
            print(f"\nSection Subjects ({len(section_subjects)} total):")
            
            for i, subject in enumerate(section_subjects, 1):
                if subject in student.exempted_subjects:
                    print(f"{i}. {subject} [EXEMPTED]")
                else:
                    print(f"{i}. {subject}")
            
            print("\n1. Exempt Student from Subject")
            print("2. Remove Subject Exemption")
            print("0. Back")
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                print("\nSelect subject to exempt from:")
                for i, subject in enumerate(section_subjects, 1):
                    status = "[EXEMPTED]" if subject in student.exempted_subjects else ""
                    print(f"{i}. {subject} {status}")
                
                subject_choice = safe_int_input("Subject number (0 to cancel): ", 0, len(section_subjects))
                if subject_choice and subject_choice > 0:
                    subject = section_subjects[subject_choice - 1]
                    success, msg = self.student_mgr.exempt_subject(student_id, subject)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
            
            elif choice == "2":
                exempted = [s for s in section_subjects if s in student.exempted_subjects]
                if not exempted:
                    print("\nNo exempted subjects.")
                    input("Press Enter to continue...")
                    continue
                
                print("\nSelect subject to remove exemption from:")
                for i, subject in enumerate(exempted, 1):
                    print(f"{i}. {subject}")
                
                subject_choice = safe_int_input("Subject number (0 to cancel): ", 0, len(exempted))
                if subject_choice and subject_choice > 0:
                    subject = exempted[subject_choice - 1]
                    success, msg = self.student_mgr.unexempt_subject(student_id, subject)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")

    def mark_attendance(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        subjects = self.get_student_subjects_from_section(student_id)
        
        if not subjects:
            print(f"\n{student.name}'s section ({student.section}) has no subjects defined yet.")
            print("Please add subjects in Course Management first.")
            input("Press Enter to continue...")
            return
        
        available_subjects = [s for s in subjects if s not in student.exempted_subjects]
        
        if not available_subjects:
            print(f"\n{student.name} is exempted from all subjects in their section.")
            input("Press Enter to continue...")
            return
        
        print("\nSubjects in Section:")
        for i, subject in enumerate(available_subjects, 1):
            print(f"{i}. {subject}")
        
        choice = safe_int_input("Select subject number: ", 1, len(available_subjects))
        if choice is None:
            return
        
        subject = available_subjects[choice - 1]
        date = safe_string_input("Date (YYYY-MM-DD): ")
        
        print("\n1. Present")
        print("2. Absent")
        print("3. Tardy")
        
        status_choice = safe_int_input("Mark as: ", 1, 3)
        if status_choice is None:
            return
        
        status_map = {1: "present", 2: "absent", 3: "tardy"}
        status = status_map[status_choice]
        
        success, msg = self.student_mgr.mark_attendance(student_id, subject, date, status)
        print(f"\n{'✓' if success else '✗'} {msg}")
        
        input("Press Enter to continue...")
    
    def record_grades(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        subjects = self.get_student_subjects_from_section(student_id)
        
        if not subjects:
            print(f"\n{student.name} is not enrolled in any subjects.")
            input("Press Enter to continue...")
            return
        
        available_subjects = [s for s in subjects if s not in student.exempted_subjects]
        
        if not available_subjects:
            print(f"\n{student.name} is exempted from all subjects in their section.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"RECORD GRADES - {student.name}")
            print("\nSubjects:")
            for i, subject in enumerate(available_subjects, 1):
                print(f"{i}. {subject}")
            print("0. Back")
            
            choice = safe_int_input("Select subject: ", 0, len(available_subjects))
            if choice is None or choice == 0:
                break
            
            subject = available_subjects[choice - 1]
            
            print(f"\n--- {subject} ---")
            print("1. Record Exam Score (Prelim/Midterm/Finals)")
            print("2. Record Activity")
            print("0. Back to Subject List")
            
            action = safe_string_input("Choose action: ")
            
            if action == "1":
                print("\n1. Prelim")
                print("2. Midterm")
                print("3. Finals")
                
                exam_choice = safe_int_input("Select exam: ", 1, 3)
                if exam_choice is None:
                    continue
                
                exam_map = {1: "prelim", 2: "midterm", 3: "finals"}
                exam_type = exam_map[exam_choice]
                
                score = safe_int_input("Enter score (0-100): ", 0, 100)
                if score is not None:
                    success, msg = self.student_mgr.record_exam(student_id, subject, exam_type, float(score))
                    print(f"{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
            
            elif action == "2":
                total_items = safe_int_input("Total items in activity: ", 1)
                if total_items is None:
                    continue
                
                correct = safe_int_input(f"Correct answers (0-{total_items}): ", 0, total_items)
                if correct is not None:
                    success, msg = self.student_mgr.add_activity(student_id, subject, total_items, correct)
                    print(f"{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
    
    def view_grades(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"GRADES & GPA - {student.name}")
        
        subjects = self.get_student_subjects_from_section(student_id)
        
        if not subjects:
            print("\nStudent's section has no subjects defined yet.")
            input("Press Enter to continue...")
            return
        
        available_subjects = [s for s in subjects if s not in student.exempted_subjects]
        
        print("\nSubject Grades:")
        if available_subjects:
            for subject in available_subjects:
                grade = self.student_mgr.get_subject_grade(student_id, subject)
                if grade is not None:
                    print(f"{subject}: {grade:.2f}")
                else:
                    print(f"{subject}: No grades recorded yet")
        else:
            print("Student is exempted from all subjects in their section.")
        
        gpa = self.student_mgr.get_gpa(student_id)
        if gpa:
            print(f"\nGPA: {gpa:.2f}")
        else:
            print("\nGPA: Not available yet")
        
        input("\nPress Enter to continue...")
    
    def view_attendance(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"ATTENDANCE - {student.name}")
        
        subjects = self.get_student_subjects_from_section(student_id)
        
        if not subjects:
            print("\nStudent's section has no subjects defined yet.")
            input("Press Enter to continue...")
            return
        
        available_subjects = [s for s in subjects if s not in student.exempted_subjects]
        
        if not available_subjects:
            print("\nStudent is exempted from all subjects in their section.")
            input("Press Enter to continue...")
            return
        
        print("\nSelect subject to view attendance:")
        for i, subject in enumerate(available_subjects, 1):
            print(f"{i}. {subject}")
        print("0. Back")
        
        choice = safe_int_input("Choose subject: ", 0, len(available_subjects))
        if choice is None or choice == 0:
            return
        
        subject = available_subjects[choice - 1]
        
        clear_screen()
        print_header(f"ATTENDANCE - {student.name} ({subject})")
        
        attendance = self.student_mgr.get_attendance(student_id, subject)
        
        if not attendance:
            print("\nNo attendance records found for this subject.")
        else:
            print("\nAttendance Records:")
            print("-" * 50)
            print(f"{'Date':<15} {'Status':<15}")
            print("-" * 50)
            for date, status in attendance:
                print(f"{date:<15} {status.capitalize():<15}")
            
            summary = self.student_mgr.get_attendance_summary(student_id, subject)
            if summary:
                print("-" * 50)
                print(f"Present: {summary['present']} | Absent: {summary['absent']} | Tardy: {summary['tardy']}")
        
        input("\nPress Enter to continue...")
    
    def update_student_info(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        print(f"\nCurrent Info:")
        print(f"Name: {student.name}")
        print(f"Contact: {student.contact}")
        print(f"Status: {student.enrollment_status}")
        
        update_name_input = safe_string_input("\nUpdate name? (yes/no, leave empty to skip): ", allow_empty=True)
        
        name = None
        if update_name_input and update_name_input.lower() == "yes":
            name = get_full_name()
        
        contact = safe_string_input("\nContact (leave empty to skip): ", allow_empty=True)
        
        print("\n1. Active")
        print("2. Inactive")
        print("3. Suspended")
        print("0. Skip status update")
        status_choice = safe_int_input("Status (0 to skip): ", 0, 3)
        
        status = None
        if status_choice == 1:
            status = "active"
        elif status_choice == 2:
            status = "inactive"
        elif status_choice == 3:
            status = "suspended"
        
        success, msg = self.student_mgr.update_student(student_id, name, contact, status)
        print(f"\n{'✓' if success else '✗'} {msg}")
        
        input("Press Enter to continue...")
    
    def delete_student(self, student_id):

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        confirm = safe_string_input(f"\nAre you sure you want to delete {student.name}? (yes/no): ")
        
        if confirm and confirm.lower() == "yes":
            success, msg = self.student_mgr.delete_student(student_id)
            print(f"{'✓' if success else '✗'} {msg}")
        else:
            print("Deletion cancelled.")
        
        input("Press Enter to continue...")
    
    def teacher_menu(self):

        while True:
            clear_screen()
            print_header("TEACHER & TIMETABLE MANAGEMENT")
            print("\n1. Create Teacher")
            print("2. View all Teachers")
            print("3. View Teacher Details")
            print("0. Back to Main Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.create_teacher()
            elif choice == "2":
                self.view_and_manage_teachers()
            elif choice == "3":
                self.view_teacher_details_and_manage()
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
    
    def create_teacher(self):

        print_section("CREATE NEW TEACHER")
        
        name = get_full_name()
        if not name:
            return
        
        email = safe_string_input("Email address: ")
        if not email:
            return
        
        phone = safe_string_input("Phone number: ")
        if not phone:
            return
        
        success, result = self.teacher_mgr.create_teacher(name, email, phone)
        
        if success:
            print(f"\n✓ Teacher created successfully!")
            print(f"Teacher ID: {result}")
            print(f"Name: {name}")
        else:
            print(f"\n✗ Error: {result}")
        
        input("\nPress Enter to continue...")
    
    def view_and_manage_teachers(self):

        teachers = self.teacher_mgr.list_teachers()
        
        if not teachers:
            print("\nNo teachers found.")
            input("Press Enter to continue...")
            return
        
        page = 1
        while True:
            clear_screen()
            print_header("ALL TEACHERS")
            
            items = [f"{t.teacher_id} - {t.name} ({t.email})" for t in teachers]
            page, selected = display_page(items, page, "Teachers")
            
            if selected == -1:
                break
            
            if selected is not None:
                teacher_id = teachers[(page - 1) * 9 + selected].teacher_id
                teacher_deleted = self.teacher_operations_menu(teacher_id)
                if teacher_deleted:
                    break
    
    def teacher_operations_menu(self, teacher_id):

        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return False
        
        while True:
            clear_screen()
            print_header(f"MANAGE TEACHER - {teacher.name}")
            print(f"ID: {teacher.teacher_id}")
            print(f"Email: {teacher.email}")
            print(f"Phone: {teacher.phone}")
            print("\n1. View Details")
            print("2. View Subjects")
            print("3. Manage Class Schedule")
            print("4. Update Info")
            print("5. Delete Teacher")
            print("0. Back to Teachers List")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.view_teacher_details(teacher_id)
            elif choice == "2":
                self.view_teacher_subjects_from_schedule(teacher_id)
            elif choice == "3":
                self.manage_class_schedule(teacher_id)
            elif choice == "4":
                self.update_teacher_info(teacher_id)
            elif choice == "5":
                deleted = self.delete_teacher(teacher_id)
                if deleted:
                    return True
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
        
        return False
    
    def view_teacher_details_and_manage(self):

        teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        self.display_teacher_details(teacher)
        self.teacher_operations_menu(teacher_id)
    
    def display_teacher_details(self, teacher):

        clear_screen()
        print_header(f"TEACHER DETAILS - {teacher.name}")
        print(f"\nID: {teacher.teacher_id}")
        print(f"Name: {teacher.name}")
        print(f"Email: {teacher.email}")
        print(f"Phone: {teacher.phone}")
        print(f"\nSubjects Taught: {', '.join(teacher.subjects_taught) if teacher.subjects_taught else 'None'}")
        print(f"Sections Assigned: {len(teacher.class_sessions)}")
        
        if teacher.class_sessions:
            print("\nSections:")
            for section in teacher.class_sessions:
                print(f"  - {section}")
        
        input("\nPress Enter to continue...")
    
    def view_all_teachers(self):

        teachers = self.teacher_mgr.list_teachers()
        
        if not teachers:
            print("\nNo teachers found.")
            input("Press Enter to continue...")
            return
        
        page = 1
        while True:
            clear_screen()
            print_header("ALL TEACHERS")
            
            items = [f"{t.teacher_id} - {t.name} ({t.email})" for t in teachers]
            page, selected = display_page(items, page, "Teachers")
            
            if selected == -1:
                break
    
    def view_teacher_details(self, teacher_id=None):

        if teacher_id is None:
            teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"TEACHER DETAILS - {teacher.name}")
        print(f"\nID: {teacher.teacher_id}")
        print(f"Name: {teacher.name}")
        print(f"Email: {teacher.email}")
        print(f"Phone: {teacher.phone}")
        print(f"\nSubjects Taught: {', '.join(teacher.subjects_taught) if teacher.subjects_taught else 'None'}")
        print(f"Sections Assigned: {len(teacher.class_sessions)}")
        
        if teacher.class_sessions:
            print("\nSections:")
            for section in teacher.class_sessions:
                print(f"  - {section}")
        
        input("\nPress Enter to continue...")
    
    def view_teacher_subjects_from_schedule(self, teacher_id=None):

        if teacher_id is None:
            teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        subjects_set = set()
        for section in teacher.class_sessions:
            schedules = self.teacher_mgr.get_schedules(teacher_id, section)
            if schedules:
                for sched in schedules:
                    subjects_set.add(sched.subject)
        
        clear_screen()
        print_header(f"SUBJECTS - {teacher.name}")
        
        if subjects_set:
            print("\nSubjects Assigned:")
            for i, subject in enumerate(sorted(subjects_set), 1):
                print(f"{i}. {subject}")
        else:
            print("\nNo subjects assigned yet. Teacher has no class schedules.")
        
        input("\nPress Enter to continue...")
    
    def manage_teacher_subjects(self, teacher_id=None):

        if teacher_id is None:
            teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"MANAGE SUBJECTS - {teacher.name}")
            print("\n1. Add Subject")
            print("2. View Subjects")
            print("0. Back")
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                subject = safe_string_input("Subject name: ")
                if subject:
                    success, msg = self.teacher_mgr.add_subject(teacher_id, subject)
                    print(f"{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
            elif choice == "2":
                subjects = self.teacher_mgr.get_subjects(teacher_id)
                if subjects:
                    print("\nSubjects Taught:")
                    for i, subject in enumerate(subjects, 1):
                        print(f"{i}. {subject}")
                else:
                    print("\nNo subjects assigned yet.")
                input("Press Enter to continue...")
    
    def assign_section_to_teacher(self):

        teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        section = safe_string_input("Section to assign (COURSE-YEAR-SECTION, e.g., BSIT-3-1): ")
        if section:
            success, msg = self.teacher_mgr.assign_section(teacher_id, section)
            print(f"\n{'✓' if success else '✗'} {msg}")
        
        input("Press Enter to continue...")
    
    def manage_class_schedule(self, teacher_id=None):

        if teacher_id is None:
            teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"MANAGE SCHEDULE - {teacher.name}")
            print("\n1. Add Schedule for a Section")
            print("2. View Schedules")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                section = safe_string_input("Section (COURSE-YEAR-SECTION, e.g., BSIT-3-1): ")
                if not section:
                    continue
                
                section_parts = section.split("-")
                if len(section_parts) != 3:
                    print("\n✗ Invalid section format. Use COURSE-YEAR-SECTION (e.g., BSIT-3-1)")
                    input("Press Enter to continue...")
                    continue
                
                course_code, year_str, section_num = section_parts
                try:
                    year = int(year_str)
                    section_num = int(section_num)
                except ValueError:
                    print("\n✗ Invalid section format. Year and section number must be numbers.")
                    input("Press Enter to continue...")
                    continue
                
                section_obj = self.course_mgr.get_section(course_code, year, section_num)
                if section_obj is None:
                    print(f"\n✗ Section {section} not found.")
                    input("Press Enter to continue...")
                    continue
                
                available_subjects = section_obj.get("subjects", [])
                if not available_subjects:
                    print(f"\n✗ No subjects defined for section {section}.")
                    input("Press Enter to continue...")
                    continue
                
                clear_screen()
                print_header(f"SELECT SUBJECT - {section}")
                print("\nAvailable Subjects:")
                for i, subj in enumerate(available_subjects, 1):
                    print(f"{i}. {subj}")
                print("0. Back")
                
                subject_choice = safe_int_input("Select subject: ", 0, len(available_subjects))
                if subject_choice is None or subject_choice == 0:
                    continue
                
                subject = available_subjects[subject_choice - 1]
                
                print("\nDay of week:")
                print("1. Monday")
                print("2. Tuesday")
                print("3. Wednesday")
                print("4. Thursday")
                print("5. Friday")
                print("6. Saturday")
                
                day_choice = safe_int_input("Select day: ", 1, 6)
                if day_choice is None:
                    continue
                
                day_map = {1: "Monday", 2: "Tuesday", 3: "Wednesday",
                           4: "Thursday", 5: "Friday", 6: "Saturday"}
                day = day_map[day_choice]
                
                start_time = safe_string_input("Start time (HH:MM): ")
                if not start_time:
                    continue
                
                end_time = safe_string_input("End time (HH:MM): ")
                if not end_time:
                    continue
                
                room = safe_string_input("Room/Location: ")
                if not room:
                    continue
                
                has_conflict, conflict_msg = self.course_mgr.check_section_scheduling_conflict(
                    course_code, year, section_num, day, start_time, end_time
                )
                if has_conflict:
                    print(f"\n✗ {conflict_msg}")
                    input("Press Enter to continue...")
                    continue
                
                success, msg = self.teacher_mgr.add_schedule(teacher_id, section, subject,
                                                             day, start_time, end_time, room)
                if success:
                    section_obj = self.course_mgr.get_section(course_code, year, section_num)
                    if section_obj:
                        if "schedules" not in section_obj:
                            section_obj["schedules"] = []
                        section_obj["schedules"].append({
                            "subject": subject,
                            "day": day,
                            "start_time": start_time,
                            "end_time": end_time,
                            "room": room
                        })
                        self.course_mgr.save_courses()
                
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                sections = self.teacher_mgr.get_sections(teacher_id)
                if not sections:
                    print(f"\n{teacher.name} has no schedules yet.")
                    input("Press Enter to continue...")
                    continue
                
                while True:
                    clear_screen()
                    print_header(f"SCHEDULES - {teacher.name}")
                    print("\nSections with Schedules:")
                    for i, section in enumerate(sections, 1):
                        schedules = self.teacher_mgr.get_schedules(teacher_id, section)
                        schedule_count = len(schedules) if schedules else 0
                        print(f"{i}. {section} ({schedule_count} class(es))")
                    print("0. Back")
                    
                    sec_choice = safe_int_input("Select section to view: ", 0, len(sections))
                    if sec_choice is None or sec_choice == 0:
                        break
                    
                    section = sections[sec_choice - 1]
                    
                    while True:
                        clear_screen()
                        print_header(f"SCHEDULE - {section}")
                        schedules = self.teacher_mgr.get_schedules(teacher_id, section)
                        
                        if schedules:
                            print("\nClass Schedule:")
                            for i, sched in enumerate(schedules, 1):
                                print(f"{i}. {sched.subject} - {sched.day} {sched.start_time}-{sched.end_time} ({sched.room})")
                            
                            print("\n1. Remove Schedule")
                            print("0. Back")
                            
                            action = safe_string_input("Choose option: ")
                            
                            if action == "0":
                                break
                            elif action == "1":
                                idx = safe_int_input("Select schedule to remove: ", 1, len(schedules))
                                if idx:
                                    schedule_to_remove = schedules[idx - 1]
                                    
                                    success, msg = self.teacher_mgr.remove_schedule(teacher_id, section, idx - 1)
                                    if success:
                                        section_parts = section.split("-")
                                        if len(section_parts) == 3:
                                            try:
                                                course_code, year_str, section_num = section_parts
                                                year = int(year_str)
                                                section_num = int(section_num)
                                                section_obj = self.course_mgr.get_section(course_code, year, section_num)
                                                if section_obj and "schedules" in section_obj:
                                                    section_obj["schedules"] = [
                                                        s for s in section_obj["schedules"]
                                                        if not (s.get("subject") == schedule_to_remove.subject and
                                                                s.get("day") == schedule_to_remove.day and
                                                                s.get("start_time") == schedule_to_remove.start_time and
                                                                s.get("end_time") == schedule_to_remove.end_time)
                                                    ]
                                                    self.course_mgr.save_courses()
                                            except (ValueError, IndexError):
                                                pass
                                    
                                    print(f"\n{'✓' if success else '✗'} {msg}")
                                    input("Press Enter to continue...")
                                    break
                        else:
                            print("\nNo schedules for this section.")
                            input("Press Enter to continue...")
                            break
    
    def update_teacher_info(self, teacher_id=None):

        if teacher_id is None:
            teacher_id = safe_string_input("Enter teacher ID: ")
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        print(f"\nCurrent Info:")
        print(f"Name: {teacher.name}")
        print(f"Email: {teacher.email}")
        print(f"Phone: {teacher.phone}")
        
        update_name_input = safe_string_input("\nUpdate name? (yes/no, leave empty to skip): ", allow_empty=True)
        
        name = None
        if update_name_input and update_name_input.lower() == "yes":
            name = get_full_name()
        
        email = safe_string_input("\nNew email (leave empty to skip): ", allow_empty=True)
        phone = safe_string_input("New phone (leave empty to skip): ", allow_empty=True)
        
        success, msg = self.teacher_mgr.update_teacher(teacher_id, name, email, phone)
        print(f"\n{'✓' if success else '✗'} {msg}")
        
        input("Press Enter to continue...")
    
    def delete_teacher(self, teacher_id=None):

        if teacher_id is None:
            teacher_id = safe_string_input("Enter teacher ID to delete: ")
        if not teacher_id:
            return False
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return False
        
        confirm = safe_string_input(f"\nAre you sure you want to delete {teacher.name}? (yes/no): ")
        
        if confirm and confirm.lower() == "yes":
            success, msg = self.teacher_mgr.delete_teacher(teacher_id)
            print(f"{'✓' if success else '✗'} {msg}")
            input("Press Enter to continue...")
            return success
        else:
            print("Deletion cancelled.")
            input("Press Enter to continue...")
            return False
    
    def fee_menu(self):

        while True:
            clear_screen()
            print_header("FEE & FINANCE MANAGEMENT")
            print("\n1. Manage Fee Structures")
            print("2. Manage Particulars")
            print("3. Generate Enrollment Invoice")
            print("4. Create Custom Invoice")
            print("5. Record Payment")
            print("6. View Invoices")
            print("7. Manage Payroll")
            print("8. Financial Reports")
            print("0. Back to Main Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.manage_fee_structures()
            elif choice == "2":
                self.manage_particulars()
            elif choice == "3":
                self.generate_enrollment_invoice_for_student()
            elif choice == "4":
                self.create_custom_invoice_single_student()
            elif choice == "5":
                self.record_payment()
            elif choice == "6":
                self.view_invoices()
            elif choice == "7":
                self.manage_payroll()
            elif choice == "8":
                self.financial_reports()
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
    
    def manage_particulars(self):

        while True:
            clear_screen()
            print_header("MANAGE PARTICULARS")
            print("\n1. Create Particular")
            print("2. View All Particulars")
            print("3. Update Particular")
            print("4. Delete Particular")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                name = safe_string_input("\nParticular name (e.g., Library Fee, Athletics Fee): ")
                if not name:
                    continue
                
                amount = safe_int_input("Amount (PHP): ", 1)
                if amount is None:
                    continue
                
                description = safe_string_input("Description (optional): ", allow_empty=True)
                
                success, msg = self.fee_mgr.create_particular(name, float(amount), description)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                particulars = self.fee_mgr.list_particulars()
                if particulars:
                    print("\nAll Particulars:")
                    for particular in particulars:
                        print(f"- {particular.name}: PHP{particular.amount:.2f}")
                        if particular.description:
                            print(f"  ({particular.description})")
                else:
                    print("\nNo particulars found.")
                input("Press Enter to continue...")
            
            elif choice == "3":
                name = safe_string_input("\nParticular name to update: ")
                if not name:
                    continue
                
                amount = safe_int_input("New amount (PHP, leave blank to skip): ", 1)
                description = safe_string_input("New description (leave blank to skip): ")
                
                success, msg = self.fee_mgr.update_particular(name, float(amount) if amount else None, 
                                                               description if description else None)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "4":
                name = safe_string_input("\nParticular name to delete: ")
                if name:
                    confirm = safe_string_input(f"Delete '{name}'? (yes/no): ")
                    if confirm and confirm.lower() == "yes":
                        success, msg = self.fee_mgr.delete_particular(name)
                        print(f"\n{'✓' if success else '✗'} {msg}")
                    else:
                        print("Deletion cancelled.")
                input("Press Enter to continue...")
    
    def manage_fee_structures(self):

        while True:
            clear_screen()
            print_header("FEE STRUCTURES (by COURSE-YEAR)")
            print("\n1. Create Fee Structure for COURSE-YEAR")
            print("2. View All Fee Structures")
            print("3. Configure Fee Structure")
            print("4. Delete Fee Structure")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
        
                courses = self.course_mgr.list_courses()
                options = []
                for code, cdata in courses:
                    sections = cdata.get("sections", {})
                    for year_str, year_sections in sections.items():
                        try:
                            year_int = int(year_str)
                        except ValueError:
                            continue
           
                        if year_sections:
                            options.append((f"{code}-{year_int}", code, year_int))

                if not options:
                    print("\nNo courses/years found. Please create a course and section first.")
                    input("Press Enter to continue...")
                    continue

                page = 1
                chosen = None
                while True:
                    page, selected = display_page([o[0] for o in options], page, "Select COURSE-YEAR")
                    if selected == -1:
                        break
                    if selected is None:
                        continue
                    chosen = options[selected]
                    break

                if chosen is None:
             
                    continue

                course_code = chosen[1]
                year = chosen[2]

                section = self.course_mgr.get_section(course_code, year, 1)
                if section is None:
                    print(f"\n✗ Error: Course {course_code} Year {year} does not exist in the system.")
                    print("Please create the course and enrollment first.")
                    input("Press Enter to continue...")
                    continue

                success, fee_structure = self.fee_mgr.create_fee_structure(course_code, year)
                if success:
                    print(f"\n✓ Fee structure created for {course_code}-{year}")
                else:
                    print(f"\n✗ Error: {fee_structure}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                structures = self.fee_mgr.list_fee_structures()
                if structures:
                    print("\nAll Fee Structures:")
                    for struct in structures:
                        total = self.fee_mgr.calculate_total_fee(struct.course_code, struct.year)
                        print(f"- {struct.course_code}-{struct.year}: PHP{total:.2f}")
                else:
                    print("\nNo fee structures found.")
                input("Press Enter to continue...")
            
            elif choice == "3":
                course_code = safe_string_input("\nCourse code (e.g., BSIT): ")
                if not course_code:
                    continue
                
                year = safe_int_input("Year (1-4): ", 1, 4)
                if year is None:
                    continue
                
                self.configure_fee_structure(course_code, year)
            
            elif choice == "4":
                course_code = safe_string_input("\nCourse code to delete: ")
                if not course_code:
                    continue
                
                year = safe_int_input("Year (1-4): ", 1, 4)
                if year is None:
                    continue
                
                confirm = safe_string_input(f"Delete fee structure for {course_code}-{year}? (yes/no): ")
                if confirm and confirm.lower() == "yes":
                    success, msg = self.fee_mgr.delete_fee_structure(course_code, year)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                else:
                    print("Deletion cancelled.")
                input("Press Enter to continue...")
    
    def configure_fee_structure(self, course_code: str, year: int):

        fee_structure = self.fee_mgr.get_fee_structure(course_code, year)
        if fee_structure is None:
            print("Fee structure not found.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"CONFIGURE FEE STRUCTURE - {course_code}-{year}")
            
            section = self.course_mgr.get_section(course_code, year, 1)
            if section is None:
                print(f"Section {course_code}-{year} not found in course system.")
                input("Press Enter to continue...")
                break
            
            available_subjects = section.get("subjects", [])
            total_fee = self.fee_mgr.calculate_total_fee(course_code, year)
            
            print(f"\nTotal Fee: PHP{total_fee:.2f}")
            print(f"\nConfigured Subjects ({len(fee_structure.subject_fees)}):")
            for subject, fee in fee_structure.subject_fees.items():
                print(f"  - {subject}: PHP{fee.amount:.2f}")
            
            print(f"\nConfigured Particulars ({len(fee_structure.selected_particulars)}):")
            if fee_structure.selected_particulars:
                for particular_name in fee_structure.selected_particulars:
                    particular = self.fee_mgr.get_particular(particular_name)
                    if particular:
                        print(f"  - {particular_name}: PHP{particular.amount:.2f}")
            else:
                print("  (None selected)")
            
            print("\n1. Add/Update Subject Fee")
            print("2. Add Particular")
            print("3. Remove Particular")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                if not available_subjects:
                    print("\nNo subjects available for this section.")
                    input("Press Enter to continue...")
                    continue
                
                print("\nAvailable Subjects:")
                for i, subject in enumerate(available_subjects, 1):
                    print(f"{i}. {subject}")
                
                subject_choice = safe_int_input("Select subject (number): ", 1, len(available_subjects))
                if subject_choice is None:
                    continue
                
                subject = available_subjects[subject_choice - 1]
                amount = safe_int_input(f"Fee for {subject} (PHP): ", 1)
                if amount is None:
                    continue
                
                success, msg = self.fee_mgr.add_subject_fee_to_structure(course_code, year, subject, float(amount))
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                particulars = self.fee_mgr.list_particulars()
                if not particulars:
                    print("\nNo particulars available. Create some first in 'Manage Particulars'.")
                    input("Press Enter to continue...")
                    continue
                
                print("\nAvailable Particulars:")
                for i, particular in enumerate(particulars, 1):
                    status = "✓" if particular.name in fee_structure.selected_particulars else " "
                    print(f"{i}. [{status}] {particular.name}: PHP{particular.amount:.2f}")
                
                particular_choice = safe_int_input("Select particular (number): ", 1, len(particulars))
                if particular_choice is None:
                    continue
                
                particular_name = particulars[particular_choice - 1].name
                
                if particular_name in fee_structure.selected_particulars:
                    print(f"\n'{particular_name}' is already selected.")
                else:
                    success, msg = self.fee_mgr.add_particular_to_structure(course_code, year, particular_name)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                
                input("Press Enter to continue...")
            
            elif choice == "3":
                if not fee_structure.selected_particulars:
                    print("\nNo particulars to remove.")
                    input("Press Enter to continue...")
                    continue
                
                print("\nSelected Particulars:")
                for i, particular_name in enumerate(fee_structure.selected_particulars, 1):
                    print(f"{i}. {particular_name}")
                
                particular_choice = safe_int_input("Select particular to remove (number): ", 
                                                    1, len(fee_structure.selected_particulars))
                if particular_choice is None:
                    continue
                
                particular_name = fee_structure.selected_particulars[particular_choice - 1]
                success, msg = self.fee_mgr.remove_particular_from_structure(course_code, year, particular_name)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
    
    # 'Generate Enrollment Invoice for Section' removed — handler deleted

    def generate_enrollment_invoice_for_student(self):

        student_id = safe_string_input("Enter student ID: ")
        if not student_id:
            return

        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return

        # parse section from student's section value (COURSE-YEAR-SECTION)
        parts = student.section.split("-")
        if len(parts) != 3:
            print("Student section is invalid. Cannot determine course-year.")
            input("Press Enter to continue...")
            return

        course_code = parts[0]
        try:
            year = int(parts[1])
        except ValueError:
            print("Invalid year in student section.")
            input("Press Enter to continue...")
            return

        fee_structure = self.fee_mgr.get_fee_structure(course_code, year)
        if fee_structure is None:
            print(f"No fee structure defined for {course_code}-{year}.")
            print("Please create and configure the fee structure first.")
            input("Press Enter to continue...")
            return

        total_fee = self.fee_mgr.calculate_total_fee(course_code, year)
        if total_fee <= 0:
            print(f"Fee structure for {course_code}-{year} is incomplete.")
            print("Please add subjects and/or particulars to the fee structure.")
            input("Press Enter to continue...")
            return

        clear_screen()
        print_header(f"GENERATE ENROLLMENT INVOICE - {student.name}")
        print(f"Course-Year: {course_code}-{year}")
        print(f"Standard Fee: PHP{total_fee:.2f}")

        breakdown = self.fee_mgr.get_fee_breakdown(course_code, year)
        print("\nFee Breakdown:")
        for item, amount in breakdown.items():
            print(f"  {item}: PHP{amount:.2f}")

        due_date = safe_string_input("\nDue date (YYYY-MM-DD): ")
        if not due_date:
            return

        discount_input = safe_string_input("Discount in PHP (leave blank for none): ", allow_empty=True)
        discount_value = 0.0
        if discount_input:
            try:
                discount_value = float(discount_input)
                if discount_value < 0:
                    print("Discount cannot be negative.")
                    input("Press Enter to continue...")
                    return
            except ValueError:
                print("Invalid discount value.")
                input("Press Enter to continue...")
                return
        discount_desc = ""
        if discount_value and discount_value > 0:
            discount_desc = safe_string_input("Discount description (optional): ", allow_empty=True) or ""

        print(f"\nInvoice Summary:")
        print(f"Student: {student.name} ({student_id})")
        net_amount = max(0.0, total_fee - discount_value)
        print(f"Amount: PHP{net_amount:.2f} (Discount: PHP{discount_value:.2f})")
        print(f"Due Date: {due_date}")

        confirm = safe_string_input("\nCreate this invoice? (yes/no): ")
        if not (confirm and confirm.lower() == "yes"):
            print("Cancelled.")
            input("Press Enter to continue...")
            return

        success, result = self.fee_mgr.generate_invoice_for_student(student_id, course_code, year, due_date, discount=discount_value, discount_description=discount_desc)
        if success:
            print(f"\n✓ Invoice created: {result}")
        else:
            print(f"\n✗ Error: {result}")

        input("Press Enter to continue...")
    
    def create_custom_invoice(self):

        while True:
            clear_screen()
            print_header("CREATE CUSTOM INVOICE")
            print("\n1. Create Invoice for Single Student")
            print("2. (removed) Create Invoice for Entire Section")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.create_custom_invoice_single_student()
            else:
                print("Invalid option.")
                input("Press Enter to continue...")
    
    def create_custom_invoice_single_student(self):

        student_id = safe_string_input("Enter student ID: ")
        if not student_id:
            return
        
        student = self.student_mgr.get_student(student_id)
        if not student:
            print("Student not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"CREATE CUSTOM INVOICE - {student.name}")
        
        amount = safe_int_input("Invoice amount (PHP): ", 1)
        if amount is None:
            return
        
        description = safe_string_input("Invoice description (e.g., Tuition, Lab Fee, etc., optional): ", allow_empty=True)
        due_date = safe_string_input("Due date (YYYY-MM-DD): ")
        if not due_date:
            return
        
        print(f"\nInvoice Summary:")
        print(f"Student: {student.name} ({student_id})")
        print(f"Amount: PHP{float(amount):.2f}")
        if description:
            print(f"Description: {description}")
        print(f"Due Date: {due_date}")
        
        confirm = safe_string_input("\nCreate this invoice? (yes/no): ")
        if not (confirm and confirm.lower() == "yes"):
            print("Cancelled.")
            input("Press Enter to continue...")
            return
        
        from fee_management import Invoice
        invoice_id = f"INV-{student_id}-{len(self.fee_mgr.invoices) + 1}"
        invoice = Invoice(invoice_id, student_id, "CUSTOM", 0, float(amount), due_date)
        invoice.breakdown = {description if description else "Custom Fee": float(amount)}
        
        self.fee_mgr.invoices[invoice_id] = invoice
        self.fee_mgr.save_data()
        
        print(f"\n✓ Invoice created successfully!")
        print(f"Invoice ID: {invoice_id}")
        input("Press Enter to continue...")
    
    # 'Create Invoice for Entire Section' option removed — handler deleted
    
    def _record_payment_for_invoice(self, invoice):

        invoice_id = invoice.invoice_id
        
        clear_screen()
        print_header(f"RECORD PAYMENT - {invoice_id}")
        
        print(f"\nStudent ID: {invoice.student_id}")
        if invoice.course_code != "CUSTOM":
            print(f"Course-Year: {invoice.course_code}-{invoice.year}")
        print(f"Amount Due: PHP{invoice.amount:.2f}")
        
        if invoice.breakdown:
            print(f"\nBreakdown:")
            for item, amount in invoice.breakdown.items():
                print(f"  {item}: PHP{amount:.2f}")
        
        paid = self.fee_mgr.get_total_paid(invoice_id)
        remaining = invoice.amount - paid
        if remaining <= 0:
            print(f"\nStatus: Fully Paid")
            print("This invoice cannot be paid further.")
            input("Press Enter to continue...")
            return
        else:
            print(f"\nAmount Paid: PHP{paid:.2f}")
            print(f"Remaining: PHP{remaining:.2f}")
        
        amount = safe_int_input("\nPayment amount (PHP): ", 1)
        if amount is None:
            return
        
        if float(amount) > remaining:
            print(f"\n✗ Error: Payment amount (PHP{float(amount):.2f}) exceeds remaining balance (PHP{remaining:.2f})")
            input("Press Enter to continue...")
            return
        
        success, payment_id = self.fee_mgr.record_payment(invoice_id, float(amount))
        
        if success:
            print(f"\n✓ Payment recorded!")
            print(f"Payment ID: {payment_id}")
        else:
            print(f"\n✗ Error: {payment_id}")
        
        input("Press Enter to continue...")
    
    def record_payment(self):

        invoice_id = safe_string_input("Enter invoice ID: ")
        if not invoice_id:
            return
        
        invoice = self.fee_mgr.get_invoice(invoice_id)
        if not invoice:
            print("Invoice not found.")
            input("Press Enter to continue...")
            return
        
        print(f"\nInvoice: {invoice_id}")
        print(f"Student ID: {invoice.student_id}")
        if invoice.course_code != "CUSTOM":
            print(f"Course-Year: {invoice.course_code}-{invoice.year}")
        print(f"Amount Due: PHP{invoice.amount:.2f}")
        
        if invoice.breakdown:
            print(f"\nBreakdown:")
            for item, amount in invoice.breakdown.items():
                print(f"  {item}: PHP{amount:.2f}")
        
        paid = self.fee_mgr.get_total_paid(invoice_id)
        remaining = invoice.amount - paid
        if remaining <= 0:
            print(f"Status: Fully Paid")
            print("This invoice cannot be paid further.")
            input("Press Enter to continue...")
            return
        else:
            print(f"Amount Paid: PHP{paid:.2f}")
            print(f"Remaining: PHP{remaining:.2f}")
        
        amount = safe_int_input("Payment amount (PHP): ", 1)
        if amount is None:
            return
        
        if float(amount) > remaining:
            print(f"\n✗ Error: Payment amount (PHP{float(amount):.2f}) exceeds remaining balance (PHP{remaining:.2f})")
            input("Press Enter to continue...")
            return
        
        success, payment_id = self.fee_mgr.record_payment(invoice_id, float(amount))
        
        if success:
            print(f"\n✓ Payment recorded!")
            print(f"Payment ID: {payment_id}")
        else:
            print(f"\n✗ Error: {payment_id}")
        
        input("Press Enter to continue...")
    
    def view_invoices(self):

        while True:
            clear_screen()
            print_header("VIEW INVOICES")
            print("\n1. View by Student")
            print("2. View by Course-Year")
            print("3. View All")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                student_id = safe_string_input("\nEnter student ID: ")
                if not student_id:
                    continue
                
                student = self.student_mgr.get_student(student_id)
                if not student:
                    print("Student not found.")
                    input("Press Enter to continue...")
                    continue
                
                invoices = self.fee_mgr.get_student_invoices(student_id)
                
                if not invoices:
                    print("\nNo invoices found.")
                    input("Press Enter to continue...")
                    continue
                
                page = 0
                page_size = 9
                
                while True:
                    clear_screen()
                    print_header(f"INVOICES - {student.name}")
                    
                    total_pages = (len(invoices) + page_size - 1) // page_size
                    start_idx = page * page_size
                    end_idx = min(start_idx + page_size, len(invoices))
                    page_invoices = invoices[start_idx:end_idx]
                    
                    print(f"\nPage {page + 1}/{total_pages} - Showing {len(page_invoices)} of {len(invoices)} invoices\n")
                    print("-" * 70)
                    
                    for idx, inv in enumerate(page_invoices, 1):
                        if inv.course_code != "CUSTOM":
                            print(f"\n[{idx}] {inv.invoice_id} ({inv.course_code}-{inv.year})")
                        else:
                            print(f"\n[{idx}] {inv.invoice_id}")
                        print(f"     Amount: PHP{inv.amount:.2f}")
                        
                        if inv.breakdown:
                            print(f"     Breakdown:")
                            for item, amount in inv.breakdown.items():
                                print(f"       {item}: PHP{amount:.2f}")
                        
                        print(f"     Due Date: {inv.due_date}")
                        print(f"     Status: {inv.status}")
                        
                        paid = self.fee_mgr.get_total_paid(inv.invoice_id)
                        remaining = inv.amount - paid
                        if paid > 0:
                            print(f"     Paid: PHP{paid:.2f} | Remaining: PHP{remaining:.2f}")
                    
                    print("\n")
                    print(f"[Page {page + 1}/{total_pages}] (w: next, q: prev, 0: back, 1-{len(page_invoices)}: select)")

                    choice = safe_string_input("\nSelect invoice or command: ").strip().upper()
                    
                    if choice == "0":
                        break
                    elif choice == "Q":
                        if page > 0:
                            page -= 1
                        else:
                            print("Already on first page.")
                            input("Press Enter to continue...")
                    elif choice == "W":
                        if page < total_pages - 1:
                            page += 1
                        else:
                            print("Already on last page.")
                            input("Press Enter to continue...")
                    elif choice in [str(i) for i in range(1, len(page_invoices) + 1)]:
                        selected_idx = int(choice) - 1
                        selected_invoice = page_invoices[selected_idx]
                        self._record_payment_for_invoice(selected_invoice)
                    else:
                        print("Invalid selection.")
                        input("Press Enter to continue...")

            elif choice == "2":
                course_code = safe_string_input("\nCourse code: ")
                if not course_code:
                    continue
                
                year = safe_int_input("Year (1-4): ", 1, 4)
                if year is None:
                    continue
                
                invoices = self.fee_mgr.get_section_invoices(course_code, year)
                
                clear_screen()
                print_header(f"INVOICES - {course_code}-{year}")
                
                if invoices:
                    print(f"\nTotal invoices: {len(invoices)}")
                    
                    paid_count = sum(1 for inv in invoices if inv.status == "paid")
                    pending_count = sum(1 for inv in invoices if inv.status == "pending")
                    
                    print(f"Paid: {paid_count}")
                    print(f"Pending: {pending_count}")
                    
                    total_collected = sum(self.fee_mgr.get_total_paid(inv.invoice_id) for inv in invoices)
                    total_due = sum(inv.amount for inv in invoices)
                    
                    print(f"\nTotal Due: PHP{total_due:.2f}")
                    print(f"Total Collected: PHP{total_collected:.2f}")
                    print(f"Outstanding: PHP{total_due - total_collected:.2f}")
                else:
                    print("\nNo invoices found.")
                
                input("\nPress Enter to continue...")
            
            elif choice == "3":
                invoices = self.fee_mgr.list_invoices()
                
                clear_screen()
                print_header("ALL INVOICES")
                
                if invoices:
                    print(f"\nTotal invoices: {len(invoices)}")
                    
                    paid_count = sum(1 for inv in invoices if inv.status == "paid")
                    pending_count = sum(1 for inv in invoices if inv.status == "pending")
                    
                    print(f"Paid: {paid_count}")
                    print(f"Pending: {pending_count}")
                    
                    total_collected = sum(self.fee_mgr.get_total_paid(inv.invoice_id) for inv in invoices)
                    total_due = sum(inv.amount for inv in invoices)
                    
                    print(f"\nTotal Due: PHP{total_due:.2f}")
                    print(f"Total Collected: PHP{total_collected:.2f}")
                    print(f"Outstanding: PHP{total_due - total_collected:.2f}")
                else:
                    print("\nNo invoices found.")
                
                input("\nPress Enter to continue...")
    
    def manage_payroll(self):

        while True:
            clear_screen()
            print_header("PAYROLL MANAGEMENT")
            print("\n1. Manage Teachers Payrolls")
            print("2. Manage Workloads (Subject Pay Rates)")
            print("3. Manage Earnings (Base Salary, Overtime, Bonuses)")
            print("4. Manage Deductions (Tax, SSS, Absences)")
            print("5. Payout")
            print("6. View Payroll Records")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.manage_teachers_payrolls()
            elif choice == "2":
                self.manage_workloads()
            elif choice == "3":
                self.manage_earnings()
            elif choice == "4":
                self.manage_deductions()
            elif choice == "5":
                self.payroll_payout()
            elif choice == "6":
                self.view_payroll_records()
            else:
                print("Invalid option.")
                input("Press Enter to continue...")
    
    def manage_teachers_payrolls(self):

        teachers = self.teacher_mgr.list_teachers()
        
        if not teachers:
            print("\nNo teachers found.")
            input("Press Enter to continue...")
            return
        
        page = 0
        page_size = 9
        
        while True:
            clear_screen()
            print_header("MANAGE TEACHERS PAYROLLS")
            
            total_pages = (len(teachers) + page_size - 1) // page_size
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(teachers))
            page_teachers = teachers[start_idx:end_idx]
            
            print(f"\nPage {page + 1}/{total_pages} - Showing {len(page_teachers)} of {len(teachers)} teachers\n")
            print("-" * 90)
            
            for idx, teacher in enumerate(page_teachers, 1):
                teacher_payroll = self.fee_mgr.get_teacher_all_payroll(teacher.teacher_id)
                print(f"\n[{idx}] {teacher.name} ({teacher.teacher_id})")
                print(f"     Email: {teacher.email}")
                
                subjects_set = set()
                for section in teacher.class_sessions:
                    schedules = self.teacher_mgr.get_schedules(teacher.teacher_id, section)
                    if schedules:
                        for sched in schedules:
                            subjects_set.add(sched.subject)
                
                if subjects_set:
                    subjects_info = []
                    for subject in sorted(subjects_set):
                        workload_rate = self.fee_mgr.get_workload_rate(subject)
                        if workload_rate:
                            subjects_info.append(f"{subject}(PHP{workload_rate.rate_per_day:.0f}/day)")
                        else:
                            subjects_info.append(f"{subject}(no rate)")
                    print(f"     Subjects: {', '.join(subjects_info)}")
                else:
                    print(f"     Subjects: (none assigned)")
                
                print(f"     Payroll Records: {len(teacher_payroll)}")
                if teacher_payroll:
                    latest = teacher_payroll[-1]
                    print(f"     Latest: {latest.payout_period} - PHP{latest.net_salary:.2f}")
            
            print("\n" + "-" * 90)
            print(f"[Page {page + 1}/{total_pages}] (w: next, q: prev, 0: back, 1-{len(page_teachers)}: select)")
            print("-" * 90)
            
            choice = safe_string_input("\nSelect teacher or command: ").strip().upper()
            
            if choice == "0":
                break
            elif choice == "Q":
                if page > 0:
                    page -= 1
                else:
                    print("Already on first page.")
                    input("Press Enter to continue...")
            elif choice == "W":
                if page < total_pages - 1:
                    page += 1
                else:
                    print("Already on last page.")
                    input("Press Enter to continue...")
            elif choice in [str(i) for i in range(1, len(page_teachers) + 1)]:
                selected_teacher = page_teachers[int(choice) - 1]
                self.manage_teacher_payout(selected_teacher.teacher_id)
            else:
                print("Invalid selection.")
                input("Press Enter to continue...")
    
    def manage_teacher_payout(self, teacher_id: str):

        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"TEACHER PAYROLL - {teacher.name}")
            
            subjects_set = set()
            for section in teacher.class_sessions:
                schedules = self.teacher_mgr.get_schedules(teacher_id, section)
                if schedules:
                    for sched in schedules:
                        subjects_set.add(sched.subject)
            
            subjects = sorted(list(subjects_set))
            
            print(f"\nTeacher ID: {teacher_id}")
            print(f"Email: {teacher.email}")
            print(f"Phone: {teacher.phone}")
            
            print(f"\nSubjects & Pay Rates:")
            if subjects:
                for subject in subjects:
                    workload_rate = self.fee_mgr.get_workload_rate(subject)
                    if workload_rate:
                        print(f"  • {subject}: PHP{workload_rate.rate_per_day:.2f}/day")
                    else:
                        print(f"  • {subject}: (rate not configured)")
            else:
                print("  (none assigned)")
            
            payroll_records = self.fee_mgr.get_teacher_all_payroll(teacher_id)
            print(f"\nPayroll Records: {len(payroll_records)}")
            if payroll_records:
                for p in payroll_records[-3:]:
                    print(f"  {p.payout_period}: PHP{p.net_salary:.2f}")
            
            print("\n1. Process Payout")
            print("2. View Detailed Summary")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.process_teacher_payout(teacher_id, teacher)
            elif choice == "2":
                self.view_teacher_payroll_summary(teacher_id)
            else:
                print("Invalid selection.")
                input("Press Enter to continue...")
    
    def process_teacher_payout(self, teacher_id: str, teacher):

        subjects_set = set()
        for section in teacher.class_sessions:
            schedules = self.teacher_mgr.get_schedules(teacher_id, section)
            if schedules:
                for sched in schedules:
                    subjects_set.add(sched.subject)
        
        subjects = sorted(list(subjects_set))
        if not subjects:
            print("Teacher has no subjects assigned.")
            input("Press Enter to continue...")
            return
        
        payout_period = safe_string_input("\nPayout period (YYYY-MM-A or YYYY-MM-B): ")
        if not payout_period or payout_period[-1] not in ['A', 'B']:
            print("Invalid format. Use YYYY-MM-A or YYYY-MM-B")
            input("Press Enter to continue...")
            return
        
        existing = self.fee_mgr.get_teacher_payroll_by_period(teacher_id, payout_period)
        if existing:
            print(f"Payroll already exists for {payout_period}")
            input("Press Enter to continue...")
            return
        
        success, payroll_id = self.fee_mgr.create_teacher_payroll(teacher_id, payout_period)
        if not success:
            print(f"✗ Error: {payroll_id}")
            input("Press Enter to continue...")
            return
        
        days_present = safe_int_input("Days present (0-14): ", 0, 14)
        if days_present is None:
            return
        
        overtime = safe_int_input("Overtime hours (0 if none): ", 0)
        if overtime is None:
            return
        
        bonuses = self.fee_mgr.list_bonuses()
        selected_bonus_ids = []
        
        if bonuses:
            print(f"\nAvailable Bonuses:")
            for i, bonus in enumerate(bonuses, 1):
                print(f"{i}. {bonus.name} - PHP{bonus.amount:.2f}")
            
            print("\nEnter bonus numbers separated by commas (or leave empty for none)")
            bonus_input = safe_string_input("Selected bonuses: ", allow_empty=True)
            
            if bonus_input:
                try:
                    bonus_indices = [int(x.strip()) - 1 for x in bonus_input.split(',')]
                    selected_bonus_ids = [bonuses[i].bonus_id for i in bonus_indices if 0 <= i < len(bonuses)]
                except:
                    print("Invalid bonus selection.")
        
        success, msg = self.fee_mgr.calculate_payroll(
            payroll_id, days_present, subjects, selected_bonus_ids, float(overtime)
        )
        
        if not success:
            print(f"✗ Error: {msg}")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"PAYROLL BREAKDOWN")
        
        breakdown = self.fee_mgr.get_payroll_breakdown(payroll_id)
        if breakdown:
            print(f"\nTeacher: {teacher.name}")
            print(f"Period: {breakdown['payout_period']}")
            print(f"\nEarnings:")
            print(f"  Base Salary: PHP{breakdown['base_salary']:.2f}")
            print(f"  Workload ({days_present} days): PHP{breakdown['workload_earnings']:.2f}")
            if breakdown['overtime_earnings'] > 0:
                print(f"  Overtime ({overtime}h): PHP{breakdown['overtime_earnings']:.2f}")
            if breakdown['bonus_amount'] > 0:
                print(f"  Bonuses: PHP{breakdown['bonus_amount']:.2f}")
            print(f"  Gross Salary: PHP{breakdown['gross_salary']:.2f}")
            
            print(f"\nDeductions:")
            if breakdown['tax_deduction'] > 0:
                print(f"  Tax: PHP{breakdown['tax_deduction']:.2f}")
            if breakdown['sss_deduction'] > 0:
                print(f"  SSS: PHP{breakdown['sss_deduction']:.2f}")
            if breakdown['absence_deduction'] > 0:
                print(f"  Absence ({14 - days_present} days): PHP{breakdown['absence_deduction']:.2f}")
            print(f"  Total Deductions: PHP{breakdown['total_deductions']:.2f}")
            
            print(f"\nNet Salary: PHP{breakdown['net_salary']:.2f}")
        
        confirm = safe_string_input("\nConfirm payout? (yes/no): ")
        if confirm and confirm.lower() == "yes":
            success, msg = self.fee_mgr.finalize_payroll(payroll_id)
            if success:
                print(f"\n✓ Payroll finalized successfully!")
            else:
                print(f"\n✗ Error: {msg}")
        
        input("Press Enter to continue...")
    
    def view_teacher_payroll_summary(self, teacher_id: str):

        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print("Teacher not found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"PAYROLL SUMMARY - {teacher.name}")
        
        payroll_records = self.fee_mgr.get_teacher_all_payroll(teacher_id)
        
        print(f"\nTeacher ID: {teacher_id}")
        print(f"Email: {teacher.email}")
        print(f"Phone: {teacher.phone}")
        
        subjects_set = set()
        for section in teacher.class_sessions:
            schedules = self.teacher_mgr.get_schedules(teacher_id, section)
            if schedules:
                for sched in schedules:
                    subjects_set.add(sched.subject)
        
        print(f"\nSubjects & Pay Rates:")
        if subjects_set:
            for subject in sorted(subjects_set):
                workload_rate = self.fee_mgr.get_workload_rate(subject)
                if workload_rate:
                    print(f"  • {subject}: PHP{workload_rate.rate_per_day:.2f}/day")
                else:
                    print(f"  • {subject}: (rate not configured)")
        else:
            print("  (No subjects assigned)")
        
        print(f"\nEarnings Configuration:")
        earnings_config = self.fee_mgr.earnings_config
        print(f"  Base Salary: PHP{earnings_config.base_salary:.2f}")
        print(f"  Overtime Multiplier: {earnings_config.overtime_rate}x")
        print(f"  Available Bonuses: {len(earnings_config.bonuses)}")
        if earnings_config.bonuses:
            for bonus in earnings_config.bonuses.values():
                print(f"    - {bonus.name}: PHP{bonus.amount:.2f}")
        
        print(f"\nDeductions Configuration:")
        deduction_config = self.fee_mgr.deduction_config
        print(f"  Tax Rate: {deduction_config.tax_rate}%")
        print(f"  SSS Rate: {deduction_config.sss_rate}%")
        print(f"  Absence Deduction: PHP{deduction_config.absence_deduction:.2f}/day")
        
        print(f"\nPayroll Records: {len(payroll_records)}")
        
        if payroll_records:
            total_paid = sum(p.net_salary for p in payroll_records)
            
            print(f"  Total Paid: PHP{total_paid:.2f}")
            
            print(f"\nRecent Payouts:")
            for p in payroll_records[-3:]:
                print(f"  ✓ {p.payout_period}: PHP{p.net_salary:.2f}")
        
        input("\nPress Enter to continue...")
    
    def manage_workloads(self):

        while True:
            clear_screen()
            print_header("MANAGE WORKLOADS (Subject Pay Rates)")
            print("\n1. Set Subject Pay Rate")
            print("2. View All Pay Rates")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                courses = self.course_mgr.list_courses()
                available_subjects = set()
                
                for course_code, course_data in courses:
                    for year in range(1, 5):
                        section = self.course_mgr.get_section(course_code, year, 1)
                        if section:
                            available_subjects.update(section.get("subjects", []))
                
                if not available_subjects:
                    print("\nNo subjects found in any course. Create courses and sections first.")
                    input("Press Enter to continue...")
                    continue
                
                available_subjects = sorted(list(available_subjects))
                print(f"\nAvailable Subjects ({len(available_subjects)}):")
                for i, subj in enumerate(available_subjects, 1):
                    print(f"{i}. {subj}")
                
                subject_choice = safe_int_input("Select subject (number): ", 1, len(available_subjects))
                if subject_choice is None:
                    continue
                
                subject = available_subjects[subject_choice - 1]
                
                rate = safe_int_input("Pay rate per day (PHP): ", 1)
                if rate is None:
                    continue
                
                success, msg = self.fee_mgr.set_workload_rate(subject, float(rate))
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                rates = self.fee_mgr.list_workload_rates()
                if rates:
                    print("\nSubject Pay Rates:")
                    for rate in rates:
                        print(f"  {rate.subject}: PHP{rate.rate_per_day:.2f}/day")
                else:
                    print("\nNo pay rates configured yet.")
                input("Press Enter to continue...")
    
    def manage_earnings(self):

        while True:
            clear_screen()
            print_header("MANAGE EARNINGS")
            print("\n1. Set Base Salary")
            print("2. Set Overtime Rate")
            print("3. Create Bonus")
            print("4. View Bonuses")
            print("5. Delete Bonus")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                amount = safe_int_input("\nBase salary (PHP): ", 0)
                if amount is None:
                    continue
                
                success, msg = self.fee_mgr.set_base_salary(float(amount))
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                rate = safe_float_input("\nOvertime rate multiplier (e.g., 1.5 for 1.5x): ", 0.1)
                if rate is None:
                    continue
                
                success, msg = self.fee_mgr.set_overtime_rate(rate)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "3":
                name = safe_string_input("\nBonus name (e.g., Performance Bonus): ")
                if not name:
                    continue
                
                amount = safe_int_input("Bonus amount (PHP): ", 1)
                if amount is None:
                    continue
                
                success, bonus_id = self.fee_mgr.create_bonus(name, float(amount))
                if success:
                    print(f"\n✓ Bonus created! ID: {bonus_id}")
                else:
                    print(f"\n✗ Error: {bonus_id}")
                input("Press Enter to continue...")
            
            elif choice == "4":
                bonuses = self.fee_mgr.list_bonuses()
                if bonuses:
                    print("\nAvailable Bonuses:")
                    for bonus in bonuses:
                        print(f"  {bonus.bonus_id}: {bonus.name} - PHP{bonus.amount:.2f}")
                else:
                    print("\nNo bonuses configured yet.")
                input("Press Enter to continue...")
            
            elif choice == "5":
                bonus_id = safe_string_input("\nBonus ID to delete: ")
                if not bonus_id:
                    continue
                
                success, msg = self.fee_mgr.delete_bonus(bonus_id)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
    
    def manage_deductions(self):

        while True:
            clear_screen()
            print_header("MANAGE DEDUCTIONS")
            
            config = self.fee_mgr.deduction_config
            print(f"\nCurrent Settings:")
            print(f"  Tax Rate: {config.tax_rate}%")
            print(f"  SSS Rate: {config.sss_rate}%")
            print(f"  Absence Deduction: PHP{config.absence_deduction:.2f}/day")
            
            print("\n1. Set Tax Rate (%)")
            print("2. Set SSS Rate (%)")
            print("3. Set Absence Deduction (PHP/day)")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                rate = safe_int_input("\nTax rate (%): ", 0)
                if rate is None:
                    continue
                
                success, msg = self.fee_mgr.set_tax_rate(float(rate))
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                rate = safe_int_input("\nSSS rate (%): ", 0)
                if rate is None:
                    continue
                
                success, msg = self.fee_mgr.set_sss_rate(float(rate))
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "3":
                amount = safe_int_input("\nAbsence deduction (PHP/day): ", 0)
                if amount is None:
                    continue
                
                success, msg = self.fee_mgr.set_absence_deduction(float(amount))
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
    
    def payroll_payout(self):

        teacher_id = safe_string_input("Enter teacher ID: ").strip()
        if not teacher_id:
            return
        
        teacher = self.teacher_mgr.get_teacher(teacher_id)
        if not teacher:
            print(f"✗ Teacher '{teacher_id}' not found.")
            input("Press Enter to continue...")
            return
        
        payout_period = safe_string_input("\nPayout period (YYYY-MM-A or YYYY-MM-B): ")
        if not payout_period or payout_period[-1] not in ['A', 'B']:
            print("Invalid format. Use YYYY-MM-A or YYYY-MM-B")
            input("Press Enter to continue...")
            return
        
        existing = self.fee_mgr.get_teacher_payroll_by_period(teacher.teacher_id, payout_period)
        if existing:
            print(f"Payroll already exists for {payout_period}")
            input("Press Enter to continue...")
            return
        
        success, payroll_id = self.fee_mgr.create_teacher_payroll(teacher.teacher_id, payout_period)
        if not success:
            print(f"✗ Error: {payroll_id}")
            input("Press Enter to continue...")
            return
        
        subjects_set = set()
        for section in teacher.class_sessions:
            schedules = self.teacher_mgr.get_schedules(teacher.teacher_id, section)
            if schedules:
                for sched in schedules:
                    subjects_set.add(sched.subject)
        
        subjects = sorted(list(subjects_set))
        if not subjects:
            print("Teacher has no subjects assigned.")
            input("Press Enter to continue...")
            return
        
        print(f"\nTeacher Subjects (all included in payout):")
        for i, subject in enumerate(subjects, 1):
            rate = self.fee_mgr.get_workload_rate(subject)
            rate_str = f"PHP{rate.rate_per_day:.2f}/day" if rate else "(rate not set)"
            print(f"{i}. {subject} - {rate_str}")
        
        days_present = safe_int_input("Days present (0-14): ", 0, 14)
        if days_present is None:
            return
        
        overtime = safe_int_input("Overtime hours (0 if none): ", 0)
        if overtime is None:
            return
        
        bonuses = self.fee_mgr.list_bonuses()
        selected_bonus_ids = []
        
        if bonuses:
            print(f"\nAvailable Bonuses:")
            for i, bonus in enumerate(bonuses, 1):
                print(f"{i}. {bonus.name} - PHP{bonus.amount:.2f}")
            
            print("\nEnter bonus numbers separated by commas (or leave empty for none)")
            bonus_input = safe_string_input("Selected bonuses: ", allow_empty=True)
            
            if bonus_input:
                try:
                    bonus_indices = [int(x.strip()) - 1 for x in bonus_input.split(',')]
                    selected_bonus_ids = [bonuses[i].bonus_id for i in bonus_indices if 0 <= i < len(bonuses)]
                except:
                    print("Invalid bonus selection.")
        
        success, msg = self.fee_mgr.calculate_payroll(
            payroll_id, days_present, subjects, selected_bonus_ids, float(overtime)
        )
        
        if not success:
            print(f"✗ Error: {msg}")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"PAYROLL BREAKDOWN")
        
        breakdown = self.fee_mgr.get_payroll_breakdown(payroll_id)
        if breakdown:
            print(f"\nTeacher: {teacher.name}")
            print(f"Period: {breakdown['payout_period']}")
            print(f"\nEarnings:")
            print(f"  Base Salary: PHP{breakdown['base_salary']:.2f}")
            print(f"  Workload ({days_present} days): PHP{breakdown['workload_earnings']:.2f}")
            if breakdown['overtime_earnings'] > 0:
                print(f"  Overtime ({overtime}h): PHP{breakdown['overtime_earnings']:.2f}")
            if breakdown['bonus_amount'] > 0:
                print(f"  Bonuses: PHP{breakdown['bonus_amount']:.2f}")
            print(f"  Gross Salary: PHP{breakdown['gross_salary']:.2f}")
            
            print(f"\nDeductions:")
            if breakdown['tax_deduction'] > 0:
                print(f"  Tax: PHP{breakdown['tax_deduction']:.2f}")
            if breakdown['sss_deduction'] > 0:
                print(f"  SSS: PHP{breakdown['sss_deduction']:.2f}")
            if breakdown['absence_deduction'] > 0:
                print(f"  Absence ({14 - days_present} days): PHP{breakdown['absence_deduction']:.2f}")
            print(f"  Total Deductions: PHP{breakdown['total_deductions']:.2f}")
            
            print(f"\nNet Salary: PHP{breakdown['net_salary']:.2f}")
        
        confirm = safe_string_input("\nConfirm payout? (yes/no): ")
        if confirm and confirm.lower() == "yes":
            success, msg = self.fee_mgr.finalize_payroll(payroll_id)
            if success:
                print(f"\n✓ Payroll paid successfully!")
            else:
                print(f"\n✗ Error: {msg}")
        
        input("Press Enter to continue...")
    
    def view_payroll_records(self):

        payroll_records = self.fee_mgr.list_all_payroll()
        
        if not payroll_records:
            print("\nNo payroll records found.")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header("PAYROLL RECORDS")
        
        print(f"\nTotal Records: {len(payroll_records)}\n")
        print("-" * 85)
        print(f"{'ID':<15} {'Teacher':<20} {'Period':<12} {'Gross':<12} {'Deductions':<12} {'Net':<12}")
        print("-" * 85)
        
        for p in payroll_records:
            teacher = self.teacher_mgr.get_teacher(p.teacher_id)
            teacher_name = teacher.name if teacher else "Unknown"
            print(f"{p.payroll_id:<15} {teacher_name:<20} {p.payout_period:<12} PHP{p.gross_salary:<11.2f} PHP{p.total_deductions:<11.2f} PHP{p.net_salary:<11.2f}")
        
        print("-" * 85)
        input("Press Enter to continue...")
    
    def financial_reports(self):

        clear_screen()
        print_header("FINANCIAL REPORTS")
        
        summary = self.fee_mgr.get_financial_summary()
        
        print(f"\nFees Collected: PHP{summary['total_fees_collected']:.2f}")
        print(f"Outstanding Fees: PHP{summary['outstanding_fees']:.2f}")
        print(f"Total Invoices: {summary['total_invoices']}")
        print(f"  - Paid: {summary['paid_invoices']}")
        print(f"  - Pending: {summary['pending_invoices']}")
        print(f"Total Payments: {summary['total_payments']}")
        print(f"Total Payroll Expenses: PHP{summary['total_payroll_expenses']:.2f}")
        
        input("\nPress Enter to continue...")
    
    def course_menu(self):

        while True:
            clear_screen()
            print_header("COURSE & SECTION MANAGEMENT")
            print("\n1. Create Course")
            print("2. Create Section")
            print("3. View All Courses")
            print("4. Add Subject to Section")
            print("0. Back to Main Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                code = safe_string_input("\nCourse code (e.g., BSIT): ")
                if not code:
                    continue
                
                name = safe_string_input("Course name (e.g., Bachelor of Science in Information Technology): ")
                if not name:
                    continue
                
                desc = safe_string_input("Description (optional): ", allow_empty=True)
                
                success, msg = self.course_mgr.create_course(code, name, desc or "")
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "2":
                code = safe_string_input("\nCourse code: ")
                if not code:
                    continue
                
                year = safe_int_input("Year (1-4): ", 1, 4)
                if year is None:
                    continue
                
                success, msg = self.course_mgr.create_section(code, year)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "3":
                courses = self.course_mgr.list_courses()
                if courses:
                    print("\nCourses:")
                    course_list = []
                    for idx, (code, course) in enumerate(courses, 1):
                        course_list.append((code, course))
                        print(f"\n{idx}. {code} - {course['name']}")
                        if course['description']:
                            print(f"   {course['description']}")
                        
                        for year, sections in course['sections'].items():
                            print(f"   Year {year}: {len(sections)} section(s)")
                    
                    print("\n0. Back")
                    selection = safe_string_input("\nSelect course to view subjects (or 0 to go back): ")
                    
                    if selection != "0":
                        try:
                            idx = int(selection) - 1
                            if 0 <= idx < len(course_list):
                                code, course = course_list[idx]
                                year = safe_int_input(f"\nYear (1-4) for {code}: ", 1, 4)
                                if year is not None:
                                    year_str = str(year)
                                    if year_str in course['sections'] and course['sections'][year_str]:
                                        print(f"\nSubjects in {code} Year {year}:")
                                        for sec_num, section in sorted(course['sections'][year_str].items()):
                                            print(f"  Section {sec_num}: {', '.join(section['subjects']) if section['subjects'] else 'No subjects'}")
                                    else:
                                        print(f"\nNo sections found for {code} Year {year}")
                                    input("\nPress Enter to continue...")
                        except ValueError:
                            pass
                else:
                    print("\nNo courses found.")
                    input("Press Enter to continue...")
            
            elif choice == "4":
                code = safe_string_input("\nCourse code: ")
                if not code:
                    continue
                
                year = safe_int_input("Year (1-4): ", 1, 4)
                if year is None:
                    continue
                
                subject = safe_string_input("Subject name: ")
                if not subject:
                    continue
                
                success, msg = self.course_mgr.add_subject_to_year(code, year, subject)
                print(f"\n{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
    
    def communication_menu(self):

        while True:
            clear_screen()
            print_header("PARENT & COMMUNICATION MANAGEMENT")
            print("\n1. Manage Parent Accounts")
            print("2. Send Notification")
            print("3. Send Bulk Notification")
            print("4. View Notifications")
            print("0. Back to Main Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.manage_parents()
            elif choice == "2":
                self.send_notification()
            elif choice == "3":
                self.send_bulk_notification()
            elif choice == "4":
                self.view_notifications()
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
    
    def view_parents(self):

        parents = self.comm_mgr.list_parents()
        
        if not parents:
            print("\nNo parent accounts found.")
            input("Press Enter to continue...")
            return
        
        page = 1
        while True:
            clear_screen()
            print_header("PARENT ACCOUNTS")
            
            items = [f"{p.parent_id} - {p.name} ({p.email})" for p in parents]
            page, selected = display_page(items, page, "Parents")
            
            if selected == -1:
                break
            
            if selected is not None:
                selected_parent = parents[selected]
                self.parent_management_options(selected_parent.parent_id)
    
    def parent_management_options(self, parent_id):

        parent = self.comm_mgr.get_parent(parent_id)
        if not parent:
            print("Parent not found.")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print_header(f"PARENT - {parent.name}")
            print(f"\nID: {parent.parent_id}")
            print(f"Email: {parent.email}")
            print(f"Phone: {parent.phone}")
            print("\n" + "-" * 60)
            print("\n1. Update Parent Info")
            print("2. Link Student to Parent")
            print("3. Remove Student from Parent")
            print("4. View Parent Details")
            print("0. Back to Parent List")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                print(f"\nCurrent: {parent.name}, {parent.email}, {parent.phone}")
                
                name = safe_string_input("New name (leave blank to skip): ")
                email = safe_string_input("New email (leave blank to skip): ")
                phone = safe_string_input("New phone (leave blank to skip): ")
                
                success, msg = self.comm_mgr.update_parent(parent_id, name, email, phone)
                print(f"{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
                
                parent = self.comm_mgr.get_parent(parent_id)
            
            elif choice == "2":
                student_id = safe_string_input("\nStudent ID to link: ")
                if student_id:
                    success, msg = self.comm_mgr.add_student_to_parent(parent_id, student_id)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
                    parent = self.comm_mgr.get_parent(parent_id)
            
            elif choice == "3":
                if not parent.student_ids:
                    print("\n✗ No students linked to this parent")
                    input("Press Enter to continue...")
                    continue
                
                print("\nLinked Students:")
                for i, child_id in enumerate(parent.student_ids, 1):
                    child = self.student_mgr.get_student(child_id)
                    if child:
                        print(f"  {i}. {child_id}: {child.name}")
                
                student_id = safe_string_input("\nEnter Student ID to remove: ")
                if student_id:
                    success, msg = self.comm_mgr.remove_student_from_parent(parent_id, student_id)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
                    parent = self.comm_mgr.get_parent(parent_id)
            
            elif choice == "4":
                clear_screen()
                print_header(f"PARENT DETAILS - {parent.name}")
                print(f"\nID: {parent.parent_id}")
                print(f"Name: {parent.name}")
                print(f"Email: {parent.email}")
                print(f"Phone: {parent.phone}")
                print(f"Status: {parent.account_status}")
                print(f"Children Count: {len(parent.student_ids)}")
                print(f"Created: {parent.created_date}")
                
                if parent.student_ids:
                    print(f"\nLinked Students:")
                    for child_id in parent.student_ids:
                        child = self.student_mgr.get_student(child_id)
                        if child:
                            print(f"  - {child_id}: {child.name}")
                
                input("\nPress Enter to continue...")
    
    def send_notification(self):

        parent_id = safe_string_input("Enter parent ID: ")
        if not parent_id:
            return
        
        parent = self.comm_mgr.get_parent(parent_id)
        if not parent:
            print("Parent not found.")
            input("Press Enter to continue...")
            return
        
        print(f"\nSending notification to: {parent.name}")
        
        subject = safe_string_input("Subject: ")
        if not subject:
            return
        
        message = safe_string_input("Message: ")
        if not message:
            return
        
        print("\n1. Grade")
        print("2. Attendance")
        print("3. Fee")
        print("4. Event")
        print("5. Holiday")
        print("6. Other")
        
        type_choice = safe_int_input("Notification type: ", 1, 6)
        if type_choice is None:
            return
        
        type_map = {1: "grade", 2: "attendance", 3: "fee", 4: "event", 5: "holiday", 6: "other"}
        notif_type = type_map[type_choice]
        
        success, notif_id = self.comm_mgr.send_notification(parent_id, subject, message, notif_type)
        
        if success:
            print(f"\n✓ Notification sent!")
            print(f"Notification ID: {notif_id}")
        else:
            print(f"\n✗ Error: {notif_id}")
        
        input("Press Enter to continue...")
    
    def send_bulk_notification(self):

        print_section("SEND BULK NOTIFICATION")
        
        all_parents = self.comm_mgr.list_parents()
        if not all_parents:
            print("No parent accounts found.")
            input("Press Enter to continue...")
            return
        
        subject = safe_string_input("Subject: ")
        if not subject:
            return
        
        message = safe_string_input("Message: ")
        if not message:
            return
        
        confirm = safe_string_input(f"\nSend to {len(all_parents)} parent(s)? (yes/no): ")
        
        if confirm and confirm.lower() == "yes":
            success_count = 0
            for parent in all_parents:
                success, msg = self.comm_mgr.send_notification(parent.parent_id, subject, message, "other")
                if success:
                    success_count += 1
            
            print(f"\n✓ Notifications sent to {success_count}/{len(all_parents)} parents")
        else:
            print("Cancelled.")
        
        input("Press Enter to continue...")
    
    def view_notifications(self):

        all_notifs = self.comm_mgr.list_notifications()
        
        if not all_notifs:
            print("\nNo notifications found.")
            input("Press Enter to continue...")
            return
        
        page = 1
        while True:
            clear_screen()
            print_header("NOTIFICATIONS")
            
            items = [f"{n.notification_id} - {n.subject} ({n.notification_type})" for n in all_notifs]
            page, selected = display_page(items, page, "Notifications")
            
            if selected == -1:
                break
    
    def create_standalone_parent(self):

        clear_screen()
        print_header("CREATE NEW PARENT ACCOUNT")
        
        name = get_full_name()
        if not name:
            print("Parent creation cancelled.")
            input("Press Enter to continue...")
            return
        
        email = safe_string_input("Email address: ")
        if not email:
            print("Email is required.")
            input("Press Enter to continue...")
            return
        
        phone = safe_string_input("Phone number: ")
        if not phone:
            print("Phone is required.")
            input("Press Enter to continue...")
            return
        
        student_ids = []
        print("\nLink students to this parent (enter at least one student ID):")
        
        while True:
            student_id = safe_string_input("Enter student ID (or press Enter to skip): ", allow_empty=True)
            if not student_id:
                if student_ids:
                    break
                else:
                    confirm = safe_string_input("No students linked. Create parent anyway? (yes/no): ")
                    if confirm and confirm.lower() == "yes":
                        student_ids = ["PLACEHOLDER"]
                        break
                    continue
            
            student = self.student_mgr.get_student(student_id)
            if not student:
                print("✗ Student not found.")
                continue
            
            if student_id not in student_ids:
                student_ids.append(student_id)
                print(f"✓ {student.name} added")
            else:
                print("✗ Student already added")
            
            another = safe_string_input("Add another student? (yes/no): ")
            if not (another and another.lower() == "yes"):
                break
        
        if not student_ids:
            print("No students provided. Cancelled.")
            input("Press Enter to continue...")
            return
        
        success, parent_id = self.comm_mgr.create_parent_account(name, email, phone, student_ids)
        
        if success:
            if student_ids == ["PLACEHOLDER"]:
                self.comm_mgr.get_parent(parent_id).student_ids = []
                self.comm_mgr.get_parent(parent_id).children = []
                self.comm_mgr.save_data()
            
            print(f"\n✓ Parent account created successfully!")
            print(f"Parent ID: {parent_id}")
            print(f"Name: {name}")
            print(f"Email: {email}")
            print(f"Phone: {phone}")
            print(f"Linked Students: {len([s for s in student_ids if s != 'PLACEHOLDER'])}")
        else:
            print(f"✗ {parent_id}")
        
        input("Press Enter to continue...")
    
    def manage_parents(self):

        while True:
            clear_screen()
            print_header("MANAGE PARENT ACCOUNTS")
            print("\n1. View Parent Accounts")
            print("2. Create New Parent")
            print("3. Update Parent Info")
            print("4. Link Student to Parent")
            print("5. Remove Student from Parent")
            print("6. View Parent Details")
            print("7. View Parent by Student ID")
            print("0. Back")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.view_parents()
            elif choice == "2":
                self.create_standalone_parent()
            elif choice == "3":
                parent_id = safe_string_input("\nParent ID: ")
                if not parent_id:
                    continue
                
                parent = self.comm_mgr.get_parent(parent_id)
                if not parent:
                    print("Parent not found.")
                    input("Press Enter to continue...")
                    continue
                
                print(f"\nCurrent: {parent.name}, {parent.email}, {parent.phone}")
                
                name = safe_string_input("New name (leave blank to skip): ")
                email = safe_string_input("New email (leave blank to skip): ")
                phone = safe_string_input("New phone (leave blank to skip): ")
                
                success, msg = self.comm_mgr.update_parent(parent_id, name, email, phone)
                print(f"{'✓' if success else '✗'} {msg}")
                input("Press Enter to continue...")
            
            elif choice == "4":
                parent_id = safe_string_input("\nParent ID: ")
                if not parent_id:
                    continue
                
                parent = self.comm_mgr.get_parent(parent_id)
                if not parent:
                    print("Parent not found.")
                    input("Press Enter to continue...")
                    continue
                
                student_id = safe_string_input("Student ID to link: ")
                if student_id:
                    success, msg = self.comm_mgr.add_student_to_parent(parent_id, student_id)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
            
            elif choice == "5":
                parent_id = safe_string_input("\nParent ID: ")
                if not parent_id:
                    continue
                
                parent = self.comm_mgr.get_parent(parent_id)
                if not parent:
                    print("Parent not found.")
                    input("Press Enter to continue...")
                    continue
                
                if not parent.student_ids:
                    print("\n✗ No students linked to this parent")
                    input("Press Enter to continue...")
                    continue
                
                print("\nLinked Students:")
                for i, child_id in enumerate(parent.student_ids, 1):
                    child = self.student_mgr.get_student(child_id)
                    if child:
                        print(f"  {i}. {child_id}: {child.name}")
                
                student_id = safe_string_input("\nEnter Student ID to remove: ")
                if student_id:
                    success, msg = self.comm_mgr.remove_student_from_parent(parent_id, student_id)
                    print(f"\n{'✓' if success else '✗'} {msg}")
                    input("Press Enter to continue...")
            
            elif choice == "6":
                parent_id = safe_string_input("\nParent ID: ")
                if not parent_id:
                    continue
                
                parent = self.comm_mgr.get_parent(parent_id)
                if not parent:
                    print("Parent not found.")
                    input("Press Enter to continue...")
                    continue
                
                clear_screen()
                print_header(f"PARENT DETAILS - {parent.name}")
                print(f"\nID: {parent.parent_id}")
                print(f"Name: {parent.name}")
                print(f"Email: {parent.email}")
                print(f"Phone: {parent.phone}")
                print(f"Status: {parent.account_status}")
                print(f"Children Count: {len(parent.student_ids)}")
                print(f"Created: {parent.created_date}")
                
                input("\nPress Enter to continue...")
            
            elif choice == "7":
                self.view_parent_by_student_id()
    
    def view_parent_by_student_id(self):

        student_id = safe_string_input("\nEnter Student ID: ")
        if not student_id:
            return
        
        student = self.student_mgr.get_student(student_id)
        if not student:
            print("✗ Student not found.")
            input("Press Enter to continue...")
            return
        
        all_parents = self.comm_mgr.list_parents()
        parent_found = None
        
        for parent in all_parents:
            if student_id in parent.student_ids:
                parent_found = parent
                break
        
        if not parent_found:
            print(f"\n✗ No parent found for student {student_id} ({student.name})")
            input("Press Enter to continue...")
            return
        
        clear_screen()
        print_header(f"PARENT DETAILS (via Student: {student.name})")
        print(f"\nStudent ID: {student_id}")
        print(f"Student Name: {student.name}")
        print(f"\nParent Information:")
        print(f"  Parent ID: {parent_found.parent_id}")
        print(f"  Name: {parent_found.name}")
        print(f"  Email: {parent_found.email}")
        print(f"  Phone: {parent_found.phone}")
        print(f"  Status: {parent_found.account_status}")
        print(f"  Created: {parent_found.created_date}")
        
        print(f"\n  Linked Students: {len(parent_found.student_ids)}")
        if parent_found.student_ids:
            print("  Student List:")
            for child_id in parent_found.student_ids:
                child = self.student_mgr.get_student(child_id)
                if child:
                    print(f"    - {child_id}: {child.name}")
        
        input("\nPress Enter to continue...")
    
    def settings_menu(self):

        while True:
            clear_screen()
            print_header("SYSTEM SETTINGS")
            print("\n1. Change Admin Password")
            print("2. View System Statistics")
            print("0. Back to Main Menu")
            print("-" * 60)
            
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.change_admin_password()
            elif choice == "2":
                self.view_statistics()
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")
    
    def change_admin_password(self):

        print_section("CHANGE ADMIN PASSWORD")
        print("\nThis feature requires authentication.")
        print("Please use the password recovery system at login.")
        input("Press Enter to continue...")
    
    def view_statistics(self):

        clear_screen()
        print_header("SYSTEM STATISTICS")
        
        students_count = len(self.student_mgr.list_students())
        teachers_count = len(self.teacher_mgr.list_teachers())
        parents_count = len(self.comm_mgr.list_parents())
        
        print(f"\nTotal Students: {students_count}")
        print(f"Total Teachers: {teachers_count}")
        print(f"Total Parents: {parents_count}")
        
        invoices = self.fee_mgr.list_invoices()
        paid = sum(1 for inv in invoices if inv.status == "paid")
        pending = sum(1 for inv in invoices if inv.status in ["pending", "overdue"])
        
        print(f"\nTotal Invoices: {len(invoices)}")
        print(f"Paid: {paid}")
        print(f"Outstanding: {pending}")
        
        print(f"\nTotal Notifications: {len(self.comm_mgr.list_notifications())}")
        
        input("\nPress Enter to continue...")
    
    def run(self):

        if not self.login():
            print("\n✗ Login failed. Exiting.")
            sys.exit(1)
        
        while True:
            self.show_main_menu()
            choice = safe_string_input("Choose option: ")
            
            if choice == "0":
                print("\nLogging out... Goodbye!")
                break
            elif choice == "1":
                self.student_menu()
            elif choice == "2":
                self.teacher_menu()
            elif choice == "3":
                self.fee_menu()
            elif choice == "4":
                self.course_menu()
            elif choice == "5":
                self.communication_menu()
            elif choice == "6":
                self.settings_menu()
            else:
                print("Invalid option. Please try again.")
                input("Press Enter to continue...")

if __name__ == "__main__":
    portal = AdminPortal()
    try:
        portal.run()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ An error occurred: {str(e)}")
        input("Press Enter to continue...")
