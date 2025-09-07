import os
import google.generativeai as genai
import re
from typing import Dict, Any
from core.models import SymptomPayload, PatientContext
from datetime import datetime

class PatientSymptomAgent:
    def __init__(self):
        self.gemini_available = False
        try:
            if os.getenv("GEMINI_API_KEY"):
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
        except:
            self.gemini_available = False
    
    def extract_symptoms(self, user_input: str, context: Dict[str, Any] = None) -> SymptomPayload:
        """Extract structured symptom information from patient input"""
        if self.gemini_available:
            try:
                prompt = f"""
                You are a medical symptom extraction agent. Extract detailed information from this patient message:
                
                Patient message: "{user_input}"
                
                Context: {context if context else 'No additional context provided'}
                
                Extract comprehensive information including:
                - chief_complaint: Primary complaint in 2-5 words
                - symptoms: List of all symptoms mentioned with details
                - onset: Duration or time since onset with specific timeframe
                - severity: Mild, moderate, severe, or critical
                - red_flags: List any potential red flag symptoms
                - duration_hours: Estimated duration in hours
                - triggers: Any identified triggers or aggravating factors
                
                Return ONLY valid JSON with these fields. Do not include any other text.
                """
                
                response = self.model.generate_content(prompt)
                json_str = self._extract_json(response.text)
                symptom_data = eval(json_str)
                
                patient_context = PatientContext(**context) if context else PatientContext()
                
                return SymptomPayload(
                    chief_complaint=symptom_data.get("chief_complaint", ""),
                    symptoms=symptom_data.get("symptoms", []),
                    onset=symptom_data.get("onset"),
                    severity=symptom_data.get("severity"),
                    red_flags=symptom_data.get("red_flags", []),
                    context=patient_context,
                    duration_hours=symptom_data.get("duration_hours"),
                    triggers=symptom_data.get("triggers", [])
                )
            except Exception as e:
                print(f"Gemini API error: {e}")
                return self._fallback_extraction(user_input, context)
        else:
            return self._fallback_extraction(user_input, context)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON string from response"""
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return text
    
    def _fallback_extraction(self, user_input: str, context: Dict[str, Any] = None) -> SymptomPayload:
        """Fallback method for symptom extraction"""
        symptoms = []
        red_flags = []
        
        # Enhanced symptom detection
        symptom_patterns = {
            "fever": [r"fever", r"temperature", r"hot", r"chills", r"°F", r"°C"],
            "sore throat": [r"sore throat", r"throat pain", r"difficulty swallowing"],
            "cough": [r"cough", r"coughing", r"hacking"],
            "headache": [r"headache", r"head pain", r"migraine"],
            "fatigue": [r"fatigue", r"tired", r"exhausted", r"weakness"],
            "nausea": [r"nausea", r"sick to stomach", r"queasy"],
            "vomiting": [r"vomiting", r"throwing up", r"puking"],
            "chest pain": [r"chest pain", r"chest discomfort"],
            "breathing issues": [r"shortness of breath", r"difficulty breathing", r"wheezing"],
            "abdominal pain": [r"stomach pain", r"abdominal pain", r"belly ache"]
        }
        
        # Red flag detection
        red_flag_patterns = [
            r"severe pain", r"worst pain", r"excruciating",
            r"can't breathe", r"difficulty breathing",
            r"chest pain", r"chest pressure",
            r"confusion", r"disoriented",
            r"fainting", r"passed out",
            r"blood", r"bleeding",
            r"high fever", r"fever over 103"
        ]
        
        user_input_lower = user_input.lower()
        
        # Extract symptoms
        for symptom, patterns in symptom_patterns.items():
            if any(re.search(pattern, user_input_lower) for pattern in patterns):
                symptoms.append(symptom)
        
        # Extract red flags
        for pattern in red_flag_patterns:
            if re.search(pattern, user_input_lower):
                red_flags.append(pattern)
        
        # Extract duration
        duration_match = re.search(r'for (\d+)\s*(hour|day|week|month)', user_input_lower)
        duration_hours = None
        if duration_match:
            value, unit = duration_match.groups()
            value = int(value)
            if unit == 'hour':
                duration_hours = value
            elif unit == 'day':
                duration_hours = value * 24
            elif unit == 'week':
                duration_hours = value * 168
            elif unit == 'month':
                duration_hours = value * 720
        
        # Determine chief complaint
        chief_complaint = symptoms[0] if symptoms else "General symptoms"
        
        # Determine severity based on keywords
        severity = "mild"
        if any(word in user_input_lower for word in ["severe", "worst", "excruciating", "unbearable"]):
            severity = "severe"
        elif any(word in user_input_lower for word in ["moderate", "moderately", "significant"]):
            severity = "moderate"
        
        # Create patient context
        patient_context = PatientContext(**context) if context else PatientContext()
        
        return SymptomPayload(
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            onset=None,
            severity=severity,
            red_flags=red_flags,
            context=patient_context,
            duration_hours=duration_hours
        )