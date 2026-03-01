from flask_security.utils import hash_password
from applications.models import *
import uuid


def create_initial_data(app, db):

    # ------------------------------------------------------------------
    # 1. ROLES
    # ------------------------------------------------------------------
    admin_role        = app.security.datastore.find_or_create_role(name='admin',        description='Administrator')
    doctor_role       = app.security.datastore.find_or_create_role(name='doctor',       description='Service Provider')
    patient_role      = app.security.datastore.find_or_create_role(name='patient',      description='Client')
    receptionist_role = app.security.datastore.find_or_create_role(name='receptionist', description='Front Desk')
    accountant_role   = app.security.datastore.find_or_create_role(name='accountant',   description='Financial Staff')

    db.session.commit()

    # ------------------------------------------------------------------
    # 2. ADMINISTRATOR
    # ------------------------------------------------------------------
    if not app.security.datastore.find_user(email='admin@ivfclinic.com'):
        admin = Administrator(
            email='admin@ivfclinic.com',
            name='Clinic Admin',
            password=hash_password('admin123'),
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
            roles=[admin_role]
        )
        db.session.add(admin)

    # ------------------------------------------------------------------
    # 3. RECEPTIONIST
    # ------------------------------------------------------------------
    if not Receptionist.query.filter_by(email='reception@ivfclinic.com').first():
        receptionist = Receptionist(
            email='reception@ivfclinic.com',
            name='Front Desk',
            password=hash_password('reception123'),
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
            desk_id='DESK-01',
            roles=[receptionist_role]
        )
        db.session.add(receptionist)

    # ------------------------------------------------------------------
    # 4. ACCOUNTANT
    # ------------------------------------------------------------------
    if not Accountant.query.filter_by(email='accounts@ivfclinic.com').first():
        accountant = Accountant(
            email='accounts@ivfclinic.com',
            name='Finance Staff',
            password=hash_password('accounts123'),
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
            roles=[accountant_role]
        )
        db.session.add(accountant)

    # ------------------------------------------------------------------
    # 5. SEED DOCTORS (3 as per spec — Admin normally registers via dashboard,
    #    but seeded here so the app is functional from first run)
    # ------------------------------------------------------------------
    seed_doctors = [
        {
            'email': 'dr.sharma@ivfclinic.com',
            'name': 'Dr. Priya Sharma',
            'specialization': 'Reproductive Endocrinology',
            'license_number': 'MCI-2024-001'
        },
        {
            'email': 'dr.mehta@ivfclinic.com',
            'name': 'Dr. Arjun Mehta',
            'specialization': 'Embryology',
            'license_number': 'MCI-2024-002'
        },
        {
            'email': 'dr.kapoor@ivfclinic.com',
            'name': 'Dr. Sunita Kapoor',
            'specialization': 'Gynecology & IVF',
            'license_number': 'MCI-2024-003'
        },
    ]

    for doc_data in seed_doctors:
        if not Doctor.query.filter_by(email=doc_data['email']).first():
            doctor = Doctor(
                email=doc_data['email'],
                name=doc_data['name'],
                password=hash_password('doctor123'),  # In production, auto-generate & email
                active=True,
                fs_uniquifier=str(uuid.uuid4()),
                specialization=doc_data['specialization'],
                license_number=doc_data['license_number'],
                roles=[doctor_role]
            )
            db.session.add(doctor)

    # ------------------------------------------------------------------
    # 6. SEED PATIENT (for dev/testing only)
    # ------------------------------------------------------------------
    if not Patient.query.filter_by(email='patient@ivfclinic.com').first():
        patient = Patient(
            email='patient@ivfclinic.com',
            name='Test Patient',
            password=hash_password('patient123'),
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
            service_id='SVC-2026-0001',
            contact_info='9876543210',
            current_cycle_stage='Onboarding',
            roles=[patient_role]
        )
        db.session.add(patient)

    db.session.commit()