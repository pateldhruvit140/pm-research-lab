from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
import string
import random
from datetime import datetime, timezone, timedelta
from enum import Enum
import io
import csv
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="PM Research Lab API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

def generate_share_code(length=8):
    """Generate a unique alphanumeric share code for experiments"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

# ========================
# ENUMS
# ========================

class NotificationStrategy(str, Enum):
    JUST_IN_TIME = "just_in_time"
    SCAFFOLDED = "scaffolded"
    FADED = "faded"
    CONTROL = "control"

class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"

class TaskPriority(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"

class SessionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLACKOUT = "blackout"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class OffloadingChoice(str, Enum):
    REMEMBER = "remember"  # User chose to rely on internal memory
    SET_REMINDER = "set_reminder"  # User chose to offload to external system

class RecallProbeType(str, Enum):
    DOSE_NUMBER = "dose_number"  # "What was the dose number?"
    NEXT_DOSE_TIME = "next_dose_time"  # "When is the next dose?"
    DOSES_REMAINING = "doses_remaining"  # "How many doses remaining?"
    LAST_DOSE_TIME = "last_dose_time"  # "When was the last reminder?"

# ========================
# MODELS - Experiments
# ========================

class ExperimentConfig(BaseModel):
    notification_strategy: NotificationStrategy
    notification_frequency_minutes: int = Field(default=30, ge=0, le=1440)
    blackout_duration_minutes: int = Field(default=60, ge=5, le=480)
    total_duration_minutes: int = Field(default=180, ge=30, le=1440)
    time_compression_factor: float = Field(default=60.0, ge=1.0, le=1000.0)
    num_doses: int = Field(default=3, ge=1, le=10)
    visual_persistence_seconds: int = Field(default=10, ge=1, le=60)
    # Scaffolded strategy config
    scaffolded_increase_factor: float = Field(default=1.5, ge=1.0, le=3.0)  # How much to increase interval each time
    # Faded strategy config
    faded_opacity_decay: float = Field(default=0.15, ge=0.05, le=0.5)  # How much to reduce visibility each time

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: ExperimentConfig

class Experiment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    config: ExperimentConfig
    share_code: str = Field(default_factory=lambda: generate_share_code())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True
    total_sessions: int = 0
    completed_sessions: int = 0

# ========================
# MODELS - Demographics
# ========================

class Demographics(BaseModel):
    age_group: Optional[str] = None
    education: Optional[str] = None
    tech_familiarity: Optional[str] = None  # How often they use phone reminders
    gender: Optional[str] = None
    occupation: Optional[str] = None
    # Additional fields for research
    memory_self_rating: Optional[int] = None  # 1-5 scale
    reminder_app_usage: Optional[str] = None
    health_condition_management: Optional[bool] = None

# ========================
# MODELS - Participants & Sessions
# ========================

class ParticipantCreate(BaseModel):
    participant_code: str
    experiment_id: str
    demographics: Optional[Demographics] = None

class Participant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_code: str
    experiment_id: str
    demographics: Optional[Demographics] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    consent_given: bool = True
    consent_timestamp: Optional[str] = None

class SessionCreate(BaseModel):
    participant_id: str
    experiment_id: str

class OffloadingEvent(BaseModel):
    """Tracks when participant chooses to remember vs set reminder"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_id: str
    dose_number: int
    choice: OffloadingChoice
    decision_time_ms: int  # Time taken to make the choice
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # For scaffolded/faded strategies
    notification_prominence: float = Field(default=1.0)  # 1.0 = full, decreases for faded
    current_interval_minutes: Optional[float] = None  # For scaffolded tracking

class SimulatedNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    simulated_time: str
    real_time: str
    dose_number: int
    was_shown: bool = True
    dismissed_at: Optional[str] = None
    # Enhanced tracking
    user_response: Optional[OffloadingChoice] = None  # Did they choose to remember or set reminder?
    response_time_ms: Optional[int] = None  # Time to respond to notification
    notification_prominence: float = Field(default=1.0)  # For faded strategy (1.0 = full opacity)
    interval_from_last_minutes: Optional[float] = None  # For scaffolded strategy tracking

class RecallProbe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    probe_type: RecallProbeType = RecallProbeType.DOSE_NUMBER
    probe_time: str
    probe_shown_timestamp: str  # Exact timestamp when probe was displayed
    dose_asked: int
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    response_time_ms: Optional[int] = None  # Actual measured response time
    response_submitted_timestamp: Optional[str] = None  # When user submitted answer
    confidence_rating: Optional[int] = None  # 1-5 how confident they were

