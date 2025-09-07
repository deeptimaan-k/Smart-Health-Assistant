# Safety rules and validation logic
from typing import List, Dict, Any
from core.models import SymptomPayload, DoctorPlan, Medication

class SafetyRules:
    @staticmethod
    def check_red_flags(symptoms: List[str], red_flags: List[str]) -> bool:
        """Check if any red flag symptoms are present"""
        critical_red_flags = [
            "chest pain", "severe shortness of breath", "unilateral weakness",
            "confusion", "blood in vomit", "blood in stool", "difficulty breathing",
            "neck stiffness", "severe headache", "fainting", "loss of consciousness",
            "severe abdominal pain", "high fever", "rapid heart rate",
            "sudden vision changes", "difficulty speaking"
        ]
        
        # Check if any critical red flags are mentioned in symptoms or red_flags
        all_symptoms = symptoms + red_flags
        for flag in critical_red_flags:
            if any(flag in symptom.lower() for symptom in all_symptoms):
                return True
        return False

    @staticmethod
    def check_medication_safety(medication: Medication, context: Dict[str, Any]) -> List[str]:
        """Check medication safety based on patient context"""
        issues = []
        
        # Check paracetamol/acetaminophen dosage
        if medication.name.lower() in ["paracetamol", "acetaminophen"]:
            if context.get("age") and context["age"] < 18:
                # Pediatric dosing
                if "max_daily" not in medication.__dict__ or not medication.max_daily:
                    issues.append("Pediatric paracetamol dosing requires careful weight-based calculation")
            else:
                # Adult dosing - check if exceeds 3000-4000 mg daily
                if hasattr(medication, 'max_daily') and medication.max_daily:
                    try:
                        daily_max = int(''.join(filter(str.isdigit, medication.max_daily)))
                        if daily_max > 4000:
                            issues.append(f"Paracetamol daily maximum {daily_max}mg exceeds safe limits")
                        elif daily_max > 3000:
                            issues.append(f"Paracetamol daily maximum {daily_max}mg should be used with caution")
                    except:
                        issues.append("Could not parse paracetamol dosage information")
        
        # Check for allergies
        if context.get("allergies"):
            allergies = [allergy.lower() for allergy in context["allergies"]]
            med_name = medication.name.lower()
            
            # Penicillin allergy cross-reactivity
            if "penicillin" in allergies and med_name in ["amoxicillin", "augmentin", "ampicillin"]:
                issues.append(f"Medication {medication.name} contraindicated due to penicillin allergy")
            
            # Sulfa allergy
            if "sulfa" in allergies and any(sulfa in med_name for sulfa in ["sulfa", "sulfamethoxazole", "sulfasalazine"]):
                issues.append(f"Medication {medication.name} contraindicated due to sulfa allergy")
        
        # Pregnancy precautions
        if context.get("pregnant") and medication.name.lower() in ["ibuprofen", "naproxen", "diclofenac", "warfarin", "statins"]:
            issues.append(f"Medication {medication.name} should be avoided in pregnancy")
            
        # Renal precautions
        if context.get("renal_issues") and medication.name.lower() in ["ibuprofen", "naproxen", "diclofenac"]:
            issues.append(f"Medication {medication.name} should be used with caution in renal impairment")
        
        return issues

    @staticmethod
    def check_pregnancy_contraindications(plan: DoctorPlan, context: Dict[str, Any]) -> List[str]:
        """Check for pregnancy-related contraindications"""
        issues = []
        if context.get("pregnant"):
            # Check medications that should be avoided in pregnancy
            contraindicated_meds = ["ibuprofen", "naproxen", "diclofenac", "warfarin", "statins", 
                                   "ace inhibitors", "arb", "retinoids", "methotrexate"]
            for med in plan.medications:
                if any(contraindicated in med.name.lower() for contraindicated in contraindicated_meds):
                    issues.append(f"Medication {med.name} may not be safe during pregnancy")
        
        return issues

    @staticmethod
    def check_allergy_contraindication(medication: str, allergies: List[str]) -> bool:
        """Check if medication is contraindicated due to allergies"""
        allergy_contraindications = {
            "penicillin": ["amoxicillin", "augmentin", "ampicillin", "penicillin"],
            "sulfa": ["sulfamethoxazole", "sulfasalazine", "sulfadiazine", "sulfa"],
            "aspirin": ["aspirin", "ibuprofen", "naproxen", "diclofenac", "nsaid"],
            "nsaid": ["ibuprofen", "naproxen", "diclofenac", "aspirin", "nsaid"]
        }
        
        medication_lower = medication.lower()
        allergies_lower = [a.lower() for a in allergies]
        
        for allergy in allergies_lower:
            if allergy in allergy_contraindications:
                if any(med in medication_lower for med in allergy_contraindications[allergy]):
                    return True
        
        return False