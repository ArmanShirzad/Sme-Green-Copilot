"""
LLM Service - Groq API integration with regulatory reasoning
Adapted from SmartPdfFiller, using Groq API

Default Model: llama-3.1-70b-versatile
- Best for complex regulatory reasoning (GDPR, CSRD, EU AI Act)
- Higher accuracy for compliance tasks
- Slower than 8B but significantly better reasoning quality
"""
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import requests

load_dotenv()

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: groq not available. Install with: pip install groq")


class LLMService:
    """LLM service for regulatory reasoning and field inference."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-70b-versatile"):
        """
        Initialize LLM service.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model to use (default: llama-3.1-70b-versatile)
                  - llama-3.1-70b-versatile: Best for complex reasoning (regulatory compliance)
                  - llama-3.1-8b-instant: Faster but less accurate for complex tasks
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.model = model
        self.client = None
        
        if GROQ_AVAILABLE and self.api_key and self.api_key != 'your_groq_api_key_here':
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing Groq client: {e}")
                self.client = None
    
    def infer_regulatory_data(self, description: str, regulation: str = "GDPR") -> Dict[str, Any]:
        """
        Infer regulatory data from description using LLM.
        
        Args:
            description: Description of processing activity or system
            regulation: Regulation type (GDPR, CSRD, EU_AI_ACT)
            
        Returns:
            Dictionary with inferred regulatory data
        """
        if not self.client:
            return self._fallback_inference(description, regulation)
        
        # Build regulatory reasoning prompt
        prompt = self._build_regulatory_prompt(description, regulation)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            if response and hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                return self._parse_regulatory_response(content, regulation)
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._fallback_inference(description, regulation)
    
    def _build_regulatory_prompt(self, description: str, regulation: str) -> str:
        """Build prompt for regulatory reasoning."""
        if regulation == "GDPR":
            return f"""Analyze the following data processing description and infer GDPR Article 30 record fields.

Description: {description}

Provide a JSON response with:
- processing_purposes: List of purposes
- data_categories: Categories of personal data
- legal_basis: Lawful basis per GDPR Art. 6 (e.g., "consent", "contract", "legal obligation")
- data_subjects: Categories of data subjects
- retention_period: Suggested retention period
- security_measures: Recommended security measures

Respond only with valid JSON."""
        
        elif regulation == "CSRD":
            return f"""Analyze the following business activity and infer CSRD ESRS E1 (Climate) fields.

Description: {description}

Provide a JSON response with:
- energy_sources: List of energy sources
- estimated_kwh: Estimated annual energy consumption in kWh
- scope2_emissions: Estimated Scope 2 emissions in tCO2e
- reduction_actions: Suggested reduction actions

Respond only with valid JSON."""
        
        elif regulation == "EU_AI_ACT":
            return f"""Analyze the following AI system description and classify risk per EU AI Act.

Description: {description}

Provide a JSON response with:
- risk_level: "minimal", "limited", or "high"
- annex_iii_category: If high-risk, which Annex III category
- compliance_requirements: List of required compliance steps
- system_card_required: Boolean

Respond only with valid JSON."""
        
        return f"Analyze: {description}"
    
    def _parse_regulatory_response(self, content: str, regulation: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        import json
        try:
            # Try to extract JSON from response
            json_match = None
            if '{' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                if end > start:
                    json_str = content[start:end]
                    json_match = json.loads(json_str)
            
            if json_match:
                return json_match
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
        
        # Fallback: return raw content
        return {"raw_response": content, "regulation": regulation}
    
    def infer_field_values(self, field_labels: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer field values from labels and context using LLM.
        
        Args:
            field_labels: List of extracted field labels
            context: Context data (user_data, slots, etc.)
            
        Returns:
            Dictionary mapping field labels to inferred values
        """
        if not self.client:
            return {}
        
        prompt = f"""Given these form field labels and context, infer appropriate values.

Field Labels:
{chr(10).join(f'- {label}' for label in field_labels)}

Context:
{chr(10).join(f'- {k}: {v}' for k, v in context.items())}

Provide a JSON object mapping field labels to inferred values.
Only include fields where you can reasonably infer a value.

Respond only with valid JSON: {{"field_label": "value", ...}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            if response and hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                import json
                try:
                    if '{' in content:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if end > start:
                            return json.loads(content[start:end])
                except:
                    pass
        except Exception as e:
            print(f"Groq API error in field inference: {e}")
        
        return {}
    
    def classify_intent_and_slots(self, user_text: str) -> Dict[str, Any]:
        """
        Classify user intent and extract slots using LLM.
        Enhanced version for regulatory compliance intents.
        
        Args:
            user_text: User input text
            
        Returns:
            Dictionary with intentType, slots, confidence
        """
        if not self.client:
            return self._fallback_intent_classification(user_text)
        
        prompt = f"""Extract intent and slots from this user request for a compliance agent.

User Request: {user_text}

Possible intents:
- energyAuditForCSRD: Energy audit for CSRD compliance
- gdprArt30: GDPR Article 30 record generation
- euAiActRisk: EU AI Act risk assessment

Respond with JSON:
{{
  "intentType": "intent_name",
  "slots": {{
    "kWh": number if mentioned,
    "city": string if mentioned,
    "company": string if mentioned
  }},
  "confidence": 0.0-1.0
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            if response and hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                import json
                try:
                    if '{' in content:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if end > start:
                            result = json.loads(content[start:end])
                            return result
                except:
                    pass
        except Exception as e:
            print(f"Groq API error in intent classification: {e}")
        
        return self._fallback_intent_classification(user_text)
    
    def _fallback_inference(self, description: str, regulation: str) -> Dict[str, Any]:
        """Fallback inference without LLM."""
        if regulation == "GDPR":
            return {
                "legal_basis": "contract",  # Default
                "processing_purposes": ["Business operations"],
                "data_categories": ["Personal data"],
                "retention_period": "As required by law"
            }
        elif regulation == "CSRD":
            return {
                "energy_sources": ["Electricity"],
                "estimated_kwh": 0,
                "scope2_emissions": 0
            }
        return {}
    
    def _fallback_intent_classification(self, user_text: str) -> Dict[str, Any]:
        """Fallback intent classification using pattern matching."""
        text_lower = user_text.lower()
        
        intent = "general"
        confidence = 0.5
        slots = {}
        
        # Pattern matching
        if any(kw in text_lower for kw in ["energy", "csrd", "emissions", "carbon"]):
            intent = "energyAuditForCSRD"
            confidence = 0.7
            
            import re
            kwh_match = re.search(r'(\d+)\s*(kwh|kilowatt)', text_lower)
            if kwh_match:
                slots['kWh'] = float(kwh_match.group(1))
        
        elif any(kw in text_lower for kw in ["gdpr", "article 30", "data processing", "privacy"]):
            intent = "gdprArt30"
            confidence = 0.7
        
        elif any(kw in text_lower for kw in ["ai act", "ai risk", "artificial intelligence"]):
            intent = "euAiActRisk"
            confidence = 0.7
        
        return {
            "intentType": intent,
            "slots": slots,
            "confidence": confidence
        }

