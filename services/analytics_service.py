from collections import Counter, defaultdict
from datetime import datetime, timezone
import math
from statistics import mean
from typing import Optional

from sqlalchemy.orm import Session

from core.config import settings
from models.models import AnalyticsEvent, PredictionRecord, User
from schemas.schemas import (
    AccountsKpi,
    AdminDashboardResponse,
    AdminFilterEcho,
    AdminMetricsResponse,
    FeatureUsageMetric,
    ModelUsageMetric,
    OperationsSummary,
    SaaSMetrics,
    TrendPoint,
    UsageFunnel,
    WorkflowSplitItem,
)


def _normalize_date(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def record_event(
        self,
        *,
        event_name: str,
        feature_type: str,
        endpoint: str,
        method: str,
        user: Optional[User],
        status_code: int,
        success: bool,
        latency_ms: Optional[float],
        metadata: Optional[dict] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        tenant_name: Optional[str] = None,
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(
            event_name=event_name,
            feature_type=feature_type,
            endpoint=endpoint,
            method=method,
            user_id=user.id if user else None,
            role=user.role if user else None,
            environment=settings.app_environment,
            tenant_name=tenant_name or (user.tenant_name if user else None),
            success=success,
            status_code=status_code,
            latency_ms=round(latency_ms, 2) if latency_ms is not None else None,
            metadata_json=metadata or {},
            model_name=model_name,
            model_version=model_version,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def _filtered_events(
        self,
        *,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tenant: Optional[str] = None,
        environment: Optional[str] = None,
        feature_type: Optional[str] = None,
    ) -> list[AnalyticsEvent]:
        query = self.db.query(AnalyticsEvent)
        if date_from is not None:
            query = query.filter(AnalyticsEvent.created_at >= _normalize_date(date_from))
        if date_to is not None:
            query = query.filter(AnalyticsEvent.created_at <= _normalize_date(date_to))
        if tenant:
            query = query.filter(AnalyticsEvent.tenant_name == tenant)
        if environment:
            query = query.filter(AnalyticsEvent.environment == environment)
        if feature_type:
            query = query.filter(AnalyticsEvent.feature_type == feature_type)
        return query.all()

    def build_dashboard(
        self,
        *,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tenant: Optional[str] = None,
        environment: Optional[str] = None,
        feature_type: Optional[str] = None,
    ) -> AdminDashboardResponse:
        events = self._filtered_events(
            date_from=date_from,
            date_to=date_to,
            tenant=tenant,
            environment=environment,
            feature_type=feature_type,
        )

        users_query = self.db.query(User)
        if tenant:
            users_query = users_query.filter(User.tenant_name == tenant)
        if date_from is not None:
            users_query = users_query.filter(User.created_at >= _normalize_date(date_from))
        if date_to is not None:
            users_query = users_query.filter(User.created_at <= _normalize_date(date_to))
        users = users_query.all()

        active_user_ids = {event.user_id for event in events if event.user_id}
        feature_counter = Counter(event.feature_type for event in events)
        total_events = sum(feature_counter.values())
        workflow_items = []
        for feature in ["prediction", "forecast", "recommendation"]:
            count = feature_counter.get(feature, 0)
            percentage = (count / total_events * 100) if total_events else 0.0
            workflow_items.append(
                WorkflowSplitItem(
                    feature_type=feature,
                    count=count,
                    percentage=round(percentage, 2),
                )
            )

        latencies = [event.latency_ms for event in events if event.latency_ms is not None]
        sorted_latencies = sorted(latencies)
        p95_index = max(math.ceil(len(sorted_latencies) * 0.95) - 1, 0) if sorted_latencies else 0
        error_events = [event for event in events if not event.success]
        adoption = Counter(event.tenant_name or "unknown" for event in events)

        prediction_records = self.db.query(PredictionRecord).all()
        average_risk = (
            round(mean(record.risk_probability for record in prediction_records), 4)
            if prediction_records else 0.0
        )

        daily_buckets: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "prediction": 0, "forecast": 0, "recommendation": 0}
        )
        for event in events:
            bucket = event.created_at.strftime("%Y-%m-%d")
            daily_buckets[bucket]["total"] += 1
            if event.feature_type in daily_buckets[bucket]:
                daily_buckets[bucket][event.feature_type] += 1

        trends = [
            TrendPoint(
                bucket=bucket,
                total_events=values["total"],
                prediction_events=values["prediction"],
                forecast_events=values["forecast"],
                recommendation_events=values["recommendation"],
            )
            for bucket, values in sorted(daily_buckets.items())
        ]

        return AdminDashboardResponse(
            filters=AdminFilterEcho(
                date_from=date_from,
                date_to=date_to,
                tenant=tenant,
                environment=environment,
                feature_type=feature_type,
            ),
            accounts=AccountsKpi(
                accounts_created=len(users),
                active_users=len(active_user_ids),
            ),
            feature_usage=[
                FeatureUsageMetric(feature_type=name, request_volume=count)
                for name, count in sorted(feature_counter.items())
            ],
            model_usage=ModelUsageMetric(
                prediction_runs=feature_counter.get("prediction", 0),
                forecast_runs=feature_counter.get("forecast", 0),
                average_risk_probability=average_risk,
                model_name=settings.model_name,
                model_version=settings.model_version,
            ),
            workflow_split=workflow_items,
            usage_funnel=UsageFunnel(
                prediction_views=feature_counter.get("prediction", 0),
                forecast_views=feature_counter.get("forecast", 0),
                recommendation_views=feature_counter.get("recommendation", 0),
            ),
            saas_metrics=SaaSMetrics(
                api_calls=total_events,
                per_feature_request_volume=dict(feature_counter),
                adoption_by_tenant=dict(adoption),
            ),
            operations=OperationsSummary(
                avg_latency_ms=round(mean(latencies), 2) if latencies else 0.0,
                p95_latency_ms=round(sorted_latencies[p95_index], 2) if sorted_latencies else 0.0,
                error_rate=round((len(error_events) / total_events) * 100, 2) if total_events else 0.0,
                availability=round((1 - len(error_events) / total_events) * 100, 2) if total_events else 100.0,
                slo_summary={
                    "latency_target_ms": 500,
                    "availability_target_percent": 99.0,
                    "latency_met": (round(sorted_latencies[p95_index], 2) if sorted_latencies else 0.0) <= 500,
                    "availability_met": (round((1 - len(error_events) / total_events) * 100, 2) if total_events else 100.0) >= 99.0,
                },
            ),
            trends=trends,
        )

    def build_metrics(
        self,
        *,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tenant: Optional[str] = None,
        environment: Optional[str] = None,
        feature_type: Optional[str] = None,
    ) -> AdminMetricsResponse:
        dashboard = self.build_dashboard(
            date_from=date_from,
            date_to=date_to,
            tenant=tenant,
            environment=environment,
            feature_type=feature_type,
        )
        return AdminMetricsResponse(
            total_users=dashboard.accounts.accounts_created,
            active_users=dashboard.accounts.active_users,
            avg_response_time_ms=dashboard.operations.avg_latency_ms,
            error_rate=dashboard.operations.error_rate,
        )