class Session(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_id: str
    experiment_id: str
    status: SessionStatus = SessionStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    simulated_start_time: Optional[str] = None
    simulated_current_time: Optional[str] = None
    # Notification tracking
    notifications: List[SimulatedNotification] = []
    # Offloading events - key for thesis
    offloading_events: List[OffloadingEvent] = []
    # Recall probes
    recall_probes: List[RecallProbe] = []
    # Blackout tracking
    blackout_started_at: Optional[str] = None
    # Aggregated metrics
    total_notifications_shown: int = 0
    total_remember_choices: int = 0  # Times user chose "I'll remember"
    total_offload_choices: int = 0  # Times user chose "Set reminder"
    avg_decision_time_ms: Optional[float] = None
    avg_recall_response_time_ms: Optional[float] = None
    recall_accuracy_percent: Optional[float] = None
    # Strategy-specific tracking
    scaffolded_final_interval: Optional[float] = None
    faded_final_prominence: Optional[float] = None

# ========================
# MODELS - Progress Tracker
# ========================

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    week_number: int = Field(ge=1, le=52)
    priority: TaskPriority = TaskPriority.P1
    target_date: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    target_date: Optional[str] = None
    notes: Optional[str] = None
    actual_hours: Optional[float] = None
    category: Optional[str] = None

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    week_number: int
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.P1
    target_date: Optional[str] = None
    actual_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    notes: Optional[str] = None
    category: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WeeklyReportCreate(BaseModel):
    week_number: int = Field(ge=1, le=52)
    start_date: str
    end_date: str
    summary: Optional[str] = None
    accomplishments: List[str] = []
    challenges: List[str] = []
    next_week_goals: List[str] = []
    notes: Optional[str] = None

class WeeklyReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    week_number: int
    start_date: str
    end_date: str
    summary: Optional[str] = None
    accomplishments: List[str] = []
    challenges: List[str] = []
    next_week_goals: List[str] = []
    notes: Optional[str] = None
    tasks_completed: int = 0
    tasks_total: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ========================
# ROUTES - Health
# ========================

@api_router.get("/")
async def root():
    return {"message": "PM Research Lab API", "version": "2.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ========================
# ROUTES - Experiments
# ========================

@api_router.post("/experiments", response_model=Experiment)
async def create_experiment(data: ExperimentCreate):
    experiment = Experiment(
        name=data.name,
        description=data.description,
        config=data.config
    )
    doc = experiment.model_dump()
    await db.experiments.insert_one(doc)
    return experiment

@api_router.get("/experiments", response_model=List[Experiment])
async def get_experiments(is_active: Optional[bool] = None):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    experiments = await db.experiments.find(query, {"_id": 0}).to_list(100)
    return experiments

@api_router.get("/experiments/{experiment_id}", response_model=Experiment)
async def get_experiment(experiment_id: str):
    experiment = await db.experiments.find_one({"id": experiment_id}, {"_id": 0})
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment

@api_router.put("/experiments/{experiment_id}", response_model=Experiment)
async def update_experiment(experiment_id: str, data: ExperimentCreate):
    experiment = await db.experiments.find_one({"id": experiment_id}, {"_id": 0})
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    update_data = {
        "name": data.name,
        "description": data.description,
        "config": data.config.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.experiments.update_one({"id": experiment_id}, {"$set": update_data})
    updated = await db.experiments.find_one({"id": experiment_id}, {"_id": 0})
    return updated

@api_router.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str):
    result = await db.experiments.delete_one({"id": experiment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"message": "Experiment deleted"}

@api_router.get("/experiments/join/{share_code}")
async def join_experiment_by_code(share_code: str):
    """Allow participants to join a specific experiment via share code"""
    experiment = await db.experiments.find_one({"share_code": share_code.upper()}, {"_id": 0})
    if not experiment:
        raise HTTPException(status_code=404, detail="Invalid study code. Please check and try again.")
    if not experiment.get("is_active", True):
        raise HTTPException(status_code=400, detail="This study is no longer accepting participants.")
    return experiment

# ========================
# ROUTES - Participants
# ========================

@api_router.post("/participants", response_model=Participant)
async def create_participant(data: ParticipantCreate):
    # Convert demographics dict to Demographics model if provided
    demographics_data = None
    if data.demographics:
        if isinstance(data.demographics, dict):
            demographics_data = Demographics(**data.demographics)
        else:
            demographics_data = data.demographics
    
    participant = Participant(
        participant_code=data.participant_code,
        experiment_id=data.experiment_id,
        demographics=demographics_data,
        consent_timestamp=datetime.now(timezone.utc).isoformat()
    )
    doc = participant.model_dump()
    await db.participants.insert_one(doc)
    
    # Log for data integrity verification
    logging.info(f"Participant created: {participant.id} with demographics: {demographics_data}")
    
    return participant

@api_router.get("/participants", response_model=List[Participant])
async def get_participants(experiment_id: Optional[str] = None):
    query = {}
    if experiment_id:
        query["experiment_id"] = experiment_id
    participants = await db.participants.find(query, {"_id": 0}).to_list(500)
    return participants

@api_router.get("/participants/{participant_id}", response_model=Participant)
async def get_participant(participant_id: str):
    participant = await db.participants.find_one({"id": participant_id}, {"_id": 0})
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant

@api_router.put("/participants/{participant_id}/demographics")
async def update_participant_demographics(participant_id: str, demographics: Demographics):
    """Update participant demographics - ensures data integrity"""
    participant = await db.participants.find_one({"id": participant_id}, {"_id": 0})
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    await db.participants.update_one(
        {"id": participant_id},
        {"$set": {"demographics": demographics.model_dump()}}
    )
    
    logging.info(f"Demographics updated for participant {participant_id}: {demographics}")
    
    updated = await db.participants.find_one({"id": participant_id}, {"_id": 0})
    return updated

# ========================
# ROUTES - Sessions
# ========================

@api_router.post("/sessions", response_model=Session)
async def create_session(data: SessionCreate):
    experiment = await db.experiments.find_one({"id": data.experiment_id}, {"_id": 0})
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    session = Session(
        participant_id=data.participant_id,
        experiment_id=data.experiment_id
    )
    doc = session.model_dump()
    await db.sessions.insert_one(doc)
    
    await db.experiments.update_one(
        {"id": data.experiment_id},
        {"$inc": {"total_sessions": 1}}
    )
    
    return session

@api_router.get("/sessions", response_model=List[Session])
async def get_sessions(
    experiment_id: Optional[str] = None,
    participant_id: Optional[str] = None,
    status: Optional[SessionStatus] = None
):
    query = {}
    if experiment_id:
        query["experiment_id"] = experiment_id
    if participant_id:
        query["participant_id"] = participant_id
    if status:
        query["status"] = status.value
    sessions = await db.sessions.find(query, {"_id": 0}).to_list(500)
    return sessions

@api_router.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@api_router.post("/sessions/{session_id}/start", response_model=Session)
async def start_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": SessionStatus.ACTIVE.value,
        "started_at": now,
        "simulated_start_time": now,
        "simulated_current_time": now
    }
    await db.sessions.update_one({"id": session_id}, {"$set": update_data})
    updated = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    return updated

@api_router.post("/sessions/{session_id}/notification")
async def record_notification(session_id: str, notification: SimulatedNotification):
    """Record a notification event with full tracking"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    notification_dict = notification.model_dump()
    
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$push": {"notifications": notification_dict},
            "$inc": {"total_notifications_shown": 1}
        }
    )
    
    logging.info(f"Notification recorded for session {session_id}: dose {notification.dose_number}")
    
    return {"message": "Notification recorded", "notification_id": notification.id}

@api_router.post("/sessions/{session_id}/offloading-event")
async def record_offloading_event(session_id: str, event: OffloadingEvent):
    """Record when participant chooses to remember vs set reminder - KEY FOR THESIS"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    event_dict = event.model_dump()
    
    # Update counters based on choice
    inc_fields = {}
    if event.choice == OffloadingChoice.REMEMBER:
        inc_fields["total_remember_choices"] = 1
    else:
        inc_fields["total_offload_choices"] = 1
    
    await db.sessions.update_one(
        {"id": session_id},
        {
            "$push": {"offloading_events": event_dict},
            "$inc": inc_fields
        }
    )
    
    # Recalculate average decision time
    updated_session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    events = updated_session.get("offloading_events", [])
    if events:
        avg_time = sum(e.get("decision_time_ms", 0) for e in events) / len(events)
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"avg_decision_time_ms": avg_time}}
        )
    
    logging.info(f"Offloading event recorded: session {session_id}, choice: {event.choice.value}, decision_time: {event.decision_time_ms}ms")
    
    return {"message": "Offloading event recorded", "event_id": event.id}

