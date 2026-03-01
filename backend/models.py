# # backend/models.py

# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash

# # ⚠️ We don't create 'db' here - we expect it to be passed in or imported
# # This avoids circular imports

# db = SQLAlchemy()  # ← Create db instance here (but don't init yet)


# class User(db.Model):
#     """
#     User model representing a registered user in the system.
#     """
#     __tablename__ = 'users'  # Optional: explicitly name the table
    
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     username = db.Column(db.String(80), unique=True, nullable=False, index=True)
#     password = db.Column(db.String(120), nullable=False)
    
#     def __repr__(self):
#         return f'<User {self.username}>'
    
#     def set_password(self, password):
#         """Hash and set the user's password."""
#         self.password = generate_password_hash(password)
    
#     def check_password(self, password):
#         """Check if a plaintext password matches the stored hash."""
#         return check_password_hash(self.password, password)
    
#     def to_dict(self):
#         """Convert user object to dictionary (for API responses)."""
#         return {
#             'id': self.id,
#             'username': self.username
#             # Never return password in API responses!
#         }


# backend/models.py

# ✅ CORRECT IMPORTS
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# ✅ Create db instance HERE (don't import from elsewhere)
db = SQLAlchemy()  # ← This is the fix!

# --------------------------------------------------------------------------
# 1. CORE AUTH & POLYMORPHISM BASE
# --------------------------------------------------------------------------

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    # ✅ Auto-generate fs_uniquifier (Flask-Security requirement)
    fs_uniquifier = db.Column(db.String(255), nullable=False, unique=True, default=lambda: uuid.uuid4().hex)

    # Polymorphic identity: 'doctor', 'patient', 'accountant', 'receptionist', 'admin'
    type = db.Column(db.String(50))

    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy=True))

    # === HELPER METHODS ===
    
    def set_password(self, password):
        """Hash and set password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password, password)
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def to_dict(self):
        """Safe API response (no password)."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'type': self.type,
            'active': self.active,
            'roles': [role.name for role in self.roles],
            # Type-specific fields (use getattr to avoid errors)
            'service_id': getattr(self, 'service_id', None),
            'specialization': getattr(self, 'specialization', None),
            'license_number': getattr(self, 'license_number', None),
        }

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))


# --------------------------------------------------------------------------
# 2. STAKEHOLDER MODELS (Joined Table Inheritance from User)
# --------------------------------------------------------------------------

class Doctor(User):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    specialization = db.Column(db.String(100))
    license_number = db.Column(db.String(50), unique=True)

    availabilities = db.relationship('Availability', backref='doctor', lazy=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    __mapper_args__ = {'polymorphic_identity': 'doctor'}


class Patient(User):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    # Unique Service ID format: SVC-2026-XXXX (assigned by Receptionist at registration)
    service_id = db.Column(db.String(20), unique=True, nullable=False)
    contact_info = db.Column(db.String(15))

    # IVF Cycle Stage progression:
    # Onboarding -> Baseline -> Stimulation -> Monitoring -> Trigger -> Retrieval -> Transfer
    current_cycle_stage = db.Column(db.String(50), default='Onboarding')

    # Convenience backref: patient.appointments
    appointments = db.relationship('Appointment', backref='patient', lazy=True,
                                   foreign_keys='Appointment.patient_id')

    __mapper_args__ = {'polymorphic_identity': 'patient'}


class Receptionist(User):
    __tablename__ = 'receptionist'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    desk_id = db.Column(db.String(20))  # Operational hub identifier

    __mapper_args__ = {'polymorphic_identity': 'receptionist'}


class Accountant(User):
    __tablename__ = 'accountant'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    # Strictly blocked from clinical history via route-level logic and query isolation

    __mapper_args__ = {'polymorphic_identity': 'accountant'}


class Administrator(User):
    __tablename__ = 'administrator'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    # Responsible for doctor onboarding, audit log review, and stats visibility

    __mapper_args__ = {'polymorphic_identity': 'admin'}


# --------------------------------------------------------------------------
# 3. AVAILABILITY & SCHEDULING (7-Day FCFS)
# --------------------------------------------------------------------------

class Availability(db.Model):
    __tablename__ = 'availability'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration_minutes = db.Column(db.Integer, default=30)  # Duration of each bookable slot


class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)  # Stored explicitly for overlap detection

    # Appointment statuses: 'waiting', 'in-session', 'completed', 'cancelled'
    status = db.Column(db.String(20), default='waiting')

    # Walk-in flag: True = injected into FCFS queue by Receptionist; False = self-booked via portal
    is_walkin = db.Column(db.Boolean, default=False)

    # Clinical Data — isolated from Accountant at the route/query level
    clinical_notes = db.Column(db.Text)
    stage_at_visit = db.Column(db.String(50))  # IVF stage captured at time of visit

    # Backref: appointment.prescription (one-to-one)
    prescription = db.relationship('Prescription', backref='appointment',
                                   uselist=False, lazy=True)

    # Backref: appointment.invoice (one-to-one)
    invoice = db.relationship('Invoice', backref='appointment',
                              uselist=False, lazy=True)


# --------------------------------------------------------------------------
# 4. AI-ENHANCED DOCUMENTATION (Gemini Clerical Verification)
# --------------------------------------------------------------------------

class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'),
                               nullable=False, unique=True)  # One prescription per appointment
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    raw_draft = db.Column(db.Text)         # Original doctor input before AI review
    verified_content = db.Column(db.Text)  # Gemini-verified and typo-corrected text
    is_finalized = db.Column(db.Boolean, default=False)  # Doctor must explicitly finalize
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Direct relationships for clean querying without chaining through Appointment
    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', lazy=True))
    patient = db.relationship('Patient', backref=db.backref('prescriptions', lazy=True))


# --------------------------------------------------------------------------
# 5. FINANCIALS
# --------------------------------------------------------------------------

class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = db.Column(db.Integer, primary_key=True)

    # Linked via Service ID (not patient name) to enforce PHI isolation for Accountant
    patient_service_id = db.Column(db.String(20), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'),
                               nullable=False, unique=True)  # Always appointment-driven

    amount = db.Column(db.Float, nullable=False)
    service_code = db.Column(db.String(20))  # e.g., IVF-STAGE-03 — only identifier visible to Accountant

    # Payment status: 'pending', 'paid'
    status = db.Column(db.String(20), default='pending')

    # Source of payment: 'portal' (patient self-pay) or 'front_desk' (receptionist cash toggle)
    # NULL until payment is confirmed
    payment_source = db.Column(db.String(20))

    date_generated = db.Column(db.DateTime, default=datetime.utcnow)
    date_paid = db.Column(db.DateTime, nullable=True)  # Populated when status flips to 'paid'


# --------------------------------------------------------------------------
# 6. AUDIT LOGS
# --------------------------------------------------------------------------

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(45))   # Supports both IPv4 and IPv6
    endpoint = db.Column(db.String(100))    # e.g., /api/v1/generate-bill
    action = db.Column(db.String(255))      # Human-readable description of the action