"""
Authentication module for the College Academic Management System.
Handles admin, teacher, and parent login, password recovery, and account creation.
"""

from utils import (
    load_from_pickle, save_to_pickle, generate_id, validate_password,
    safe_string_input, ADMINS_FILE
)
from typing import Dict, Optional, Tuple
import hashlib


class AuthManager:
    """Manages authentication for admins, teachers, and parents."""
    
    def __init__(self):
        self.admins = load_from_pickle(ADMINS_FILE)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def save_admins(self):
        """Save admins to pickle file."""
        save_to_pickle(ADMINS_FILE, self.admins)
    
    def admin_exists(self) -> bool:
        """Check if any admin account exists."""
        return len(self.admins) > 0
    
    def create_admin(self, username: str, password: str, 
                     security_questions: Dict[str, str]) -> Tuple[bool, str]:
        """
        Create a new admin account.
        
        Returns: (success, message_or_admin_id)
        """
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if username in self.admins:
            return False, "Username already exists"
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return False, error_msg
        
        if len(security_questions) != 3:
            return False, "Must provide 3 security questions and answers"
        
        # Generate admin ID
        admin_id = generate_id("011", self.admins)
        
        # Create admin record
        hashed_password = self._hash_password(password)
        self.admins[username] = {
            "id": admin_id,
            "password": hashed_password,
            "security_questions": security_questions,
            "role": "admin"
        }
        
        self.save_admins()
        return True, admin_id
    
    def admin_login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate admin login.
        
        Returns: (success, message_or_admin_id)
        """
        if username not in self.admins:
            return False, "Invalid username or password"
        
        admin = self.admins[username]
        hashed_password = self._hash_password(password)
        
        if admin["password"] != hashed_password:
            return False, "Invalid username or password"
        
        return True, admin["id"]
    
    def recover_password(self, username: str) -> Tuple[bool, str]:
        """
        Recover admin password using security questions.
        
        Returns: (success, message)
        """
        if username not in self.admins:
            return False, "Username not found"
        
        admin = self.admins[username]
        security_qs = admin["security_questions"]
        
        print("\n--- Password Recovery ---")
        print("Answer the following security questions to reset your password:\n")
        
        correct_answers = 0
        for i, (question, correct_answer) in enumerate(security_qs.items(), 1):
            user_answer = safe_string_input(f"Q{i}: {question}\nYour answer: ")
            
            if user_answer and user_answer.lower() == correct_answer.lower():
                correct_answers += 1
        
        if correct_answers < 3:
            return False, "Incorrect answers. Password recovery failed."
        
        # Ask for new password
        print("\n--- Set New Password ---")
        while True:
            new_password = safe_string_input("Enter new password: ")
            if not new_password:
                continue
            
            is_valid, error_msg = validate_password(new_password)
            if not is_valid:
                print(f"Password validation failed: {error_msg}")
                continue
            
            confirm = safe_string_input("Confirm password: ")
            if new_password != confirm:
                print("Passwords do not match. Try again.")
                continue
            
            break
        
        # Update password
        hashed_password = self._hash_password(new_password)
        admin["password"] = hashed_password
        self.save_admins()
        
        return True, "Password successfully reset. Please login with your new password."
    
    def change_password(self, username: str, old_password: str, 
                       new_password: str) -> Tuple[bool, str]:
        """Change admin password with old password verification."""
        # Verify old password
        success, msg = self.admin_login(username, old_password)
        if not success:
            return False, "Current password is incorrect"
        
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return False, error_msg
        
        hashed_password = self._hash_password(new_password)
        self.admins[username]["password"] = hashed_password
        self.save_admins()
        
        return True, "Password successfully changed"


def setup_first_admin() -> Tuple[bool, str]:
    """
    Setup first admin account on system initialization.
    
    Returns: (success, admin_id)
    """
    auth = AuthManager()
    
    if auth.admin_exists():
        return False, "Admin account already exists"
    
    print("\n" + "=" * 60)
    print("  FIRST TIME SETUP - CREATE ADMIN ACCOUNT")
    print("=" * 60)
    
    while True:
        username = safe_string_input("\nEnter admin username (min 3 characters): ")
        if username and len(username) >= 3:
            break
        print("Username must be at least 3 characters")
    
    while True:
        print("\n--- Password Requirements ---")
        print("- At least 6 characters")
        print("- At least 1 uppercase letter")
        print("- At least 3 numbers")
        print("- At least 1 special character (!@#$%^&*)")
        
        password = safe_string_input("\nEnter password: ")
        if not password:
            continue
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            print(f"Password validation failed: {error_msg}")
            continue
        
        confirm = safe_string_input("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Try again.")
            continue
        
        break
    
    print("\n--- Security Questions (for password recovery) ---")
    print("Create 3 security questions and answers that you can remember.")
    print("Example: 'What is your pet\\'s name?' with answer 'Fluffy'\n")
    
    security_questions = {}
    
    for i in range(3):
        while True:
            question = safe_string_input(f"Security Question {i+1}: ")
            if question and len(question) >= 5:
                break
            print("Question must be at least 5 characters long")
        
        while True:
            answer = safe_string_input(f"Answer to Question {i+1}: ")
            if answer and len(answer) >= 2:
                break
            print("Answer must be at least 2 characters long")
        
        security_questions[question] = answer
    
    success, result = auth.create_admin(username, password, security_questions)
    
    if success:
        print(f"\n✓ Admin account created successfully!")
        print(f"Admin ID: {result}")
        return True, result
    else:
        print(f"\n✗ Failed to create admin account: {result}")
        return False, result


def admin_login_prompt() -> Optional[str]:
    """
    Prompt for admin login and return admin ID if successful.
    Returns None if login fails or user exits.
    """
    auth = AuthManager()
    
    print("\n" + "=" * 60)
    print("  ADMIN LOGIN")
    print("=" * 60)
    
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        username = safe_string_input("\nUsername (0 to exit): ")
        
        if username == "0":
            return None
        
        if not username:
            continue
        
        password = safe_string_input("Password: ")
        if not password:
            continue
        
        success, result = auth.admin_login(username, password)
        
        if success:
            return result
        else:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"Login failed. {remaining} attempts remaining.")
            else:
                print("Maximum login attempts exceeded.")
                
                print("\nForgot password? (y/n): ", end="")
                if input().strip().lower() == "y":
                    recovery_username = safe_string_input("Enter your username: ")
                    if recovery_username:
                        success, msg = auth.recover_password(recovery_username)
                        print(msg)
                        if success:
                            # Try login again
                            return admin_login_prompt()
    
    return None
