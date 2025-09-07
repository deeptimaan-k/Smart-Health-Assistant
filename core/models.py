from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SeverityLevel(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

class PatientContext:
    def __init__(self, age=None, sex=None, pregnant=None, allergies=None, 
                 meds=None, vitals=None, medical_history=None, location=None):
        self.age = age
        self.sex = sex
        self.pregnant = pregnant
        self.allergies = allergies or []
        self.meds = meds or []
        self.vitals = vitals or {}
        self.medical_history = medical_history or []
        self.location = location
        
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

class SymptomPayload:
    def __init__(self, chief_complaint, symptoms, onset=None, severity=None, 
                 red_flags=None, context=None, duration_hours=None, triggers=None):
        self.chief_complaint = chief_complaint
        self.symptoms = symptoms or []
        self.onset = onset
        self.severity = severity
        self.red_flags = red_flags or []
        self.context = context or PatientContext()
        self.duration_hours = duration_hours
        self.triggers = triggers or []
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self):
        result = {k: v for k, v in self.__dict__.items() if v is not None}
        result['context'] = self.context.to_dict()
        return result

class Medication:
    def __init__(self, name, dose, route, frequency, max_daily=None, 
                 duration=None, precautions=None, interactions=None):
        self.name = name
        self.dose = dose
        self.route = route
        self.frequency = frequency
        self.max_daily = max_daily
        self.duration = duration
        self.precautions = precautions or []
        self.interactions = interactions or []
        
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

class DoctorPlan:
    def __init__(self, differential, tests_suggested=None, self_care=None, 
                 medications=None, escalation=None, disclaimer="", 
                 follow_up_advice=None, warning_signs=None):
        self.differential = differential or []
        self.tests_suggested = tests_suggested or []
        self.self_care = self_care or []
        self.medications = medications or []
        self.escalation = escalation or {"needed": False, "reason": None}
        self.disclaimer = disclaimer
        self.follow_up_advice = follow_up_advice or []
        self.warning_signs = warning_signs or []
        
    def to_dict(self):
        result = {k: v for k, v in self.__dict__.items() if v is not None}
        result['medications'] = [med.to_dict() for med in self.medications]
        return result

class PharmacyAvailability:
    def __init__(self, availability=None, alternatives=None, 
                 nearby_pharmacies=None, delivery_options=None):
        self.availability = availability or []
        self.alternatives = alternatives or []
        self.nearby_pharmacies = nearby_pharmacies or []
        self.delivery_options = delivery_options or []
        
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

class SafetyReview:
    def __init__(self, approved, issues=None, notes=None, 
                 risk_level=None, recommendations=None):
        self.approved = approved
        self.issues = issues or []
        self.notes = notes or []
        self.risk_level = risk_level
        self.recommendations = recommendations or []
        
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}