@api_router.post("/sessions/{session_id}/recall-probe")
async def record_recall_probe(session_id: str, probe: RecallProbe):
    """Record recall probe with precise timing"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    probe_dict = probe.model_dump()
    
    await db.sessions.update_one(
        {"id": session_id},
        {"$push": {"recall_probes": probe_dict}}
    )
    
    # Recalculate averages
    updated_session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    probes = updated_session.get("recall_probes", [])
    
    if probes:
        # Average response time
        response_times = [p.get("response_time_ms") for p in probes if p.get("response_time_ms")]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {"avg_recall_response_time_ms": avg_response_time}}
            )
        
        # Recall accuracy
        correct_count = sum(1 for p in probes if p.get("is_correct"))
        accuracy = (correct_count / len(probes)) * 100
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"recall_accuracy_percent": accuracy}}
        )
    
    logging.info(f"Recall probe recorded: session {session_id}, correct: {probe.is_correct}, response_time: {probe.response_time_ms}ms")
    
    return {"message": "Recall probe recorded", "probe_id": probe.id}

@api_router.post("/sessions/{session_id}/start-blackout", response_model=Session)
async def start_blackout(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": SessionStatus.BLACKOUT.value, "blackout_started_at": now}}
    )
    
    logging.info(f"Blackout started for session {session_id}")
    
    updated = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    return updated

@api_router.post("/sessions/{session_id}/complete", response_model=Session)
async def complete_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": SessionStatus.COMPLETED.value, "completed_at": now}}
    )
    
    await db.experiments.update_one(
        {"id": session["experiment_id"]},
        {"$inc": {"completed_sessions": 1}}
    )
    
    logging.info(f"Session completed: {session_id}")
    
    updated = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    return updated

@api_router.put("/sessions/{session_id}/strategy-metrics")
async def update_strategy_metrics(session_id: str, scaffolded_interval: Optional[float] = None, faded_prominence: Optional[float] = None):
    """Update strategy-specific tracking metrics"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = {}
    if scaffolded_interval is not None:
        update_data["scaffolded_final_interval"] = scaffolded_interval
    if faded_prominence is not None:
        update_data["faded_final_prominence"] = faded_prominence
    
    if update_data:
        await db.sessions.update_one({"id": session_id}, {"$set": update_data})
    
    return {"message": "Strategy metrics updated"}

# ========================
# ROUTES - Tasks (Progress Tracker)
# ========================

@api_router.post("/tasks", response_model=Task)
async def create_task(data: TaskCreate):
    task = Task(
        title=data.title,
        description=data.description,
        week_number=data.week_number,
        priority=data.priority,
        target_date=data.target_date,
        notes=data.notes,
        category=data.category
    )
    doc = task.model_dump()
    await db.tasks.insert_one(doc)
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(
    week_number: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    category: Optional[str] = None
):
    query = {}
    if week_number:
        query["week_number"] = week_number
    if status:
        query["status"] = status.value
    if priority:
        query["priority"] = priority.value
    if category:
        query["category"] = category
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(500)
    return tasks

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, data: TaskUpdate):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if data.status == TaskStatus.COMPLETED and not task.get("actual_date"):
        update_data["actual_date"] = datetime.now(timezone.utc).isoformat()
    
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return updated

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

# ========================
# ROUTES - Weekly Reports
# ========================

@api_router.post("/weekly-reports", response_model=WeeklyReport)
async def create_weekly_report(data: WeeklyReportCreate):
    tasks = await db.tasks.find({"week_number": data.week_number}, {"_id": 0}).to_list(100)
    tasks_completed = len([t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value])
    
    report = WeeklyReport(
        week_number=data.week_number,
        start_date=data.start_date,
        end_date=data.end_date,
        summary=data.summary,
        accomplishments=data.accomplishments,
        challenges=data.challenges,
        next_week_goals=data.next_week_goals,
        notes=data.notes,
        tasks_completed=tasks_completed,
        tasks_total=len(tasks)
    )
    doc = report.model_dump()
    await db.weekly_reports.insert_one(doc)
    return report

@api_router.get("/weekly-reports", response_model=List[WeeklyReport])
async def get_weekly_reports():
    reports = await db.weekly_reports.find({}, {"_id": 0}).sort("week_number", 1).to_list(52)
    return reports

@api_router.get("/weekly-reports/{report_id}", response_model=WeeklyReport)
async def get_weekly_report(report_id: str):
    report = await db.weekly_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report

@api_router.put("/weekly-reports/{report_id}", response_model=WeeklyReport)
async def update_weekly_report(report_id: str, data: WeeklyReportCreate):
    report = await db.weekly_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    
    tasks = await db.tasks.find({"week_number": data.week_number}, {"_id": 0}).to_list(100)
    tasks_completed = len([t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value])
    
    update_data = data.model_dump()
    update_data["tasks_completed"] = tasks_completed
    update_data["tasks_total"] = len(tasks)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.weekly_reports.update_one({"id": report_id}, {"$set": update_data})
    updated = await db.weekly_reports.find_one({"id": report_id}, {"_id": 0})
    return updated

