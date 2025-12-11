"""
Parent & Communication Portal module for the College Academic Management System.
Handles notifications, parent accounts, and student-parent communications.
"""

from utils import (
    load_from_pickle, save_to_pickle, generate_id, validate_password,
    safe_string_input, PARENTS_FILE, NOTIFICATIONS_FILE
)
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib


class ParentAccount:
    """Parent account profile."""
    
    def __init__(self, parent_id: str, name: str, email: str, phone: str, 
                 student_ids: List[str]):
        self.parent_id = parent_id
        self.name = name
        self.email = email
        self.phone = phone
        self.student_ids = student_ids  # IDs of children
        self.account_status = "active"
        self.created_date = datetime.now().strftime("%Y-%m-%d")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display."""
        return {
            "id": self.parent_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "children": len(self.student_ids)
        }


class Notification:
    """Notification record."""
    
    def __init__(self, notification_id: str, recipient_id: str, subject: str, 
                 message: str, notification_type: str):
        self.notification_id = notification_id
        self.recipient_id = recipient_id  # Parent ID
        self.subject = subject
        self.message = message
        self.notification_type = notification_type  # grade, attendance, fee, event, etc.
        self.sent_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.read = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.notification_id,
            "subject": self.subject,
            "type": self.notification_type,
            "sent": self.sent_date,
            "read": self.read
        }


class CommunicationManager:
    """Manages parent accounts and notifications."""
    
    def __init__(self):
        self.parents = load_from_pickle(PARENTS_FILE)
        notifications_data = load_from_pickle(NOTIFICATIONS_FILE)
        self.notifications = notifications_data.get("notifications", {})
        self.notification_counter = notifications_data.get("counter", 0)
    
    def save_data(self):
        """Save parent accounts and notifications."""
        save_to_pickle(PARENTS_FILE, self.parents)
        save_to_pickle(NOTIFICATIONS_FILE, {
            "notifications": self.notifications,
            "counter": self.notification_counter
        })
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    # Parent Account Methods
    def create_parent_account(self, name: str, email: str, phone: str, 
                             student_ids: List[str], password: str = None) -> Tuple[bool, str]:
        """
        Create parent account (auto-generated password if not provided).
        Auto-generates ID (099-xxxxxxx).
        A student can only be linked to one parent.
        
        Returns: (success, parent_id_or_error)
        """
        if not name or len(name) < 2:
            return False, "Parent name must be at least 2 characters"
        
        if not email or "@" not in email:
            return False, "Valid email is required"
        
        if not phone:
            return False, "Phone number is required"
        
        if not student_ids:
            return False, "At least one student ID must be provided"
        
        # Check if any student is already linked to another parent
        for student_id in student_ids:
            if student_id == "PLACEHOLDER":
                continue
            for parent_data in self.parents.values():
                if student_id in parent_data["student_ids"]:
                    other_parent = parent_data["profile"]
                    return False, f"Student {student_id} is already linked to parent {other_parent.parent_id} ({other_parent.name})"
        
        # Generate parent ID
        parent_id = generate_id("099", self.parents)
        
        # Use provided password or generate temporary one
        if password:
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                return False, error_msg
        else:
            # Generate temporary password
            password = f"Parent@{parent_id[-6:]}"
        
        hashed_password = self._hash_password(password)
        
        # Create parent account
        parent = ParentAccount(parent_id, name, email, phone, student_ids)
        
        self.parents[parent_id] = {
            "profile": parent,
            "password": hashed_password,
            "student_ids": student_ids
        }
        
        self.save_data()
        return True, parent_id
    
    def get_parent(self, parent_id: str) -> Optional[ParentAccount]:
        """Get parent account by ID."""
        if parent_id not in self.parents:
            return None
        return self.parents[parent_id]["profile"]
    
    def get_parent_by_email(self, email: str) -> Optional[ParentAccount]:
        """Get parent account by email."""
        for parent_data in self.parents.values():
            if parent_data["profile"].email == email:
                return parent_data["profile"]
        return None
    
    def list_parents(self) -> List[ParentAccount]:
        """Get all parent accounts."""
        return [data["profile"] for data in self.parents.values()]
    
    def update_parent(self, parent_id: str, name: str = None, email: str = None,
                     phone: str = None) -> Tuple[bool, str]:
        """Update parent information."""
        if parent_id not in self.parents:
            return False, "Parent not found"
        
        parent = self.parents[parent_id]["profile"]
        
        if name:
            parent.name = name
        if email:
            parent.email = email
        if phone:
            parent.phone = phone
        
        self.save_data()
        return True, "Parent account updated"
    
    def add_student_to_parent(self, parent_id: str, student_id: str) -> Tuple[bool, str]:
        """Add a student to parent's account. A student can only have one parent."""
        if parent_id not in self.parents:
            return False, "Parent not found"
        
        student_ids = self.parents[parent_id]["student_ids"]
        
        if student_id in student_ids:
            return False, "Student already linked to this parent"
        
        # Check if student is already linked to another parent
        for pid, parent_data in self.parents.items():
            if pid != parent_id and student_id in parent_data["student_ids"]:
                other_parent = parent_data["profile"]
                return False, f"Student is already linked to parent {pid} ({other_parent.name}). Only one parent per student allowed."
        
        student_ids.append(student_id)
        self.save_data()
        return True, "Student added to parent account"
    
    def remove_student_from_parent(self, parent_id: str, student_id: str) -> Tuple[bool, str]:
        """Remove a student from parent's account (unlink)."""
        if parent_id not in self.parents:
            return False, "Parent not found"
        
        student_ids = self.parents[parent_id]["student_ids"]
        
        if student_id not in student_ids:
            return False, "Student not linked to this parent"
        
        student_ids.remove(student_id)
        self.save_data()
        return True, "Student removed from parent account"
    
    def parent_login(self, parent_id: str, password: str) -> Tuple[bool, str]:
        """Authenticate parent login."""
        if parent_id not in self.parents:
            return False, "Invalid ID or password"
        
        parent_data = self.parents[parent_id]
        hashed_password = self._hash_password(password)
        
        if parent_data["password"] != hashed_password:
            return False, "Invalid ID or password"
        
        return True, parent_id
    
    def change_parent_password(self, parent_id: str, old_password: str,
                              new_password: str) -> Tuple[bool, str]:
        """Change parent password."""
        # Verify old password
        success, msg = self.parent_login(parent_id, old_password)
        if not success:
            return False, "Current password is incorrect"
        
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return False, error_msg
        
        hashed_password = self._hash_password(new_password)
        self.parents[parent_id]["password"] = hashed_password
        self.save_data()
        
        return True, "Password successfully changed"
    
    # Notification Methods
    def send_notification(self, parent_id: str, subject: str, message: str,
                         notification_type: str) -> Tuple[bool, str]:
        """Send a notification to a parent."""
        if parent_id not in self.parents:
            return False, "Parent not found"
        
        self.notification_counter += 1
        notification_id = f"NOTIF{str(self.notification_counter).zfill(6)}"
        
        notification = Notification(notification_id, parent_id, subject, message, notification_type)
        self.notifications[notification_id] = notification
        
        self.save_data()
        return True, notification_id
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        return self.notifications.get(notification_id)
    
    def get_parent_notifications(self, parent_id: str) -> List[Notification]:
        """Get all notifications for a parent."""
        return [n for n in self.notifications.values() if n.recipient_id == parent_id]
    
    def get_unread_notifications(self, parent_id: str) -> List[Notification]:
        """Get unread notifications for a parent."""
        return [n for n in self.notifications.values() 
                if n.recipient_id == parent_id and not n.read]
    
    def mark_notification_read(self, notification_id: str) -> Tuple[bool, str]:
        """Mark notification as read."""
        if notification_id not in self.notifications:
            return False, "Notification not found"
        
        self.notifications[notification_id].read = True
        self.save_data()
        return True, "Notification marked as read"
    
    def list_notifications(self) -> List[Notification]:
        """Get all notifications."""
        return list(self.notifications.values())
    
    # Bulk Notification Methods
    def notify_parent_about_grades(self, parent_id: str, student_name: str, 
                                   subject: str, grade: float) -> Tuple[bool, str]:
        """Send grade notification to parent."""
        subject_line = f"Grade Update: {student_name}"
        message = f"{student_name}'s grade for {subject} has been updated: {grade:.2f}"
        return self.send_notification(parent_id, subject_line, message, "grade")
    
    def notify_parent_about_attendance(self, parent_id: str, student_name: str,
                                      subject: str, status: str) -> Tuple[bool, str]:
        """Send attendance notification to parent."""
        subject_line = f"Attendance Alert: {student_name}"
        message = f"{student_name} was marked {status} in {subject}"
        return self.send_notification(parent_id, subject_line, message, "attendance")
    
    def notify_parent_about_fees(self, parent_id: str, student_name: str,
                                amount: float, due_date: str) -> Tuple[bool, str]:
        """Send fee notification to parent."""
        subject_line = f"Fee Due: {student_name}"
        message = f"An invoice of ${amount:.2f} is due by {due_date} for {student_name}"
        return self.send_notification(parent_id, subject_line, message, "fee")
    
    def notify_parent_about_event(self, parent_ids: List[str], event_name: str,
                                 event_date: str, description: str) -> Tuple[int, str]:
        """Send event notification to multiple parents."""
        success_count = 0
        for parent_id in parent_ids:
            success, msg = self.send_notification(parent_id, f"School Event: {event_name}",
                                                  f"{event_name} on {event_date}: {description}",
                                                  "event")
            if success:
                success_count += 1
        
        return success_count, f"Event notification sent to {success_count}/{len(parent_ids)} parents"
    
    def notify_parent_about_holiday(self, parent_ids: List[str], holiday_name: str,
                                   dates: str) -> Tuple[int, str]:
        """Send holiday notification to multiple parents."""
        success_count = 0
        for parent_id in parent_ids:
            success, msg = self.send_notification(parent_id, f"Holiday: {holiday_name}",
                                                  f"{holiday_name} from {dates}",
                                                  "holiday")
            if success:
                success_count += 1
        
        return success_count, f"Holiday notification sent to {success_count}/{len(parent_ids)} parents"
