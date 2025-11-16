"""
Data Models for Green SME Compliance Co-Pilot
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    """Supported intent types"""
    ENERGY_AUDIT_FOR_CSRD = "energyAuditForCSRD"
    GDPR_ART30_EXPORT = "gdprArt30Export"
    EU_AI_ACT_RISK = "euAiActRisk"
    GENERAL_COMPLIANCE = "generalCompliance"
    ENERGY_OPTIMIZATION = "energyOptimization"


class SubmissionStatus(str, Enum):
    """Submission workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class DetectIntentRequest(BaseModel):
    text: str = Field(..., description="User input text for intent detection")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class DetectIntentResponse(BaseModel):
    intentType: IntentType
    slots: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: Optional[List[Dict[str, Any]]] = None


class SelectWorkflowRequest(BaseModel):
    intentType: IntentType
    slots: Dict[str, Any]
    userId: Optional[int] = None


class SelectWorkflowResponse(BaseModel):
    recipeId: str
    neededForms: List[str]
    questions: List[str] = Field(default_factory=list)
    estimatedTime: Optional[str] = None


class ParseFormRequest(BaseModel):
    pdfPath: str
    formId: Optional[str] = None


class ParseFormResponse(BaseModel):
    formId: str
    labels: List[str]
    structure: Dict[str, Any]
    confidence: float


class MapFieldsRequest(BaseModel):
    labels: List[str]
    userProfile: Dict[str, Any]
    slots: Dict[str, Any]


class MapFieldsResponse(BaseModel):
    fieldValues: Dict[str, Any]
    lowConfidence: List[str] = Field(default_factory=list)
    suggestions: Optional[Dict[str, Any]] = None


class CollectAnswersRequest(BaseModel):
    submissionId: int
    questions: List[str]
    method: str = Field(default="chat", description="chat or email")


class CollectAnswersResponse(BaseModel):
    answers: Dict[str, Any]
    status: str


class EstimateEmissionsRequest(BaseModel):
    kWh: float = Field(..., gt=0, description="Total energy consumption in kWh")
    city: Optional[str] = None
    gridFactor: Optional[float] = Field(default=0.42, description="Grid emission factor")
    includeScope3: bool = Field(default=False)


class EstimateEmissionsResponse(BaseModel):
    tCO2e: float
    scope2: float
    scope3: Optional[float] = None
    note: str
    breakdown: Optional[Dict[str, float]] = None


class FillPdfRequest(BaseModel):
    formId: str
    fieldValues: Dict[str, Any]
    templatePath: Optional[str] = None


class FillPdfResponse(BaseModel):
    docId: str
    filePath: str
    generatedAt: datetime = Field(default_factory=datetime.now)


class ExportFileRequest(BaseModel):
    docId: str
    format: str = Field(default="pdf", description="pdf or zip")
    includeEvidence: bool = Field(default=False)


class ExportFileResponse(BaseModel):
    downloadUrl: str
    expiresAt: Optional[datetime] = None
    fileSize: Optional[int] = None


class EmailFileRequest(BaseModel):
    docId: str
    recipient: EmailStr
    subject: str
    body: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class EmailFileResponse(BaseModel):
    status: str
    messageId: Optional[str] = None
    sentAt: datetime = Field(default_factory=datetime.now)


class GenerateCompliancePackRequest(BaseModel):
    submissionId: int
    regulations: List[str]


class GenerateCompliancePackResponse(BaseModel):
    packId: str
    filePath: str
    regulations: List[Dict[str, Any]]
    systemCard: Optional[str] = None


class WeatherInsightRequest(BaseModel):
    city: str
    country: str = Field(default="DE")


class WeatherInsightResponse(BaseModel):
    sunHours: float
    temperature: Optional[float] = None
    recommendation: Optional[str] = None


class LoadShiftRecommendationRequest(BaseModel):
    kWhProfile: Dict[str, float]
    weatherHint: Optional[Dict[str, Any]] = None


class LoadShiftRecommendationResponse(BaseModel):
    recommendations: List[str]
    potentialSavings: Optional[float] = None
    bestTimeSlots: Optional[List[str]] = None


# Database Models
class UserProfile(BaseModel):
    id: Optional[int] = None
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "DE"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    IBAN: Optional[str] = None
    business_type: Optional[str] = None
    business_facts: Optional[Dict[str, Any]] = None
    employee_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Submission(BaseModel):
    id: Optional[int] = None
    userId: int
    intent: str
    selected_forms: Optional[List[str]] = None
    answers: Optional[Dict[str, Any]] = None
    files: Optional[List[str]] = None
    status: SubmissionStatus = SubmissionStatus.PENDING
    audit_trail: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
