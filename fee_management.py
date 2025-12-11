from utils import (
    load_from_pickle, save_to_pickle, safe_string_input, safe_int_input, FEES_FILE
)
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime

class SubjectFee:

    def __init__(self, subject: str, amount: float):
        self.subject = subject
        self.amount = amount

class Particular:

    def __init__(self, name: str, amount: float, description: str = ""):
        self.name = name
        self.amount = amount
        self.description = description
        self.created_date = datetime.now().strftime("%Y-%m-%d")

class FeeStructure:

    def __init__(self, course_code: str, year: int):
        self.course_code = course_code
        self.year = year
        self.subject_fees = {}  
        self.selected_particulars = []  
        self.created_date = datetime.now().strftime("%Y-%m-%d")
    
    def add_subject_fee(self, subject: str, amount: float) -> Tuple[bool, str]:
    
        if amount <= 0:
            return False, "Subject fee must be greater than 0"
        
        self.subject_fees[subject] = SubjectFee(subject, amount)
        return True, f"Subject '{subject}' fee set to ${amount:.2f}"
    
    def add_particular(self, particular_name: str) -> Tuple[bool, str]:
      
        if particular_name in self.selected_particulars:
            return False, f"Particular '{particular_name}' already included"
        
        self.selected_particulars.append(particular_name)
        return True, f"Particular '{particular_name}' added"
    
    def remove_particular(self, particular_name: str) -> Tuple[bool, str]:
  
        if particular_name not in self.selected_particulars:
            return False, f"Particular '{particular_name}' not found"
        
        self.selected_particulars.remove(particular_name)
        return True, f"Particular '{particular_name}' removed"
    
    def get_section_key(self) -> str:
       
        return f"{self.course_code}-{self.year}"

class Invoice:

    def __init__(self, invoice_id: str, student_id: str, course_code: str, year: int, 
                 amount: float, due_date: str):
        self.invoice_id = invoice_id
        self.student_id = student_id
        self.course_code = course_code
        self.year = year
        self.amount = amount
        self.due_date = due_date
        self.issued_date = datetime.now().strftime("%Y-%m-%d")
        self.status = "pending"  
        self.payment_date = None
        self.breakdown = {}  

class Payment:

    def __init__(self, payment_id: str, invoice_id: str, amount: float):
        self.payment_id = payment_id
        self.invoice_id = invoice_id
        self.amount = amount
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.status = "confirmed"

class WorkloadRate:

    def __init__(self, subject: str, rate_per_day: float):
        self.subject = subject
        self.rate_per_day = rate_per_day

class Bonus:

    def __init__(self, bonus_id: str, name: str, amount: float):
        self.bonus_id = bonus_id
        self.name = name
        self.amount = amount

class EarningsConfig:

    def __init__(self):
        self.base_salary = 0.0
        self.overtime_rate = 1.5 
        self.bonuses = {} 

class DeductionConfig:
    
    def __init__(self):
        self.tax_rate = 0.0 
        self.sss_rate = 0.0  
        self.absence_deduction = 0.0 

class TeacherPayroll:
    
    def __init__(self, payroll_id: str, teacher_id: str, payout_period: str):
        self.payroll_id = payroll_id
        self.teacher_id = teacher_id
        self.payout_period = payout_period 
        
        self.days_present = 0
        self.workload_earnings = 0.0  
        self.selected_bonus_ids = []  
        self.bonus_amount = 0.0
        self.overtime_hours = 0.0
        self.overtime_earnings = 0.0

        self.base_salary = 0.0
        self.gross_salary = 0.0  
        
        self.tax_deduction = 0.0
        self.sss_deduction = 0.0
        self.absence_deduction = 0.0
        self.total_deductions = 0.0
        
        self.net_salary = 0.0
        self.payment_status = "paid" 
        self.payout_date = datetime.now().strftime("%Y-%m-%d")
        self.created_date = datetime.now().strftime("%Y-%m-%d")

