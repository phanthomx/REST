# backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
# ✅ Import db AND all models from models.py
from models import db, User, Doctor, Patient, Receptionist, Accountant, Administrator, Role, UserRoles

import uuid
from datetime import datetime, time, date

app = Flask(__name__)

# CONFIG
app.config['SECRET_KEY'] = 'super-secret-key-change-in-prod'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-prod'
app.config['SECURITY_PASSWORD_SALT'] = 'another-secret-salt'

# ✅ INIT: Bind db to app (this connects the SQLAlchemy instance)
db.init_app(app)  # ← This is critical!

jwt = JWTManager(app)
CORS(app)
# === HELPER: Map type string to model class ===
def get_user_class_by_type(user_type):
    """Convert string type to actual model class for polymorphic creation."""
    type_map = {
        'doctor': Doctor,
        'patient': Patient,
        'receptionist': Receptionist,
        'accountant': Accountant,
        'admin': Administrator
    }
    return type_map.get(user_type, User)

# === HELPER: Generate Service ID for Patients ===
def generate_service_id():
    """Generate unique service ID: SVC-YYYY-XXXX format."""
    year = datetime.now().year
    # Simple counter (in production, use database sequence)
    import random
    return f"SVC-{year}-{random.randint(1000, 9999)}"

# CREATE DB + INITIAL ROLES (Run once on startup)
with app.app_context():
    db.create_all()
    
    # Create default roles if they don't exist
    roles_to_create = [
        ('admin', 'System Administrator'),
        ('doctor', 'Medical Doctor'),
        ('patient', 'Patient'),
        ('receptionist', 'Front Desk Staff'),
        ('accountant', 'Finance Staff')
    ]
    
    for role_name, description in roles_to_create:
        if not Role.query.filter_by(name=role_name).first():
            new_role = Role(name=role_name, description=description)
            db.session.add(new_role)
    
    db.session.commit()

# ==================== AUTH ROUTES ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user with polymorphic type."""
    data = request.json
    
    # Required fields
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    user_type = data.get('type', 'patient')  # Default to patient
    
    # Validate
    if not all([email, name, password]):
        return jsonify({"message": "Email, name, and password are required"}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400
    
    # Get the correct subclass (Doctor, Patient, etc.)
    UserClass = get_user_class_by_type(user_type)
    
    # Create new user instance
    new_user = UserClass(
        email=email,
        name=name,
        type=user_type,  # Required for polymorphic identity
        fs_uniquifier=uuid.uuid4().hex,  # Flask-Security requirement
        active=True
    )
    
    # Patient-specific: Generate service ID
    if user_type == 'patient':
        new_user.service_id = generate_service_id()
        new_user.contact_info = data.get('contact_info', '')
        new_user.current_cycle_stage = data.get('cycle_stage', 'Onboarding')
    
    # Doctor-specific: Add specialization
    if user_type == 'doctor':
        new_user.specialization = data.get('specialization', 'General')
        new_user.license_number = data.get('license_number')
    
    # Hash password
    new_user.set_password(password)
    
    # Assign default role based on type
    default_role = Role.query.filter_by(name=user_type).first()
    if default_role:
        new_user.roles.append(default_role)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "message": "User created successfully",
            "user": new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Registration failed: {str(e)}"}), 400


@app.route('/api/login', methods=['POST'])
def login():
    """Login with email + password."""
    data = request.json
    
    email = data.get('email')
    password = data.get('password')
    
    # Find user by EMAIL (not username)
    user = User.query.filter_by(email=email).first()
    
    # Check: exists + active + password matches
    if user and user.active and user.check_password(password):
        # Create JWT token with user ID
        token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "token": token,
            "user": user.to_dict()  # Safe response without password
        }), 200
    
    return jsonify({"message": "Invalid credentials"}), 401


@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Protected dashboard - shows different content by user type."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.active:
        return jsonify({"message": "User not found or inactive"}), 404
    
    # Build response based on user type
    response = {
        "message": f"Welcome, {user.name}!",
        "user": user.to_dict(),
        "user_type": user.type
    }
    
    # Type-specific data
    if user.type == 'doctor':
        response['dashboard_data'] = {
            'today_appointments': len(user.appointments),
            'specialization': user.specialization
        }
    elif user.type == 'patient':
        response['dashboard_data'] = {
            'service_id': user.service_id,
            'cycle_stage': user.current_cycle_stage,
            'upcoming_appointments': len([a for a in user.appointments if a.status == 'waiting'])
        }
    elif user.type == 'admin':
        response['dashboard_data'] = {
            'total_users': User.query.count(),
            'pending_registrations': User.query.filter_by(active=False).count()
        }
    
    return jsonify(response), 200


