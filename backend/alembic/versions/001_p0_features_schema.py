"""
Alembic Database Migrations - Phase 1 (P0 Features)

Adds new tables for:
- P0.4: Local patient data + consent tracking
- P0.5: Expert clinical reviews + CCR calculation
- P0.6: Immutable prediction audit logs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration metadata
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create new tables for Phase 1 features"""
    
    # ==================== P0.4: Local Patient Data ====================
    op.create_table(
        'local_patient',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('anonymized_patient_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('age_bracket', sa.String(20), nullable=False),
        sa.Column('diabetes_status', sa.String(50), nullable=False),
        sa.Column('iop_left', sa.Float, nullable=True),
        sa.Column('iop_right', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('_is_deleted', sa.Boolean, server_default='false'),
        comment='P0.4: Local patient records with SHA-256 anonymized IDs'
    )
    
    op.create_index('ix_local_patient_anonymized_id', 'local_patient', ['anonymized_patient_id'])
    
    # ==================== P0.4: Consent Records (Immutable) ====================
    op.create_table(
        'consent_record',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('patient_hash', sa.String(64), nullable=False, index=True),
        sa.Column('consent_type', sa.String(50), nullable=False),
        sa.Column('consent_date', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expiry_date', sa.Date, nullable=False),
        sa.Column('is_valid', sa.Boolean, server_default='true'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        comment='P0.4: Immutable consent audit trail (cannot be modified after creation)'
    )
    
    op.create_index('ix_consent_record_patient_hash', 'consent_record', ['patient_hash'])
    op.create_index('ix_consent_record_type', 'consent_record', ['consent_type'])
    
    # ==================== P0.5: Expert Reviews ====================
    op.create_table(
        'expert_review',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('patient_hash', sa.String(64), nullable=False, index=True),
        sa.Column('clinician_id', sa.String(100), nullable=False),
        sa.Column('dr_assessment', sa.Integer, nullable=False),  # 1-5 Likert
        sa.Column('glaucoma_assessment', sa.Integer, nullable=False),
        sa.Column('refraction_assessment', sa.Integer, nullable=False),
        sa.Column('avg_assessment', sa.Float, nullable=True),
        sa.Column('clinician_notes', sa.Text, nullable=True),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        comment='P0.5: Expert clinical reviews for H3 hypothesis validation (CCR ≥85%)'
    )
    
    op.create_index('ix_expert_review_patient_hash', 'expert_review', ['patient_hash'])
    op.create_index('ix_expert_review_clinician_id', 'expert_review', ['clinician_id'])
    
    # ==================== P0.5: CCR Metrics (Aggregate) ====================
    op.create_table(
        'ccr_metrics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('total_cases', sa.Integer, server_default='0'),
        sa.Column('cases_above_threshold', sa.Integer, server_default='0'),
        sa.Column('global_ccr', sa.Float, nullable=True),
        sa.Column('dr_ccr', sa.Float, nullable=True),
        sa.Column('glaucoma_ccr', sa.Float, nullable=True),
        sa.Column('refraction_ccr', sa.Float, nullable=True),
        sa.Column('h3_hypothesis_status', sa.String(20), default='PENDING'),  # PASS, FAIL, PENDING
        sa.Column('confidence_interval_lower', sa.Float, nullable=True),
        sa.Column('confidence_interval_upper', sa.Float, nullable=True),
        sa.Column('last_updated', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='P0.5: Aggregate CCR metrics for H3 hypothesis validation'
    )
    
    # ==================== P0.6: Audit Log (Immutable) ====================
    op.create_table(
        'prediction_audit_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('log_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('anonymized_patient_hash', sa.String(64), nullable=False, index=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('task', sa.String(50), nullable=False),  # DR, Glaucoma, Refraction
        sa.Column('prediction', sa.String(255), nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('correction_applied', sa.Boolean, server_default='false'),
        sa.Column('correction_factor', sa.Float, nullable=True),
        sa.Column('consent_verified', sa.Boolean, server_default='false'),
        sa.Column('ethics_approval_id', sa.String(50), nullable=True),
        sa.Column('clinician_id', sa.String(100), nullable=True),
        sa.Column('clinician_agreement', sa.Integer, nullable=True),  # 1-5
        sa.Column('clinician_feedback', sa.Text, nullable=True),
        sa.Column('clinician_feedback_timestamp', sa.DateTime, nullable=True),
        # IMPORTANT: No UPDATE allowed on core fields; only INSERT and feedback append
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        comment='P0.6: Immutable audit trail - append-only design (cannot be modified or deleted)'
    )
    
    op.create_index('ix_audit_log_patient_hash', 'prediction_audit_log', ['anonymized_patient_hash'])
    op.create_index('ix_audit_log_timestamp', 'prediction_audit_log', ['timestamp'])
    op.create_index('ix_audit_log_task', 'prediction_audit_log', ['task'])

def downgrade():
    """Rollback Phase 1 migrations"""
    
    # Drop tables in reverse order (foreign key dependencies first)
    op.drop_table('prediction_audit_log')
    op.drop_table('ccr_metrics')
    op.drop_table('expert_review')
    op.drop_table('consent_record')
    op.drop_table('local_patient')
