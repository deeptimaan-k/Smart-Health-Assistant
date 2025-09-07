from typing import Dict, Any
from agents.patient_symptom import PatientSymptomAgent
from agents.doctor import DoctorAgent
from agents.pharmacy import PharmacyAgent
from agents.guardian import SafetyGuardian
from core.models import SymptomPayload, DoctorPlan, PharmacyAvailability, SafetyReview
import asyncio

class Orchestrator:
    def __init__(self):
        self.psa = PatientSymptomAgent()
        self.da = DoctorAgent()
        self.pa = PharmacyAgent()
        self.sg = SafetyGuardian()
    
    def process_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a patient request through the multi-agent system"""
        # Step 1: Extract symptoms with Patient Symptom Agent
        symptom_data = self.psa.extract_symptoms(user_input, context)
        
        # Step 2: Generate plan with Doctor Agent
        doctor_plan = self.da.generate_plan(symptom_data)
        
        # Step 3: Check pharmacy availability
        pharmacy_data = self.pa.check_availability(
            doctor_plan.medications, 
            context.get("allergies") if context else None,
            context.get("location") if context else None
        )
        
        # Step 4: Safety review
        safety_review = self.sg.review_plan(symptom_data, doctor_plan, pharmacy_data)
        
        # Prepare comprehensive final response
        return {
            "symptom_analysis": symptom_data.to_dict(),
            "preliminary_assessment": doctor_plan.to_dict(),
            "pharmacy_availability": pharmacy_data.to_dict(),
            "safety_review": safety_review.to_dict(),
            "recommendation": self._generate_recommendation(doctor_plan, safety_review),
            "timestamp": self._get_timestamp(),
            "session_id": self._generate_session_id(),
            "risk_level": safety_review.risk_level
        }
    
    def _generate_recommendation(self, doctor_plan: DoctorPlan, safety_review: SafetyReview) -> str:
        """Generate a final recommendation based on the assessment"""
        if doctor_plan.escalation.get("needed", False):
            urgency = doctor_plan.escalation.get("urgency", "immediate")
            if urgency == "immediate":
                return "🚨 IMMEDIATE MEDICAL ATTENTION REQUIRED. Please seek emergency care or call your local emergency services immediately."
            else:
                return "Urgent medical evaluation recommended. Please contact a healthcare provider as soon as possible."
        
        if not safety_review.approved:
            return "Caution advised. Several safety concerns were identified. Please consult with a healthcare provider before following any recommendations."
        
        return "Based on your symptoms, the following self-care and medication options may be appropriate. Remember to consult a healthcare provider for proper diagnosis and monitor your symptoms closely."
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _generate_session_id(self):
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())[:8]