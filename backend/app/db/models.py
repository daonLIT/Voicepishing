from sqlalchemy import Column, Integer, String, Boolean, JSON, Text, ForeignKey, TIMESTAMP, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from .base import Base

class AttackMethod(Base):
    __tablename__ = "attack_method"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)

class AgentProfile(Base):
    __tablename__ = "agent_profile"
    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)  # attacker/victim/police
    name = Column(String)
    provider = Column(String)              # gpt/gemini/system
    age_group = Column(String)
    traits = Column(JSON)
    is_active = Column(Boolean, default=True)

class SimRun(Base):
    __tablename__ = "sim_run"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    seed = Column(Integer)
    total_rounds = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class SimIteration(Base):
    __tablename__ = "sim_iteration"
    id = Column(Integer, primary_key=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("sim_run.id", ondelete="CASCADE"))
    round_index = Column(Integer, nullable=False)
    status = Column(String, default="pending")

class SimAttempt(Base):
    __tablename__ = "sim_attempt"
    id = Column(Integer, primary_key=True)
    iteration_id = Column(Integer, ForeignKey("sim_iteration.id", ondelete="CASCADE"))
    method_id = Column(Integer, ForeignKey("attack_method.id"))
    attacker_id = Column(Integer, ForeignKey("agent_profile.id"))
    victim_id = Column(Integer, ForeignKey("agent_profile.id"))
    phase = Column(String, nullable=False)  # pre_edu/post_edu
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    finished_at = Column(TIMESTAMP)

class Conversation(Base):
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("sim_attempt.id", ondelete="CASCADE"))
    transcript = Column(JSON)
    redacted_transcript = Column(JSON)
    tokens = Column(Integer)
    cost_usd = Column(Numeric(10,4))

class Outcome(Base):
    __tablename__ = "outcome"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("sim_attempt.id", ondelete="CASCADE"), unique=True)
    is_phished = Column(Boolean, nullable=False)
    rationale = Column(Text)
    confidence = Column(Numeric(4,3))
    method_code = Column(String)
    victim_age_group = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class PoliceEducation(Base):
    __tablename__ = "police_education"
    id = Column(Integer, primary_key=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("sim_run.id"))
    generated_from = Column(JSON)
    title = Column(String)
    content_md = Column(Text)
    rules = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class EducationAssignment(Base):
    __tablename__ = "education_assignment"
    id = Column(Integer, primary_key=True)
    education_id = Column(Integer, ForeignKey("police_education.id", ondelete="CASCADE"))
    victim_id = Column(Integer, ForeignKey("agent_profile.id"))
    applied_at = Column(TIMESTAMP, default=datetime.utcnow)

class VictimMemory(Base):
    __tablename__ = "victim_memory"
    id = Column(Integer, primary_key=True)
    victim_id = Column(Integer, ForeignKey("agent_profile.id"))
    snapshot_at = Column(TIMESTAMP, default=datetime.utcnow)
    education_ids = Column(ARRAY(Integer), default=[])
    keywords = Column(ARRAY(String), default=[])
    counters = Column(JSON)