class FeeManager:

    def __init__(self):
        data = load_from_pickle(FEES_FILE)
        self.fee_structures = data.get("fee_structures", {})  # (course-year) -> FeeStructure
        self.particulars = data.get("particulars", {})  # particular_name -> Particular
        self.invoices = data.get("invoices", {})
        self.payments = data.get("payments", {})
        
        self.teacher_payroll = data.get("teacher_payroll", {})  # payroll_id -> TeacherPayroll
        self.workload_rates = data.get("workload_rates", {})  # subject -> WorkloadRate
        self.earnings_config = data.get("earnings_config", EarningsConfig())
        self.deduction_config = data.get("deduction_config", DeductionConfig())
        
        self.invoice_counter = data.get("invoice_counter", 0)
        self.payment_counter = data.get("payment_counter", 0)
        self.payroll_counter = data.get("payroll_counter", 0)
    
    def save_data(self):
        data = {
            "fee_structures": self.fee_structures,
            "particulars": self.particulars,
            "invoices": self.invoices,
            "payments": self.payments,
            "teacher_payroll": self.teacher_payroll,
            "workload_rates": self.workload_rates,
            "earnings_config": self.earnings_config,
            "deduction_config": self.deduction_config,
            "invoice_counter": self.invoice_counter,
            "payment_counter": self.payment_counter,
            "payroll_counter": self.payroll_counter,
        }
        save_to_pickle(FEES_FILE, data)
    
    def create_particular(self, name: str, amount: float, description: str = "") -> Tuple[bool, str]:
        if not name or len(name) < 2:
            return False, "Particular name must be at least 2 characters"
        
        if amount <= 0:
            return False, "Particular amount must be greater than 0"
        
        if name in self.particulars:
            return False, "Particular already exists"
        
        particular = Particular(name, amount, description)
        self.particulars[name] = particular
        self.save_data()
        return True, f"Particular '{name}' created: ${amount:.2f}"
    
    def get_particular(self, name: str) -> Optional[Particular]:
        return self.particulars.get(name)
    
    def list_particulars(self) -> List[Particular]:
        return list(self.particulars.values())
    
    def update_particular(self, name: str, amount: float = None, 
                         description: str = None) -> Tuple[bool, str]:
        if name not in self.particulars:
            return False, "Particular not found"
        
        particular = self.particulars[name]
        
        if amount is not None and amount > 0:
            particular.amount = amount
        if description is not None:
            particular.description = description
        
        self.save_data()
        return True, "Particular updated"
    
    def delete_particular(self, name: str) -> Tuple[bool, str]:
        if name not in self.particulars:
            return False, "Particular not found"
        
        del self.particulars[name]
        self.save_data()
        return True, "Particular deleted"
    
    def create_fee_structure(self, course_code: str, year: int) -> Tuple[bool, FeeStructure]:
        if not course_code or len(course_code) < 2:
            return False, "Course code required"
        
        if year < 1 or year > 4:
            return False, "Year must be between 1-4"
        
        section_key = f"{course_code}-{year}"
        
        if section_key in self.fee_structures:
            return False, "Fee structure already exists for this COURSE-YEAR"
        
        fee_structure = FeeStructure(course_code, year)
        self.fee_structures[section_key] = fee_structure
        self.save_data()
        return True, fee_structure
    
    def get_fee_structure(self, course_code: str, year: int) -> Optional[FeeStructure]:
        section_key = f"{course_code}-{year}"
        return self.fee_structures.get(section_key)
    
    def list_fee_structures(self) -> List[FeeStructure]:
        return list(self.fee_structures.values())
    
    def add_subject_fee_to_structure(self, course_code: str, year: int, 
                                     subject: str, amount: float) -> Tuple[bool, str]:
        fee_structure = self.get_fee_structure(course_code, year)
        if fee_structure is None:
            return False, "Fee structure not found"
        
        success, msg = fee_structure.add_subject_fee(subject, amount)
        if success:
            self.save_data()
        return success, msg
    
    def add_particular_to_structure(self, course_code: str, year: int, 
                                    particular_name: str) -> Tuple[bool, str]:
        fee_structure = self.get_fee_structure(course_code, year)
        if fee_structure is None:
            return False, "Fee structure not found"
        
        if particular_name not in self.particulars:
            return False, "Particular not found"
        
        success, msg = fee_structure.add_particular(particular_name)
        if success:
            self.save_data()
        return success, msg
    
    def remove_particular_from_structure(self, course_code: str, year: int, 
                                        particular_name: str) -> Tuple[bool, str]:
        fee_structure = self.get_fee_structure(course_code, year)
        if fee_structure is None:
            return False, "Fee structure not found"
        
        success, msg = fee_structure.remove_particular(particular_name)
        if success:
            self.save_data()
        return success, msg
    
    def calculate_total_fee(self, course_code: str, year: int) -> float:
        fee_structure = self.get_fee_structure(course_code, year)
        if fee_structure is None:
            return 0.0
        
        total = 0.0
        
        for subject_fee in fee_structure.subject_fees.values():
            total += subject_fee.amount
        
        for particular_name in fee_structure.selected_particulars:
            particular = self.particulars.get(particular_name)
            if particular:
                total += particular.amount
        
        return total
    
    def get_fee_breakdown(self, course_code: str, year: int) -> Dict[str, float]:
        fee_structure = self.get_fee_structure(course_code, year)
        if fee_structure is None:
            return {}
        
        breakdown = {}
        
        for subject_name, subject_fee in fee_structure.subject_fees.items():
            breakdown[f"Subject: {subject_name}"] = subject_fee.amount
        
        for particular_name in fee_structure.selected_particulars:
            particular = self.particulars.get(particular_name)
            if particular:
                breakdown[f"Particular: {particular_name}"] = particular.amount
        
        return breakdown
    
    def delete_fee_structure(self, course_code: str, year: int) -> Tuple[bool, str]:
        section_key = f"{course_code}-{year}"
        if section_key not in self.fee_structures:
            return False, "Fee structure not found"
        
        del self.fee_structures[section_key]
        self.save_data()
        return True, "Fee structure deleted"
    
    def generate_invoices_for_section(self, course_code: str, year: int, 
                                      students: List, due_date: str) -> Tuple[bool, List[str]]:
        total_fee = self.calculate_total_fee(course_code, year)
        
        if total_fee <= 0:
            return False, ["No fee structure defined for this COURSE-YEAR"]
        
        invoice_ids = []
        breakdown = self.get_fee_breakdown(course_code, year)
        
        for student in students:
            self.invoice_counter += 1
            invoice_id = f"INV{str(self.invoice_counter).zfill(6)}"
            
            invoice = Invoice(invoice_id, student.student_id, course_code, year, 
                            total_fee, due_date)
            invoice.breakdown = breakdown
            
            self.invoices[invoice_id] = invoice
            invoice_ids.append(invoice_id)
        
        self.save_data()
        return True, invoice_ids
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        return self.invoices.get(invoice_id)
    
    def get_student_invoices(self, student_id: str) -> List[Invoice]:
        return [inv for inv in self.invoices.values() if inv.student_id == student_id]
    
    def get_section_invoices(self, course_code: str, year: int) -> List[Invoice]:
        return [inv for inv in self.invoices.values() 
                if inv.course_code == course_code and inv.year == year]
    
    def list_invoices(self) -> List[Invoice]:
        return list(self.invoices.values())
    
    def update_invoice_status(self, invoice_id: str, status: str) -> Tuple[bool, str]:
        if invoice_id not in self.invoices:
            return False, "Invoice not found"
        
        if status not in ["pending", "paid", "overdue"]:
            return False, "Invalid invoice status"
        
        invoice = self.invoices[invoice_id]
        invoice.status = status
        
        if status == "paid":
            invoice.payment_date = datetime.now().strftime("%Y-%m-%d")
        
        self.save_data()
        return True, f"Invoice status updated to {status}"
    
    def record_payment(self, invoice_id: str, amount: float) -> Tuple[bool, str]:
        if invoice_id not in self.invoices:
            return False, "Invoice not found"
        
        invoice = self.invoices[invoice_id]
        
        if amount <= 0:
            return False, "Payment amount must be greater than 0"
        
        if amount > invoice.amount:
            return False, f"Payment amount exceeds invoice amount (${invoice.amount:.2f})"
        
        self.payment_counter += 1
        payment_id = f"PAY{str(self.payment_counter).zfill(6)}"
        
        payment = Payment(payment_id, invoice_id, amount)
        self.payments[payment_id] = payment
        
        if amount == invoice.amount:
            invoice.status = "paid"
            invoice.payment_date = datetime.now().strftime("%Y-%m-%d")
        
        self.save_data()
        return True, payment_id
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self.payments.get(payment_id)
    
    def get_invoice_payments(self, invoice_id: str) -> List[Payment]:
        return [p for p in self.payments.values() if p.invoice_id == invoice_id]
    
    def list_payments(self) -> List[Payment]:
        return list(self.payments.values())
    
    def get_total_paid(self, invoice_id: str) -> float:
        payments = self.get_invoice_payments(invoice_id)
        return sum(p.amount for p in payments)
    
    def set_workload_rate(self, subject: str, rate_per_day: float) -> Tuple[bool, str]:
        if not subject or rate_per_day <= 0:
            return False, "Invalid subject or rate"
        
        self.workload_rates[subject] = WorkloadRate(subject, rate_per_day)
        self.save_data()
        return True, f"Workload rate for {subject} set to ${rate_per_day:.2f}/day"
    
    def get_workload_rate(self, subject: str) -> Optional[WorkloadRate]:
        return self.workload_rates.get(subject)
    
    def list_workload_rates(self) -> List[WorkloadRate]:
        return list(self.workload_rates.values())
    
    def set_base_salary(self, amount: float) -> Tuple[bool, str]:
        if amount < 0:
            return False, "Base salary cannot be negative"
        
        self.earnings_config.base_salary = amount
        self.save_data()
        return True, f"Base salary set to ${amount:.2f}"
    
    def set_overtime_rate(self, multiplier: float) -> Tuple[bool, str]:
        if multiplier <= 0:
            return False, "Multiplier must be positive"
        
        self.earnings_config.overtime_rate = multiplier
        self.save_data()
        return True, f"Overtime rate set to {multiplier}x"
    
    def create_bonus(self, name: str, amount: float) -> Tuple[bool, str]:
        if not name or amount <= 0:
            return False, "Invalid bonus name or amount"
        
        bonus_id = f"BONUS-{len(self.earnings_config.bonuses) + 1}"
        bonus = Bonus(bonus_id, name, amount)
        self.earnings_config.bonuses[bonus_id] = bonus
        self.save_data()
        return True, bonus_id
    
    def list_bonuses(self) -> List[Bonus]:
        return list(self.earnings_config.bonuses.values())
    
    def delete_bonus(self, bonus_id: str) -> Tuple[bool, str]:
        if bonus_id not in self.earnings_config.bonuses:
            return False, "Bonus not found"
        
        del self.earnings_config.bonuses[bonus_id]
        self.save_data()
        return True, "Bonus deleted"
    
    def set_tax_rate(self, tax_rate: float) -> Tuple[bool, str]:
        if tax_rate < 0:
            return False, "Tax rate cannot be negative"
        
        self.deduction_config.tax_rate = tax_rate
        self.save_data()
        return True, f"Tax rate set to {tax_rate}%"
    
    def set_sss_rate(self, sss_rate: float) -> Tuple[bool, str]:
        if sss_rate < 0:
            return False, "SSS rate cannot be negative"
        
        self.deduction_config.sss_rate = sss_rate
        self.save_data()
        return True, f"SSS rate set to {sss_rate}%"
    
    def set_absence_deduction(self, amount_per_day: float) -> Tuple[bool, str]:
        if amount_per_day < 0:
            return False, "Absence deduction cannot be negative"
        
        self.deduction_config.absence_deduction = amount_per_day
        self.save_data()
        return True, f"Absence deduction set to ${amount_per_day:.2f}/day"
    
    def create_teacher_payroll(self, teacher_id: str, payout_period: str) -> Tuple[bool, str]:
        if not teacher_id or not payout_period:
            return False, "Teacher ID and payout period required"
        
        for payroll in self.teacher_payroll.values():
            if payroll.teacher_id == teacher_id and payroll.payout_period == payout_period:
                return False, f"Teacher already has payroll for {payout_period}"
        
        self.payroll_counter += 1
        payroll_id = f"PAYROLL-{str(self.payroll_counter).zfill(6)}"
        
        payroll = TeacherPayroll(payroll_id, teacher_id, payout_period)
        payroll.base_salary = self.earnings_config.base_salary
        self.teacher_payroll[payroll_id] = payroll
        
        self.save_data()
        return True, payroll_id
    
    def get_teacher_payroll(self, payroll_id: str) -> Optional[TeacherPayroll]:
        return self.teacher_payroll.get(payroll_id)
    
    def get_teacher_payroll_by_period(self, teacher_id: str, payout_period: str) -> Optional[TeacherPayroll]:
        for payroll in self.teacher_payroll.values():
            if payroll.teacher_id == teacher_id and payroll.payout_period == payout_period:
                return payroll
        return None
    
    def get_teacher_all_payroll(self, teacher_id: str) -> List[TeacherPayroll]:
        return [p for p in self.teacher_payroll.values() if p.teacher_id == teacher_id]
    
    def list_all_payroll(self) -> List[TeacherPayroll]:
        return list(self.teacher_payroll.values())
    
    def calculate_payroll(self, payroll_id: str, days_present: int, 
                         subjects: List[str], selected_bonus_ids: List[str] = None,
                         overtime_hours: float = 0.0) -> Tuple[bool, str]:
        if payroll_id not in self.teacher_payroll:
            return False, "Payroll not found"
        
        payroll = self.teacher_payroll[payroll_id]
        
        if days_present < 0:
            return False, "Days present cannot be negative"
        
        payroll.days_present = days_present
        payroll.workload_earnings = 0.0
        
        for subject in subjects:
            workload_rate = self.get_workload_rate(subject)
            if not workload_rate:
                return False, f"No workload rate set for {subject}"
            payroll.workload_earnings += days_present * workload_rate.rate_per_day
        
        if overtime_hours > 0:
            hourly_base_rate = payroll.base_salary / (8 * 14)
            payroll.overtime_earnings = overtime_hours * hourly_base_rate * self.earnings_config.overtime_rate
        
        payroll.overtime_hours = overtime_hours
        
        payroll.selected_bonus_ids = selected_bonus_ids or []
        payroll.bonus_amount = sum(self.earnings_config.bonuses[bid].amount 
                                  for bid in selected_bonus_ids 
                                  if bid in self.earnings_config.bonuses)
        
        payroll.gross_salary = (payroll.base_salary + payroll.workload_earnings + 
                               payroll.bonus_amount + payroll.overtime_earnings)
        
        payroll.tax_deduction = payroll.gross_salary * (self.deduction_config.tax_rate / 100)
        payroll.sss_deduction = payroll.gross_salary * (self.deduction_config.sss_rate / 100)
        payroll.absence_deduction = (14 - days_present) * self.deduction_config.absence_deduction  # 14 days per fortnight
        
        payroll.total_deductions = (payroll.tax_deduction + payroll.sss_deduction + 
                                   payroll.absence_deduction)
        
        payroll.net_salary = payroll.gross_salary - payroll.total_deductions
        
        self.save_data()
        return True, f"Payroll calculated: ${payroll.net_salary:.2f}"
    
    def finalize_payroll(self, payroll_id: str) -> Tuple[bool, str]:

        if payroll_id not in self.teacher_payroll:
            return False, "Payroll record not found"
        
        payroll = self.teacher_payroll[payroll_id]
        payroll.payout_date = datetime.now().strftime("%Y-%m-%d")
        
        self.save_data()
        return True, "Payroll finalized"
    
    def get_payroll_breakdown(self, payroll_id: str) -> Optional[Dict]:

        payroll = self.get_teacher_payroll(payroll_id)
        if not payroll:
            return None
        
        return {
            "payroll_id": payroll.payroll_id,
            "teacher_id": payroll.teacher_id,
            "payout_period": payroll.payout_period,
            "base_salary": payroll.base_salary,
            "workload_earnings": payroll.workload_earnings,
            "bonus_amount": payroll.bonus_amount,
            "overtime_earnings": payroll.overtime_earnings,
            "gross_salary": payroll.gross_salary,
            "tax_deduction": payroll.tax_deduction,
            "sss_deduction": payroll.sss_deduction,
            "absence_deduction": payroll.absence_deduction,
            "total_deductions": payroll.total_deductions,
            "net_salary": payroll.net_salary,
            "payment_status": payroll.payment_status,
        }

    def get_total_fees_collected(self) -> float:

        total = 0.0
        for invoice in self.invoices.values():
            if invoice.status == "paid":
                total += invoice.amount
        return total
    
    def get_outstanding_fees(self) -> float:
        total = 0.0
        for invoice in self.invoices.values():
            if invoice.status in ["pending", "overdue"]:
                total += invoice.amount
        return total
    
    def get_total_payroll_expenses(self, payout_period: str = None) -> float:
        total = 0.0
        for payroll in self.teacher_payroll.values():
            if payout_period is None or payroll.payout_period == payout_period:
                total += payroll.net_salary
        return total
    
    def get_financial_summary(self) -> Dict[str, float]:
        return {
            "total_fees_collected": self.get_total_fees_collected(),
            "outstanding_fees": self.get_outstanding_fees(),
            "total_invoices": len(self.invoices),
            "paid_invoices": sum(1 for inv in self.invoices.values() if inv.status == "paid"),
            "pending_invoices": sum(1 for inv in self.invoices.values() if inv.status == "pending"),
            "total_payments": len(self.payments),
            "total_payroll_expenses": self.get_total_payroll_expenses()
        }