# ========================
# ROUTES - Analytics
# ========================

@api_router.get("/analytics/experiments/{experiment_id}")
async def get_experiment_analytics(experiment_id: str):
    experiment = await db.experiments.find_one({"id": experiment_id}, {"_id": 0})
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    sessions = await db.sessions.find({"experiment_id": experiment_id}, {"_id": 0}).to_list(1000)
    completed_sessions = [s for s in sessions if s.get("status") == SessionStatus.COMPLETED.value]
    
    # Recall accuracy
    total_probes = 0
    correct_probes = 0
    all_response_times = []
    
    for session in completed_sessions:
        for probe in session.get("recall_probes", []):
            total_probes += 1
            if probe.get("is_correct"):
                correct_probes += 1
            if probe.get("response_time_ms"):
                all_response_times.append(probe["response_time_ms"])
    
    avg_recall_accuracy = (correct_probes / total_probes * 100) if total_probes > 0 else 0
    avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
    
    # Offloading analysis
    total_remember = sum(s.get("total_remember_choices", 0) for s in completed_sessions)
    total_offload = sum(s.get("total_offload_choices", 0) for s in completed_sessions)
    offloading_rate = (total_offload / (total_remember + total_offload) * 100) if (total_remember + total_offload) > 0 else 0
    
    # Decision time
    decision_times = [s.get("avg_decision_time_ms") for s in completed_sessions if s.get("avg_decision_time_ms")]
    avg_decision_time = sum(decision_times) / len(decision_times) if decision_times else 0
    
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment["name"],
        "strategy": experiment["config"]["notification_strategy"],
        "total_sessions": len(sessions),
        "completed_sessions": len(completed_sessions),
        "avg_recall_accuracy": round(avg_recall_accuracy, 2),
        "avg_response_time_ms": round(avg_response_time, 2),
        "total_remember_choices": total_remember,
        "total_offload_choices": total_offload,
        "offloading_rate_percent": round(offloading_rate, 2),
        "avg_decision_time_ms": round(avg_decision_time, 2),
        "total_notifications": sum(len(s.get("notifications", [])) for s in sessions),
        "total_recall_probes": total_probes
    }

@api_router.get("/analytics/overview")
async def get_analytics_overview():
    experiments = await db.experiments.find({}, {"_id": 0}).to_list(100)
    sessions = await db.sessions.find({}, {"_id": 0}).to_list(1000)
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(500)
    participants = await db.participants.find({}, {"_id": 0}).to_list(500)
    
    completed_sessions = [s for s in sessions if s.get("status") == SessionStatus.COMPLETED.value]
    completed_tasks = [t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value]
    
    # Strategy breakdown
    strategy_counts = {}
    for exp in experiments:
        strategy = exp.get("config", {}).get("notification_strategy", "unknown")
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    # Overall offloading stats
    total_remember = sum(s.get("total_remember_choices", 0) for s in completed_sessions)
    total_offload = sum(s.get("total_offload_choices", 0) for s in completed_sessions)
    
    return {
        "total_experiments": len(experiments),
        "active_experiments": len([e for e in experiments if e.get("is_active")]),
        "total_sessions": len(sessions),
        "completed_sessions": len(completed_sessions),
        "total_participants": len(participants),
        "total_tasks": len(tasks),
        "completed_tasks": len(completed_tasks),
        "task_completion_rate": round(len(completed_tasks) / len(tasks) * 100, 2) if tasks else 0,
        "strategy_breakdown": strategy_counts,
        "total_remember_choices": total_remember,
        "total_offload_choices": total_offload
    }

@api_router.get("/analytics/progress")
async def get_progress_analytics():
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(500)
    reports = await db.weekly_reports.find({}, {"_id": 0}).to_list(52)
    
    weeks_data = {}
    for task in tasks:
        week = task.get("week_number", 0)
        if week not in weeks_data:
            weeks_data[week] = {"total": 0, "completed": 0, "in_progress": 0}
        weeks_data[week]["total"] += 1
        if task.get("status") == TaskStatus.COMPLETED.value:
            weeks_data[week]["completed"] += 1
        elif task.get("status") == TaskStatus.IN_PROGRESS.value:
            weeks_data[week]["in_progress"] += 1
    
    priority_counts = {p.value: 0 for p in TaskPriority}
    for task in tasks:
        priority = task.get("priority", TaskPriority.P1.value)
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    return {
        "weeks_data": weeks_data,
        "priority_breakdown": priority_counts,
        "total_reports": len(reports),
        "total_weeks_tracked": len(weeks_data)
    }

