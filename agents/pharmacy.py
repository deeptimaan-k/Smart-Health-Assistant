import pandas as pd
from typing import List, Dict, Any
from core.models import PharmacyAvailability, Medication
import os
import random
from geopy.distance import geodesic

class PharmacyAgent:
    def __init__(self):
        # Load inventory data
        self.inventory_df = self._load_inventory()
        self.pharmacy_locations = self._generate_pharmacy_locations()
    
    def _load_inventory(self):
        """Load pharmacy inventory from CSV"""
        try:
            inventory_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.csv')
            df = pd.read_csv(inventory_path)
            
            # Add additional information if not present
            if 'generic_name' not in df.columns:
                df['generic_name'] = df['name']
            if 'form' not in df.columns:
                df['form'] = 'tablet'
            if 'manufacturer' not in df.columns:
                df['manufacturer'] = 'Generic'
            if 'stock_level' not in df.columns:
                df['stock_level'] = df['in_stock'].apply(lambda x: 'High' if x else 'Out of Stock')
            
            return df
        except:
            # Return default inventory if file not found
            return pd.DataFrame({
                'name': ['paracetamol', 'ibuprofen', 'amoxicillin', 'aspirin', 
                        'cetirizine', 'loratadine', 'omeprazole', 'dextromethorphan'],
                'generic_name': ['paracetamol', 'ibuprofen', 'amoxicillin', 'aspirin',
                                'cetirizine', 'loratadine', 'omeprazole', 'dextromethorphan'],
                'strength': ['500mg', '400mg', '500mg', '300mg', '10mg', '10mg', '20mg', '15mg'],
                'brand': ['Crocin', 'Brufen', 'Amoxil', 'Aspirin', 'Zyrtec', 'Claritin', 'Prilosec', 'Delsym'],
                'form': ['tablet', 'tablet', 'capsule', 'tablet', 'tablet', 'tablet', 'capsule', 'syrup'],
                'manufacturer': ['GSK', 'Abbott', 'GSK', 'Bayer', 'Johnson & Johnson', 'Bayer', 'AstraZeneca', 'Reckitt'],
                'in_stock': [1, 0, 1, 1, 1, 1, 1, 1],
                'stock_level': ['High', 'Out of Stock', 'Medium', 'High', 'High', 'High', 'High', 'Low'],
                'price': [15, 18, 45, 10, 12, 15, 28, 85]
            })
    
    def _generate_pharmacy_locations(self):
        """Generate simulated pharmacy locations"""
        return [
            {"name": "Apollo Pharmacy", "distance_km": 0.8, "rating": 4.5, "delivery": True},
            {"name": "MedPlus", "distance_km": 1.2, "rating": 4.2, "delivery": True},
            {"name": "Netmeds", "distance_km": 2.5, "rating": 4.3, "delivery": True},
            {"name": "Local Medical Store", "distance_km": 0.3, "rating": 4.0, "delivery": False},
            {"name": "Wellness Pharmacy", "distance_km": 1.8, "rating": 4.7, "delivery": True}
        ]
    
    def check_availability(self, medications: List[Medication], 
                          allergies: List[str] = None, 
                          location: Dict[str, float] = None) -> PharmacyAvailability:
        """Check availability of medications and suggest alternatives considering allergies"""
        availability = []
        alternatives = []
        
        for med in medications:
            med_name = med.name.lower()
            
            # Check if medication is in inventory
            matches = self.inventory_df[self.inventory_df['name'].str.lower() == med_name]
            
            if not matches.empty:
                # Medication is available
                for _, row in matches.iterrows():
                    if allergies and self._check_allergy_contraindication(med_name, allergies):
                        # Medication contraindicated due to allergy
                        alternatives.append({
                            "name": f"{row['name']} {row['strength']}",
                            "reason": "Contraindicated due to allergy",
                            "suggestion": "Consult doctor for alternative",
                            "type": "contraindicated"
                        })
                    else:
                        availability.append({
                            "name": f"{row['name']} {row['strength']}",
                            "generic_name": row['generic_name'],
                            "strength": row['strength'],
                            "form": row['form'],
                            "in_stock": bool(row['in_stock']),
                            "stock_level": row['stock_level'],
                            "price": f"₹{row['price']}",
                            "brand": row['brand'],
                            "manufacturer": row['manufacturer']
                        })
            else:
                # Medication not found, suggest alternatives
                alt_suggestions = self._suggest_alternatives(med_name, allergies)
                alternatives.append({
                    "name": med.name,
                    "reason": "Not available in inventory",
                    "suggestions": alt_suggestions,
                    "type": "unavailable"
                })
        
        # Get nearby pharmacies
        nearby_pharmacies = self._get_nearby_pharmacies(location)
        
        # Get delivery options
        delivery_options = self._get_delivery_options()
        
        return PharmacyAvailability(
            availability=availability,
            alternatives=alternatives,
            nearby_pharmacies=nearby_pharmacies,
            delivery_options=delivery_options
        )
    
    def _check_allergy_contraindication(self, medication: str, allergies: List[str]) -> bool:
        """Check if medication is contraindicated due to allergies"""
        allergy_contraindications = {
            "penicillin": ["amoxicillin", "augmentin", "ampicillin", "penicillin"],
            "sulfa": ["sulfamethoxazole", "sulfasalazine", "sulfadiazine"],
            "aspirin": ["aspirin", "ibuprofen", "naproxen", "diclofenac"]
        }
        
        medication_lower = medication.lower()
        allergies_lower = [a.lower() for a in allergies]
        
        for allergy in allergies_lower:
            if allergy in allergy_contraindications:
                if any(med in medication_lower for med in allergy_contraindications[allergy]):
                    return True
        
        return False
    
    def _suggest_alternatives(self, medication: str, allergies: List[str] = None) -> List[Dict]:
        """Suggest alternative medications"""
        alternatives = []
        
        # Simple alternative suggestions based on medication type
        alternative_map = {
            "paracetamol": ["acetaminophen"],
            "ibuprofen": ["naproxen", "diclofenac"],
            "amoxicillin": ["azithromycin", "cephalexin"],
            "cetirizine": ["loratadine", "fexofenadine"],
            "omeprazole": ["pantoprazole", "lansoprazole"]
        }
        
        for med_name, alt_list in alternative_map.items():
            if med_name in medication.lower():
                for alt in alt_list:
                    # Check if alternative is in inventory and not contraindicated
                    alt_matches = self.inventory_df[self.inventory_df['name'].str.lower() == alt]
                    if not alt_matches.empty and not (allergies and self._check_allergy_contraindication(alt, allergies)):
                        row = alt_matches.iloc[0]
                        alternatives.append({
                            "name": f"{row['name']} {row['strength']}",
                            "brand": row['brand'],
                            "price": f"₹{row['price']}",
                            "in_stock": bool(row['in_stock']),
                            "reason": f"Alternative to {medication}"
                        })
        
        return alternatives
    
    def _get_nearby_pharmacies(self, location: Dict[str, float] = None) -> List[Dict]:
        """Get nearby pharmacies based on location"""
        if not location:
            return self.pharmacy_locations[:3]  # Return first 3 if no location
        
        # Simulate distance calculation based on location
        # In a real implementation, you would use actual distance calculation
        nearby_pharmacies = sorted(
            self.pharmacy_locations,
            key=lambda x: x['distance_km']
        )[:3]
        
        return nearby_pharmacies
    
    def _get_delivery_options(self) -> List[Dict]:
        """Get delivery options"""
        return [
            {
                "service": "Apollo Delivery",
                "time": "2-4 hours",
                "charge": "₹50",
                "min_order": "₹200"
            },
            {
                "service": "MedPlus Express",
                "time": "1-3 hours",
                "charge": "₹40",
                "min_order": "₹150"
            },
            {
                "service": "Netmeds Fast",
                "time": "3-5 hours",
                "charge": "₹35",
                "min_order": "₹100"
            }
        ]