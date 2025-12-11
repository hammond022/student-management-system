"""
Utility functions for the College Academic Management System.
Handles data persistence, validation, ID generation, and pagination.
"""

import os
import pickle
import re
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = "data"
STUDENTS_FILE = os.path.join(DATA_DIR, "students.pkl")
TEACHERS_FILE = os.path.join(DATA_DIR, "teachers.pkl")
PARENTS_FILE = os.path.join(DATA_DIR, "parents.pkl")
COURSES_FILE = os.path.join(DATA_DIR, "courses.pkl")
FEES_FILE = os.path.join(DATA_DIR, "fees.pkl")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.pkl")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.pkl")


def ensure_data_dir():
    """Ensure data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def save_to_pickle(file_path: str, data: Any) -> None:
    """Save data to pickle file."""
    ensure_data_dir()
    try:
        with open(file_path, "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        raise Exception(f"Error saving data to {file_path}: {str(e)}")


def load_from_pickle(file_path: str) -> Any:
    """Load data from pickle file. Returns empty dict if file doesn't exist."""
    ensure_data_dir()
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise Exception(f"Error loading data from {file_path}: {str(e)}")


def generate_id(id_prefix: str, existing_ids: Dict[str, Any]) -> str:
    """
    Generate a 10-digit ID with format: PREFIX + 7 digits.
    Prefixes: 022 (student), 011 (teacher), 099 (parent)
    Example: 0221234567
    """
    if not id_prefix or len(id_prefix) != 3:
        raise ValueError("ID prefix must be exactly 3 digits")
    
    # Extract all IDs and get the highest number
    max_number = 0
    for user_id in existing_ids.keys():
        if user_id.startswith(id_prefix):
            try:
                number = int(user_id[3:])
                if number > max_number:
                    max_number = number
            except ValueError:
                pass
    
    # Generate next ID
    next_number = max_number + 1
    new_id = id_prefix + str(next_number).zfill(7)
    return new_id


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password requirements:
    - At least 6 characters
    - At least 1 uppercase letter
    - At least 3 numbers
    - At least 1 special character (!@#$%^&*)
    
    Returns: (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least 1 uppercase letter"
    
    if sum(1 for c in password if c.isdigit()) < 3:
        return False, "Password must contain at least 3 numbers"
    
    if not any(c in "!@#$%^&*" for c in password):
        return False, "Password must contain at least 1 special character (!@#$%^&*)"
    
    return True, ""


def validate_section_format(section: str) -> bool:
    """
    Validate section format: COURSE-YEAR-SECTION
    Example: BSIT-3-1 (BSIT course, 3rd year, section 1)
    Year must be 1-4, section can be any number.
    """
    parts = section.split("-")
    if len(parts) != 3:
        return False
    
    course, year, section_num = parts
    
    # Course should be alphanumeric
    if not course.isalnum() or len(course) == 0:
        return False
    
    # Year should be 1-4
    try:
        year_int = int(year)
        if year_int < 1 or year_int > 4:
            return False
    except ValueError:
        return False
    
    # Section number should be numeric
    try:
        int(section_num)
    except ValueError:
        return False
    
    return True


def paginate_list(items: List[Any], page: int, items_per_page: int = 9) -> Tuple[List[Any], int]:
    """
    Paginate a list and return items for the current page and total pages.
    
    Returns: (items_for_page, total_pages)
    """
    if items_per_page <= 0:
        items_per_page = 9
    
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    return items[start_idx:end_idx], total_pages


def get_year_name(year: int) -> str:
    """Convert year number to year name."""
    year_names = {1: "Freshman", 2: "Sophomore", 3: "Junior", 4: "Senior"}
    return year_names.get(year, f"Year {year}")


def format_section_display(course: str, year: int, section: int) -> str:
    """Format section for display: COURSE-YEAR-SECTION."""
    return f"{course}-{year}-{section}"


def calculate_activity_score(total_items: int, correct_answers: int) -> float:
    """Calculate activity score as percentage: (correct / total) * 100"""
    if total_items == 0:
        return 0.0
    return (correct_answers / total_items) * 100


def calculate_subject_grade(activities_scores: List[float], exam_scores: Dict[str, float], 
                           attendance: List[Tuple[str, str]] = None) -> float:
    """
    Calculate final subject grade:
    - 50% from activities average
    - 40% from exam average (Prelim, Midterm, Finals)
    - 10% from attendance (Present: 100%, Tardy: 50%, Absent: 0%)
    
    Returns average grade as float.
    """
    if not activities_scores and not exam_scores and not attendance:
        return 0.0
    
    activity_avg = sum(activities_scores) / len(activities_scores) if activities_scores else 0.0
    exam_avg = sum(exam_scores.values()) / len(exam_scores) if exam_scores else 0.0
    
    # Calculate attendance score
    if attendance:
        attendance_scores = []
        for date, status in attendance:
            if status.lower() == "present":
                attendance_scores.append(100.0)
            elif status.lower() == "tardy":
                attendance_scores.append(50.0)
            elif status.lower() == "absent":
                attendance_scores.append(0.0)
        attendance_avg = sum(attendance_scores) / len(attendance_scores) if attendance_scores else 0.0
    else:
        attendance_avg = 0.0
    
    final_grade = (activity_avg * 0.5) + (exam_avg * 0.4) + (attendance_avg * 0.1)
    return round(final_grade, 2)


def get_gpa(subject_grades: Dict[str, float]) -> float:
    """
    Calculate GPA from subject grades.
    Returns average of all subject grades.
    """
    if not subject_grades:
        return 0.0
    return round(sum(subject_grades.values()) / len(subject_grades), 2)


def clear_screen():
    """Clear the console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str):
    """Print a formatted section title."""
    print(f"\n--- {title} ---")


def safe_int_input(prompt: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Optional[int]:
    """
    Safely get integer input from user.
    Returns None if user enters invalid input.
    """
    try:
        value = input(prompt).strip()
        if value == "":
            return None
        
        num = int(value)
        
        if min_val is not None and num < min_val:
            print(f"Value must be at least {min_val}")
            return None
        
        if max_val is not None and num > max_val:
            print(f"Value must be at most {max_val}")
            return None
        
        return num
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return None


def safe_string_input(prompt: str, allow_empty: bool = False) -> Optional[str]:
    """
    Safely get string input from user.
    Returns None if user enters invalid input.
    """
    try:
        value = input(prompt).strip()
        
        if not value and not allow_empty:
            print("Input cannot be empty.")
            return None
        
        return value
    except Exception as e:
        print(f"Error reading input: {str(e)}")
        return None


def safe_float_input(prompt: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Optional[float]:
    """
    Safely get float input from user.
    Returns None if user enters invalid input.
    """
    try:
        value = float(input(prompt))
        
        if min_val is not None and value < min_val:
            print(f"Value must be at least {min_val}.")
            return None
        
        if max_val is not None and value > max_val:
            print(f"Value must be at most {max_val}.")
            return None
        
        return value
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return None
    except Exception as e:
        print(f"Error reading input: {str(e)}")
        return None


def get_full_name() -> Optional[str]:
    """
    Get full name from user (first name, last name, optional middle name).
    Returns formatted full name or None if cancelled.
    """
    first_name = safe_string_input("First name: ")
    if first_name is None:
        return None
    
    last_name = safe_string_input("Last name: ")
    if last_name is None:
        return None
    
    middle_name = safe_string_input("Middle name (optional): ", allow_empty=True)
    
    if middle_name:
        return f"{first_name} {middle_name} {last_name}"
    else:
        return f"{first_name} {last_name}"


def display_page(items: List[str], page: int, title: str = "") -> Tuple[int, Optional[int]]:
    """
    Display paginated items and handle navigation.
    
    Returns: (current_page, selected_option)
    selected_option is 0-8 for item selection (0-indexed), -1 for back, None for navigation
    """
    if title:
        print_section(title)
    
    paginated, total_pages = paginate_list(items, page)
    
    for i, item in enumerate(paginated, 1):
        print(f"{i}. {item}")
    
    print(f"\n[Page {page}/{total_pages}] (w: next, q: prev, 0: back, 1-9: select)")
    choice = input("Choose option: ").strip().lower()
    
    if choice == "q":
        return max(1, page - 1), None
    elif choice == "w":
        return min(total_pages, page + 1), None
    elif choice == "0":
        return page, -1
    else:
        try:
            option = int(choice)
            if 1 <= option <= len(paginated):
                return page, option - 1
            else:
                print("Invalid option.")
                return page, None
        except ValueError:
            print("Invalid input.")
            return page, None