@api_router.get("/analytics/offloading-comparison")
async def get_offloading_comparison():
    """Compare offloading behavior across different notification strategies - KEY FOR THESIS"""
    experiments = await db.experiments.find({}, {"_id": 0}).to_list(100)
    
    comparison_data = []
    
    for exp in experiments:
        sessions = await db.sessions.find({
            "experiment_id": exp["id"],
            "status": SessionStatus.COMPLETED.value
        }, {"_id": 0}).to_list(1000)
        
        if not sessions:
            continue
        
        total_remember = sum(s.get("total_remember_choices", 0) for s in sessions)
        total_offload = sum(s.get("total_offload_choices", 0) for s in sessions)
        total_choices = total_remember + total_offload
        
        recall_accuracies = [s.get("recall_accuracy_percent") for s in sessions if s.get("recall_accuracy_percent") is not None]
        avg_recall = sum(recall_accuracies) / len(recall_accuracies) if recall_accuracies else 0
        
        decision_times = [s.get("avg_decision_time_ms") for s in sessions if s.get("avg_decision_time_ms")]
        avg_decision = sum(decision_times) / len(decision_times) if decision_times else 0
        
        comparison_data.append({
            "experiment_id": exp["id"],
            "experiment_name": exp["name"],
            "strategy": exp["config"]["notification_strategy"],
            "num_sessions": len(sessions),
            "offloading_rate": round((total_offload / total_choices * 100) if total_choices > 0 else 0, 2),
            "remember_rate": round((total_remember / total_choices * 100) if total_choices > 0 else 0, 2),
            "avg_recall_accuracy": round(avg_recall, 2),
            "avg_decision_time_ms": round(avg_decision, 2)
        })
    
    return {
        "comparison": comparison_data,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# ========================
# ROUTES - Data Export
# ========================

@api_router.get("/export/sessions")
async def export_sessions(
    experiment_id: Optional[str] = None,
    format: str = Query(default="json", enum=["json", "csv"])
):
    query = {}
    if experiment_id:
        query["experiment_id"] = experiment_id
    
    sessions = await db.sessions.find(query, {"_id": 0}).to_list(1000)
    
    if format == "csv":
        output = io.StringIO()
        if sessions:
            flat_sessions = []
            for s in sessions:
                flat = {
                    "id": s["id"],
                    "participant_id": s["participant_id"],
                    "experiment_id": s["experiment_id"],
                    "status": s["status"],
                    "started_at": s.get("started_at", ""),
                    "completed_at": s.get("completed_at", ""),
                    "total_notifications": len(s.get("notifications", [])),
                    "total_recall_probes": len(s.get("recall_probes", [])),
                    "total_remember_choices": s.get("total_remember_choices", 0),
                    "total_offload_choices": s.get("total_offload_choices", 0),
                    "avg_decision_time_ms": s.get("avg_decision_time_ms", ""),
                    "avg_recall_response_time_ms": s.get("avg_recall_response_time_ms", ""),
                    "recall_accuracy_percent": s.get("recall_accuracy_percent", "")
                }
                flat_sessions.append(flat)
            
            writer = csv.DictWriter(output, fieldnames=flat_sessions[0].keys())
            writer.writeheader()
            writer.writerows(flat_sessions)
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sessions_export.csv"}
        )
    
    return sessions

@api_router.get("/export/full-research-data")
async def export_full_research_data():
    """Export all research data for thesis analysis"""
    experiments = await db.experiments.find({}, {"_id": 0}).to_list(100)
    participants = await db.participants.find({}, {"_id": 0}).to_list(1000)
    sessions = await db.sessions.find({}, {"_id": 0}).to_list(1000)
    
    return {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "experiments": experiments,
        "participants": participants,
        "sessions": sessions,
        "summary": {
            "total_experiments": len(experiments),
            "total_participants": len(participants),
            "total_sessions": len(sessions),
            "completed_sessions": len([s for s in sessions if s.get("status") == "completed"])
        }
    }

@api_router.get("/export/tasks")
async def export_tasks(format: str = Query(default="json", enum=["json", "csv"])):
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(500)
    
    if format == "csv":
        output = io.StringIO()
        if tasks:
            writer = csv.DictWriter(output, fieldnames=tasks[0].keys())
            writer.writeheader()
            writer.writerows(tasks)
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tasks_export.csv"}
        )
    
    return tasks

# ========================
# ROUTES - PDF Report
# ========================