# ==================== ROLE-BASED ROUTES ====================

@app.route('/api/users', methods=['GET'])
@jwt_required()
def list_users():
    """Admin-only: List all users."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Role check
    if not current_user or not current_user.has_role('admin'):
        return jsonify({"message": "Admin access required"}), 403
    
    users = User.query.all()
    return jsonify({
        "users": [user.to_dict() for user in users]
    }), 200


@app.route('/api/doctors', methods=['GET'])
@jwt_required()
def list_doctors():
    """List all doctors (accessible by admin/receptionist)."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Allow admin or receptionist
    if not current_user or not (current_user.has_role('admin') or current_user.has_role('receptionist')):
        return jsonify({"message": "Access denied"}), 403
    
    doctors = Doctor.query.all()
    return jsonify({
        "doctors": [{
            'id': d.id,
            'name': d.name,
            'email': d.email,
            'specialization': d.specialization,
            'license_number': d.license_number
        } for d in doctors]
    }), 200


# ==================== APPOINTMENT ROUTES (Simplified) ====================

@app.route('/api/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    """Create a new appointment (Patient or Receptionist)."""
    from models import Appointment, Availability
    
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    data = request.json
    
    # Validate patient and doctor exist
    patient = Patient.query.get(data.get('patient_id'))
    doctor = Doctor.query.get(data.get('doctor_id'))
    
    if not patient or not doctor:
        return jsonify({"message": "Invalid patient or doctor"}), 400
    
    # Parse date/time
    try:
        appt_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start = datetime.strptime(data['start_time'], '%H:%M').time()
        end = datetime.strptime(data['end_time'], '%H:%M').time()
    except ValueError:
        return jsonify({"message": "Invalid date/time format"}), 400
    
    # Check for overlapping appointments (simplified)
    overlap = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date == appt_date,
        Appointment.start_time < end,
        Appointment.end_time > start,
        Appointment.status != 'cancelled'
    ).first()
    
    if overlap:
        return jsonify({"message": "Time slot already booked"}), 409
    
    # Create appointment
    new_appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        date=appt_date,
        start_time=start,
        end_time=end,
        status='waiting',
        is_walkin=data.get('is_walkin', False),
        stage_at_visit=patient.current_cycle_stage if patient else None
    )
    
    try:
        db.session.add(new_appt)
        db.session.commit()
        return jsonify({"message": "Appointment booked", "appointment_id": new_appt.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to book: {str(e)}"}), 400


# ==================== PHI ISOLATION EXAMPLE ====================

@app.route('/api/financials/invoices', methods=['GET'])
@jwt_required()
def list_invoices():
    """Accountant-only: List invoices WITHOUT clinical data."""
    from models import Invoice
    
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # STRICT ROLE CHECK: Only accountants
    if not current_user or not current_user.has_role('accountant'):
        return jsonify({"message": "Accountant access required"}), 403
    
    invoices = Invoice.query.all()
    
    # Return ONLY financial data (NO clinical notes, NO patient names)
    return jsonify({
        "invoices": [{
            'id': inv.id,
            'patient_service_id': inv.patient_service_id,  # Anonymous identifier
            'amount': inv.amount,
            'service_code': inv.service_code,  # e.g., "IVF-STAGE-03"
            'status': inv.status,
            'date_generated': inv.date_generated.isoformat()
            # ❌ NO clinical_notes, NO patient.name, NO doctor.name
        } for inv in invoices]
    }), 200


# ==================== AUDIT LOGGING (Optional Middleware) ====================

@app.after_request
def log_request(response):
    """Log every request to audit_log table."""
    try:
        # Skip logging for static files or health checks
        if request.path.startswith('/static') or request.path == '/health':
            return response
        
        # Get current user if authenticated
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass  # Not authenticated
        
        # Create audit entry
        log_entry = AuditLog(
            user_id=user_id,
            ip_address=request.remote_addr,
            endpoint=request.path,
            action=f"{request.method} {request.path}"
        )
        db.session.add(log_entry)
        db.session.commit()
    except:
        pass  # Don't crash the request if logging fails
    
    return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)