@api_router.get("/export/pdf-report")
async def export_pdf_report(experiment_id: Optional[str] = None):
    """Generate a thesis-quality PDF report with strategy comparisons, demographics, and offloading data"""
    
    # Gather all data
    experiments = await db.experiments.find({}, {"_id": 0}).to_list(100)
    participants = await db.participants.find({}, {"_id": 0}).to_list(1000)
    sessions = await db.sessions.find({}, {"_id": 0}).to_list(1000)
    
    if experiment_id:
        experiments = [e for e in experiments if e["id"] == experiment_id]
        sessions = [s for s in sessions if s["experiment_id"] == experiment_id]
        participant_ids = {s["participant_id"] for s in sessions}
        participants = [p for p in participants if p["id"] in participant_ids]
    
    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
    
    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=22, spaceAfter=6, textColor=colors.HexColor('#1E3A5F'))
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#4B5563'), spaceAfter=20)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1E3A5F'), spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#374151'))
    caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6B7280'), spaceAfter=12)
    
    elements = []
    
    # --- Title Page ---
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("Prospective Memory & Cognitive Offloading", title_style))
    elements.append(Paragraph("Research Data Report", ParagraphStyle('SubHead', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#0D9488'))))
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}", caption_style))
    elements.append(Paragraph(f"Total Experiments: {len(experiments)} | Total Participants: {len(participants)} | Completed Sessions: {len(completed_sessions)}", body_style))
    elements.append(PageBreak())
    
    # --- 1. Study Overview ---
    elements.append(Paragraph("1. Study Overview", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.3*cm))
    
    overview_data = [["Metric", "Value"]]
    overview_data.append(["Total Experiments", str(len(experiments))])
    overview_data.append(["Total Participants", str(len(participants))])
    overview_data.append(["Total Sessions", str(len(sessions))])
    overview_data.append(["Completed Sessions", str(len(completed_sessions))])
    overview_data.append(["Completion Rate", f"{round(len(completed_sessions)/len(sessions)*100, 1) if sessions else 0}%"])
    
    overview_table = Table(overview_data, colWidths=[8*cm, 8*cm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # --- 2. Experiment Configurations ---
    elements.append(Paragraph("2. Experiment Configurations", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.3*cm))
    
    exp_data = [["Name", "Strategy", "Freq (min)", "Doses", "Duration (min)", "Sessions"]]
    for exp in experiments:
        config = exp.get("config", {})
        exp_data.append([
            exp["name"][:30],
            config.get("notification_strategy", "N/A").replace("_", " ").title(),
            str(config.get("notification_frequency_minutes", "N/A")),
            str(config.get("num_doses", "N/A")),
            str(config.get("total_duration_minutes", "N/A")),
            f"{exp.get('completed_sessions', 0)}/{exp.get('total_sessions', 0)}"
        ])
    
    col_widths = [4.5*cm, 3*cm, 2*cm, 1.5*cm, 2.5*cm, 2.5*cm]
    exp_table = Table(exp_data, colWidths=col_widths)
    exp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(exp_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # --- 3. Strategy Comparison (KEY THESIS DATA) ---
    elements.append(Paragraph("3. Cognitive Offloading: Strategy Comparison", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("This table presents the core thesis data comparing offloading behavior across notification strategies.", caption_style))
    
    strategy_data = [["Strategy", "N Sessions", "Offload Rate", "Remember Rate", "Recall Accuracy", "Avg Decision (ms)"]]
    
    for exp in experiments:
        exp_sessions = [s for s in completed_sessions if s.get("experiment_id") == exp["id"]]
        if not exp_sessions:
            continue
        
        total_remember = sum(s.get("total_remember_choices", 0) for s in exp_sessions)
        total_offload = sum(s.get("total_offload_choices", 0) for s in exp_sessions)
        total_choices = total_remember + total_offload
        offload_rate = round((total_offload / total_choices * 100), 1) if total_choices > 0 else 0
        remember_rate = round((total_remember / total_choices * 100), 1) if total_choices > 0 else 0
        
        recall_accs = [s.get("recall_accuracy_percent") for s in exp_sessions if s.get("recall_accuracy_percent") is not None]
        avg_recall = round(sum(recall_accs) / len(recall_accs), 1) if recall_accs else 0
        
        dec_times = [s.get("avg_decision_time_ms") for s in exp_sessions if s.get("avg_decision_time_ms")]
        avg_decision = round(sum(dec_times) / len(dec_times), 1) if dec_times else 0
        
        strategy_data.append([
            exp["config"]["notification_strategy"].replace("_", " ").title(),
            str(len(exp_sessions)),
            f"{offload_rate}%",
            f"{remember_rate}%",
            f"{avg_recall}%",
            str(avg_decision)
        ])
    
    if len(strategy_data) > 1:
        strat_table = Table(strategy_data, colWidths=[3*cm, 2*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm])
        strat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0FDFA')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(strat_table)
    else:
        elements.append(Paragraph("No completed sessions available for strategy comparison.", body_style))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # --- 4. Demographics Summary ---
    elements.append(Paragraph("4. Participant Demographics", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.3*cm))
    
    # Age group distribution
    age_dist = {}
    edu_dist = {}
    tech_dist = {}
    memory_ratings = []
    
    for p in participants:
        demo = p.get("demographics") or {}
        if demo.get("age_group"):
            age_dist[demo["age_group"]] = age_dist.get(demo["age_group"], 0) + 1
        if demo.get("education"):
            edu_dist[demo["education"]] = edu_dist.get(demo["education"], 0) + 1
        if demo.get("tech_familiarity"):
            tech_dist[demo["tech_familiarity"]] = tech_dist.get(demo["tech_familiarity"], 0) + 1
        if demo.get("memory_self_rating"):
            memory_ratings.append(demo["memory_self_rating"])
    
    if age_dist:
        demo_data = [["Age Group", "Count", "Percentage"]]
        total_p = sum(age_dist.values())
        for age, count in sorted(age_dist.items()):
            demo_data.append([age, str(count), f"{round(count/total_p*100, 1)}%"])
        
        demo_table = Table(demo_data, colWidths=[5*cm, 4*cm, 4*cm])
        demo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAF5FF')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(Paragraph("Age Group Distribution", ParagraphStyle('SubSec', parent=body_style, fontSize=11, textColor=colors.HexColor('#1E3A5F'), spaceAfter=6)))
        elements.append(demo_table)
        elements.append(Spacer(1, 0.3*cm))
    
    if edu_dist:
        edu_data = [["Education Level", "Count", "Percentage"]]
        total_e = sum(edu_dist.values())
        for edu, count in sorted(edu_dist.items()):
            edu_data.append([edu.replace("_", " ").title(), str(count), f"{round(count/total_e*100, 1)}%"])
        
        edu_table = Table(edu_data, colWidths=[5*cm, 4*cm, 4*cm])
        edu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAF5FF')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(Paragraph("Education Level Distribution", ParagraphStyle('SubSec2', parent=body_style, fontSize=11, textColor=colors.HexColor('#1E3A5F'), spaceAfter=6)))
        elements.append(edu_table)
        elements.append(Spacer(1, 0.3*cm))
    
    if memory_ratings:
        avg_memory = round(sum(memory_ratings) / len(memory_ratings), 2)
        elements.append(Paragraph(f"Average Memory Self-Rating: {avg_memory}/5 (n={len(memory_ratings)})", body_style))
    
    if not age_dist and not edu_dist:
        elements.append(Paragraph("No demographic data collected yet.", body_style))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # --- 5. Session-Level Data ---
    elements.append(Paragraph("5. Session-Level Results", heading_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.3*cm))
    
    if completed_sessions:
        session_data = [["Session", "Strategy", "Remember", "Offload", "Recall %", "Avg Decision (ms)", "Avg Recall RT (ms)"]]
        for i, s in enumerate(completed_sessions[:50], 1):
            exp_match = next((e for e in experiments if e["id"] == s.get("experiment_id")), None)
            strategy = exp_match["config"]["notification_strategy"].replace("_", " ").title() if exp_match else "N/A"
            
            session_data.append([
                str(i),
                strategy,
                str(s.get("total_remember_choices", 0)),
                str(s.get("total_offload_choices", 0)),
                f"{round(s.get('recall_accuracy_percent', 0), 1)}%",
                str(round(s.get("avg_decision_time_ms", 0), 1)),
                str(round(s.get("avg_recall_response_time_ms", 0), 1))
            ])
        
        sess_col_widths = [1.5*cm, 2.5*cm, 2*cm, 2*cm, 2*cm, 3*cm, 3*cm]
        sess_table = Table(session_data, colWidths=sess_col_widths)
        sess_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(sess_table)
        if len(completed_sessions) > 50:
            elements.append(Paragraph(f"Showing 50 of {len(completed_sessions)} sessions.", caption_style))
    else:
        elements.append(Paragraph("No completed sessions available.", body_style))
    
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("End of Report — Generated by PM Research Lab", caption_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"pm_research_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ========================
# ROUTES - Enhanced Export (Data Validation)
# ========================

@api_router.get("/export/validated-research-data")
async def export_validated_research_data():
    """Enhanced export with all thesis-critical fields validated and cross-referenced"""
    experiments = await db.experiments.find({}, {"_id": 0}).to_list(100)
    participants = await db.participants.find({}, {"_id": 0}).to_list(1000)
    sessions = await db.sessions.find({}, {"_id": 0}).to_list(1000)
    
    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
    
    # Build cross-referenced participant-session data
    validated_sessions = []
    for s in sessions:
        participant = next((p for p in participants if p["id"] == s.get("participant_id")), None)
        experiment = next((e for e in experiments if e["id"] == s.get("experiment_id")), None)
        
        # Calculate per-session metrics
        offloading_events = s.get("offloading_events", [])
        recall_probes = s.get("recall_probes", [])
        
        decision_times = [e.get("decision_time_ms", 0) for e in offloading_events if e.get("decision_time_ms")]
        recall_response_times = [p.get("response_time_ms", 0) for p in recall_probes if p.get("response_time_ms")]
        recall_correct = sum(1 for p in recall_probes if p.get("is_correct"))
        
        validated_sessions.append({
            "session_id": s["id"],
            "participant_id": s.get("participant_id"),
            "experiment_id": s.get("experiment_id"),
            "experiment_name": experiment["name"] if experiment else "N/A",
            "strategy": experiment["config"]["notification_strategy"] if experiment else "N/A",
            "status": s.get("status"),
            "started_at": s.get("started_at"),
            "completed_at": s.get("completed_at"),
            "demographics": participant.get("demographics") if participant else None,
            "total_notifications": len(s.get("notifications", [])),
            "total_remember_choices": s.get("total_remember_choices", 0),
            "total_offload_choices": s.get("total_offload_choices", 0),
            "offloading_rate": round(s.get("total_offload_choices", 0) / max(s.get("total_remember_choices", 0) + s.get("total_offload_choices", 0), 1) * 100, 2),
            "total_recall_probes": len(recall_probes),
            "recall_correct": recall_correct,
            "recall_accuracy_percent": round(recall_correct / max(len(recall_probes), 1) * 100, 2),
            "avg_decision_time_ms": round(sum(decision_times) / max(len(decision_times), 1), 2) if decision_times else None,
            "min_decision_time_ms": min(decision_times) if decision_times else None,
            "max_decision_time_ms": max(decision_times) if decision_times else None,
            "avg_recall_response_time_ms": round(sum(recall_response_times) / max(len(recall_response_times), 1), 2) if recall_response_times else None,
            "min_recall_response_time_ms": min(recall_response_times) if recall_response_times else None,
            "max_recall_response_time_ms": max(recall_response_times) if recall_response_times else None,
            "scaffolded_final_interval": s.get("scaffolded_final_interval"),
            "faded_final_prominence": s.get("faded_final_prominence"),
            "offloading_events": offloading_events,
            "recall_probes": recall_probes,
        })
    
    # Demographics cross-tab summary
    demographics_summary = {
        "age_groups": {},
        "education_levels": {},
        "tech_familiarity": {},
        "memory_self_ratings": [],
    }
    
    for p in participants:
        demo = p.get("demographics") or {}
        if demo.get("age_group"):
            demographics_summary["age_groups"][demo["age_group"]] = demographics_summary["age_groups"].get(demo["age_group"], 0) + 1
        if demo.get("education"):
            demographics_summary["education_levels"][demo["education"]] = demographics_summary["education_levels"].get(demo["education"], 0) + 1
        if demo.get("tech_familiarity"):
            demographics_summary["tech_familiarity"][demo["tech_familiarity"]] = demographics_summary["tech_familiarity"].get(demo["tech_familiarity"], 0) + 1
        if demo.get("memory_self_rating") is not None:
            demographics_summary["memory_self_ratings"].append(demo["memory_self_rating"])
    
    # Strategy-level aggregations
    strategy_summary = {}
    for exp in experiments:
        strategy = exp["config"]["notification_strategy"]
        exp_sessions = [s for s in validated_sessions if s["experiment_id"] == exp["id"] and s["status"] == "completed"]
        
        if not exp_sessions:
            continue
        
        all_decision_times = []
        all_recall_times = []
        for vs in exp_sessions:
            if vs.get("avg_decision_time_ms") is not None:
                all_decision_times.append(vs["avg_decision_time_ms"])
            if vs.get("avg_recall_response_time_ms") is not None:
                all_recall_times.append(vs["avg_recall_response_time_ms"])
        
        total_rem = sum(s["total_remember_choices"] for s in exp_sessions)
        total_off = sum(s["total_offload_choices"] for s in exp_sessions)
        total_ch = total_rem + total_off
        
        strategy_summary[strategy] = {
            "experiment_count": 1 if strategy not in strategy_summary else strategy_summary.get(strategy, {}).get("experiment_count", 0) + 1,
            "total_sessions": len(exp_sessions),
            "total_remember_choices": total_rem,
            "total_offload_choices": total_off,
            "offloading_rate": round(total_off / max(total_ch, 1) * 100, 2),
            "avg_recall_accuracy": round(sum(s["recall_accuracy_percent"] for s in exp_sessions) / len(exp_sessions), 2),
            "avg_decision_time_ms": round(sum(all_decision_times) / len(all_decision_times), 2) if all_decision_times else None,
            "avg_recall_response_time_ms": round(sum(all_recall_times) / len(all_recall_times), 2) if all_recall_times else None,
        }
    
    return {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "data_integrity": {
            "total_experiments": len(experiments),
            "total_participants": len(participants),
            "total_sessions": len(sessions),
            "completed_sessions": len(completed_sessions),
            "sessions_with_demographics": len([s for s in validated_sessions if s.get("demographics")]),
            "sessions_with_offloading_data": len([s for s in validated_sessions if s["total_remember_choices"] + s["total_offload_choices"] > 0]),
            "sessions_with_recall_data": len([s for s in validated_sessions if s["total_recall_probes"] > 0]),
        },
        "strategy_summary": strategy_summary,
        "demographics_summary": demographics_summary,
        "experiments": experiments,
        "sessions": validated_sessions,
    }

# ========================
# SEED DATA
# ========================

@api_router.post("/seed")
async def seed_data():
    """Seed initial data for demonstration"""
    
    await db.experiments.delete_many({})
    await db.participants.delete_many({})
    await db.sessions.delete_many({})
    await db.tasks.delete_many({})
    await db.weekly_reports.delete_many({})
    
    experiments = [
        Experiment(
            name="JIT Notification Study",
            description="Testing Just-in-Time notifications for multi-dose vaccination adherence",
            share_code="JIT2026A",
            config=ExperimentConfig(
                notification_strategy=NotificationStrategy.JUST_IN_TIME,
                notification_frequency_minutes=30,
                blackout_duration_minutes=60,
                total_duration_minutes=180,
                time_compression_factor=60.0,
                num_doses=3
            ),
            total_sessions=5,
            completed_sessions=3
        ),
        Experiment(
            name="Scaffolded Reminder Study",
            description="Testing scaffolded reminders that increase interval over time",
            share_code="SCF2026B",
            config=ExperimentConfig(
                notification_strategy=NotificationStrategy.SCAFFOLDED,
                notification_frequency_minutes=20,
                blackout_duration_minutes=90,
                total_duration_minutes=240,
                time_compression_factor=120.0,
                num_doses=4,
                scaffolded_increase_factor=1.5
            ),
            total_sessions=3,
            completed_sessions=2
        ),
        Experiment(
            name="Faded Reminder Study",
            description="Testing faded reminders that become less prominent over time",
            share_code="FAD2026C",
            config=ExperimentConfig(
                notification_strategy=NotificationStrategy.FADED,
                notification_frequency_minutes=25,
                blackout_duration_minutes=75,
                total_duration_minutes=200,
                time_compression_factor=80.0,
                num_doses=3,
                faded_opacity_decay=0.2
            ),
            total_sessions=2,
            completed_sessions=1
        ),
        Experiment(
            name="Control Group - No Reminders",
            description="Control condition with no automated reminders",
            share_code="CTL2026D",
            config=ExperimentConfig(
                notification_strategy=NotificationStrategy.CONTROL,
                notification_frequency_minutes=0,
                blackout_duration_minutes=120,
                total_duration_minutes=180,
                time_compression_factor=60.0,
                num_doses=3
            ),
            total_sessions=4,
            completed_sessions=4
        )
    ]
    
    for exp in experiments:
        await db.experiments.insert_one(exp.model_dump())
    
    tasks = [
        Task(title="Literature Review - PM & Cognitive Offloading", week_number=1, priority=TaskPriority.P0, status=TaskStatus.COMPLETED, category="Research", notes="Completed review of 15 key papers"),
        Task(title="Define Research Questions", week_number=1, priority=TaskPriority.P0, status=TaskStatus.COMPLETED, category="Research"),
        Task(title="Design Experiment Protocol", week_number=2, priority=TaskPriority.P0, status=TaskStatus.COMPLETED, category="Design"),
        Task(title="Create Notification Strategy Framework", week_number=2, priority=TaskPriority.P1, status=TaskStatus.COMPLETED, category="Design"),
        Task(title="Build Backend API", week_number=3, priority=TaskPriority.P0, status=TaskStatus.COMPLETED, category="Development"),
        Task(title="Implement Offloading Choice Mechanism", week_number=3, priority=TaskPriority.P0, status=TaskStatus.COMPLETED, category="Development"),
        Task(title="Implement Scaffolded/Faded Algorithms", week_number=4, priority=TaskPriority.P0, status=TaskStatus.IN_PROGRESS, category="Development"),
        Task(title="Create Researcher Dashboard", week_number=4, priority=TaskPriority.P1, status=TaskStatus.COMPLETED, category="Development"),
        Task(title="Build Participant Interface", week_number=5, priority=TaskPriority.P1, status=TaskStatus.COMPLETED, category="Development"),
        Task(title="Implement Response Time Tracking", week_number=5, priority=TaskPriority.P0, status=TaskStatus.COMPLETED, category="Development"),
        Task(title="Analytics & Data Export", week_number=6, priority=TaskPriority.P1, status=TaskStatus.COMPLETED, category="Development"),
        Task(title="Pilot Testing", week_number=7, priority=TaskPriority.P1, status=TaskStatus.NOT_STARTED, category="Testing"),
        Task(title="Data Analysis", week_number=8, priority=TaskPriority.P0, status=TaskStatus.NOT_STARTED, category="Analysis"),
        Task(title="Thesis Writing", week_number=9, priority=TaskPriority.P0, status=TaskStatus.NOT_STARTED, category="Documentation"),
    ]
    
    for task in tasks:
        await db.tasks.insert_one(task.model_dump())
    
    reports = [
        WeeklyReport(
            week_number=1,
            start_date="2026-01-06",
            end_date="2026-01-12",
            summary="Completed foundational research phase",
            accomplishments=["Reviewed 15 key papers on PM", "Defined research questions", "Identified notification strategies"],
            challenges=["Large volume of literature"],
            next_week_goals=["Design experiment protocol", "Create notification framework"],
            tasks_completed=2,
            tasks_total=2
        ),
        WeeklyReport(
            week_number=2,
            start_date="2026-01-13",
            end_date="2026-01-19",
            summary="Experiment design phase completed",
            accomplishments=["Finalized experiment protocol", "Created JIT, Scaffolded, Faded strategy definitions"],
            challenges=["Balancing complexity with feasibility"],
            next_week_goals=["Start backend development", "Implement offloading mechanism"],
            tasks_completed=2,
            tasks_total=2
        ),
    ]
    
    for report in reports:
        await db.weekly_reports.insert_one(report.model_dump())
    
    return {
        "message": "Seed data created",
        "experiments": len(experiments),
        "tasks": len(tasks),
        "weekly_reports": len(reports)
    }

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
