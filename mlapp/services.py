from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils.text import slugify
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR

from .models import (
    FIELD_ROLE_INPUT,
    FIELD_ROLE_OUTPUT,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_CATEGORY,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_NUMBER,
    TASK_TYPE_CLASSIFICATION,
    TASK_TYPE_REGRESSION,
    DatasetRecord,
    FieldDefinition,
    ModelRun,
    Project,
)


FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MISSING_VALUES = {None, ""}
MIN_TRAINING_ROWS = 3


class UserFacingError(ValueError):
    def __init__(self, code: str, message: str, params: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.params = params or {}


@dataclass(frozen=True)
class Candidate:
    key: str
    label: str
    build_pipeline: Any
    needs_scaled_numeric: bool = False


@dataclass
class ModelArtifact:
    pipeline: Pipeline
    project_id: int
    target_field: str
    target_label: str
    target_type: str
    task_type: str
    input_fields: list[dict[str, Any]]
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    candidate_key: str
    candidate_label: str


def _is_missing(value: Any) -> bool:
    if value in MISSING_VALUES:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def default_project() -> Project:
    project, _created = Project.objects.get_or_create(
        name="Default Project",
        defaults={"description": "Default Easy ML Platform project"},
    )
    return project


def _unique_project_name(base_name: str) -> str:
    existing = set(Project.objects.filter(name__startswith=base_name).values_list("name", flat=True))
    if base_name not in existing:
        return base_name
    suffix = 2
    while f"{base_name} {suffix}" in existing:
        suffix += 1
    return f"{base_name} {suffix}"


def create_sample_project() -> dict[str, Any]:
    sample_fields = [
        {"name": "x", "label": "Input X", "role": FIELD_ROLE_INPUT, "field_type": FIELD_TYPE_NUMBER, "required": True, "sort_order": 1},
        {"name": "kind", "label": "Category Kind", "role": FIELD_ROLE_INPUT, "field_type": FIELD_TYPE_CATEGORY, "choices": ["A", "B"], "sort_order": 2},
        {"name": "flag", "label": "Flag", "role": FIELD_ROLE_INPUT, "field_type": FIELD_TYPE_BOOLEAN, "sort_order": 3},
        {"name": "when", "label": "Date", "role": FIELD_ROLE_INPUT, "field_type": FIELD_TYPE_DATETIME, "sort_order": 4},
        {"name": "score", "label": "Score", "role": FIELD_ROLE_OUTPUT, "field_type": FIELD_TYPE_NUMBER, "required": True, "sort_order": 5},
        {"name": "level", "label": "Level", "role": FIELD_ROLE_OUTPUT, "field_type": FIELD_TYPE_CATEGORY, "choices": ["low", "high"], "required": True, "sort_order": 6},
    ]
    sample_rows = [
        {"x": 0, "kind": "A", "flag": True, "when": "2026-01-01T00:00:00", "score": 2, "level": "low"},
        {"x": 1, "kind": "B", "flag": False, "when": "2026-01-02T00:00:00", "score": 5, "level": "low"},
        {"x": 2, "kind": "A", "flag": True, "when": "2026-01-03T00:00:00", "score": 8, "level": "low"},
        {"x": 3, "kind": "B", "flag": False, "when": "2026-01-04T00:00:00", "score": 11, "level": "low"},
        {"x": 4, "kind": "A", "flag": True, "when": "2026-01-05T00:00:00", "score": 14, "level": "low"},
        {"x": 5, "kind": "B", "flag": False, "when": "2026-01-06T00:00:00", "score": 17, "level": "low"},
        {"x": 6, "kind": "A", "flag": True, "when": "2026-01-07T00:00:00", "score": 20, "level": "high"},
        {"x": 7, "kind": "B", "flag": False, "when": "2026-01-08T00:00:00", "score": 23, "level": "high"},
        {"x": 8, "kind": "A", "flag": True, "when": "2026-01-09T00:00:00", "score": 26, "level": "high"},
        {"x": 9, "kind": "B", "flag": False, "when": "2026-01-10T00:00:00", "score": 29, "level": "high"},
        {"x": 10, "kind": "A", "flag": True, "when": "2026-01-11T00:00:00", "score": 32, "level": "high"},
        {"x": 11, "kind": "B", "flag": False, "when": "2026-01-12T00:00:00", "score": 35, "level": "high"},
    ]
    with transaction.atomic():
        project = Project.objects.create(
            name=_unique_project_name("Sample Project"),
            description="Built-in sample project for trying Easy ML Platform.",
        )
        fields = []
        for field in sample_fields:
            field_payload = dict(field)
            field_payload.setdefault("choices", [])
            fields.append(FieldDefinition(project=project, **field_payload))
        FieldDefinition.objects.bulk_create(fields)
        created_fields = list(project.fields.order_by("sort_order", "id"))
        DatasetRecord.objects.bulk_create(
            DatasetRecord(project=project, values=validate_record_payload(project, row))
            for row in sample_rows
        )
    return {
        "success": True,
        "project": serialize_project(project),
        "fields": [serialize_field(field) for field in created_fields],
        "record_count": len(sample_rows),
    }


def normalize_field_name(name: Any) -> str:
    text = str(name or "").strip()
    if not text:
        raise UserFacingError("invalid_field_name", "字段名不能为空")
    if not FIELD_NAME_PATTERN.match(text):
        raise UserFacingError("invalid_field_name", "字段名只能包含字母、数字、下划线，且不能以字母或下划线开头")
    return text


def serialize_project(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def serialize_field(field: FieldDefinition) -> dict[str, Any]:
    return {
        "id": field.id,
        "project": field.project_id,
        "name": field.name,
        "label": field.label,
        "role": field.role,
        "field_type": field.field_type,
        "unit": field.unit,
        "required": field.required,
        "choices": field.choices,
        "sort_order": field.sort_order,
        "is_active": field.is_active,
    }


def serialize_record(record: DatasetRecord, fields: list[FieldDefinition] | None = None) -> dict[str, Any]:
    fields = fields or list(record.project.fields.order_by("sort_order", "id"))
    return {
        "id": record.id,
        "project": record.project_id,
        "values": {field.name: record.values.get(field.name) for field in fields},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def serialize_model_run(run: ModelRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "project": run.project_id,
        "target_field_id": run.target_field_id,
        "target_field": run.target_field.name,
        "target_label": run.target_field.label,
        "task_type": run.task_type,
        "candidate_key": run.candidate_key,
        "candidate_label": run.candidate_label,
        "metrics": run.metrics,
        "feature_fields": run.feature_fields,
        "model_path": run.model_path,
        "metadata_path": run.metadata_path,
        "is_recommended": run.is_recommended,
        "is_active": run.is_active,
        "training_sample_count": run.training_sample_count,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def normalize_value(field: FieldDefinition, value: Any, *, required_override: bool | None = None) -> Any:
    required = field.required if required_override is None else required_override
    if _is_missing(value):
        if required:
            raise UserFacingError("field_required", f"{field.label} 为必填", {"field": field.label})
        return None

    if field.field_type == FIELD_TYPE_NUMBER:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise UserFacingError("invalid_number", f"{field.label} 必须是数值", {"field": field.label}) from exc
        if not math.isfinite(number):
            raise UserFacingError("invalid_number", f"{field.label} 必须是有限数值", {"field": field.label})
        return number

    if field.field_type == FIELD_TYPE_BOOLEAN:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "是", "对"}:
            return True
        if text in {"0", "false", "no", "n", "否", "不"}:
            return False
        raise UserFacingError("invalid_boolean", f"{field.label} 必须是布尔值", {"field": field.label})

    if field.field_type == FIELD_TYPE_DATETIME:
        try:
            parsed = pd.to_datetime(value, errors="raise")
        except Exception as exc:
            raise UserFacingError("invalid_datetime", f"{field.label} 必须是合法日期/时间", {"field": field.label}) from exc
        if pd.isna(parsed):
            raise UserFacingError("invalid_datetime", f"{field.label} 必须是合法日期/时间", {"field": field.label})
        return parsed.isoformat()

    text = str(value).strip()
    choices = [str(item) for item in field.choices or [] if str(item).strip()]
    if choices and text not in choices:
        raise UserFacingError("invalid_choice", f"{field.label} 必须是候选值之一: {choices}", {"field": field.label})
    return text


def validate_record_payload(project: Project, payload: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise UserFacingError("invalid_payload", "数据必须是 JSON 对象")
    fields = list(project.fields.filter(is_active=True).order_by("sort_order", "id"))
    field_map = {field.name: field for field in fields}
    unknown = sorted([key for key in payload.keys() if key not in field_map])
    if unknown:
        raise UserFacingError("unknown_field", f"包含未知字段: {unknown}", {"fields": unknown})

    normalized: dict[str, Any] = {}
    for field in fields:
        if partial and field.name not in payload:
            continue
        normalized[field.name] = normalize_value(field, payload.get(field.name))
    return normalized


def create_or_update_field(project: Project, payload: dict[str, Any], *, field: FieldDefinition | None = None) -> FieldDefinition:
    if not isinstance(payload, dict):
        raise UserFacingError("invalid_payload", "字段配置必须是 JSON 对象")

    target = field or FieldDefinition(project=project)
    editable = {
        "name",
        "label",
        "role",
        "field_type",
        "unit",
        "required",
        "choices",
        "sort_order",
        "is_active",
    }
    unknown = sorted([key for key in payload.keys() if key not in editable])
    if unknown:
        raise UserFacingError("unknown_field", f"包含未知字段: {unknown}", {"fields": unknown})

    if field is None or "name" in payload:
        target.name = normalize_field_name(payload.get("name"))
    if field is None or "label" in payload:
        target.label = str(payload.get("label") or target.name).strip() or target.name
    for attr in ["role", "field_type", "unit", "required", "choices", "sort_order", "is_active"]:
        if attr in payload:
            setattr(target, attr, payload[attr])

    duplicate = FieldDefinition.objects.filter(project=project, name=target.name)
    if target.pk:
        duplicate = duplicate.exclude(pk=target.pk)
    if duplicate.exists():
        raise UserFacingError("duplicate_field_name", f"字段名已存在: {target.name}", {"field": target.name})

    try:
        target.full_clean()
    except ValidationError as exc:
        raise UserFacingError(
            "field_validation_failed",
            str(exc.message_dict if hasattr(exc, "message_dict") else exc.messages),
        ) from exc
    target.save()
    return target


def _read_uploaded_table(uploaded_file: Any) -> tuple[list[str], list[dict[str, Any]], str | None]:
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    raw = uploaded_file.read()
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    if not raw:
        return [], [], "上传文件为空"

    name = str(getattr(uploaded_file, "name", "") or "").lower()
    dataframe = None
    last_error: Exception | None = None
    if name.endswith(".csv"):
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
            try:
                dataframe = pd.read_csv(BytesIO(raw), encoding=encoding, dtype=object)
                break
            except Exception as exc:
                last_error = exc
        if dataframe is None:
            return [], [], f"CSV 读取失败: {last_error}"
    elif name.endswith(".xlsx"):
        try:
            dataframe = pd.read_excel(BytesIO(raw), dtype=object)
        except Exception as exc:
            return [], [], f"Excel 读取失败: {exc}"
    else:
        return [], [], "仅支持 .csv 或 .xlsx 文件"

    headers = [str(column).strip() for column in dataframe.columns.tolist()]
    dataframe.columns = headers
    rows: list[dict[str, Any]] = []
    for index, row in dataframe.iterrows():
        payload = {}
        for header in headers:
            value = row.get(header)
            payload[header] = "" if _is_missing(value) else value
        if all(_is_missing(value) for value in payload.values()):
            continue
        rows.append({"line": int(index) + 2, "payload": payload})
    return headers, rows, None


def preview_import(project: Project, uploaded_file: Any) -> dict[str, Any]:
    headers, rows, read_error = _read_uploaded_table(uploaded_file)
    if read_error:
        raise ValueError(read_error)
    fields = list(project.fields.filter(is_active=True).order_by("sort_order", "id"))
    header_map = {field.name: field.name for field in fields}
    header_map.update({field.label: field.name for field in fields})
    expected = [field.name for field in fields]
    mapped_headers = [header_map.get(header) for header in headers]
    unknown_headers = sorted([header for header in headers if header not in header_map])
    duplicate_headers = sorted(
        {
            header
            for header in mapped_headers
            if header is not None and mapped_headers.count(header) > 1
        }
    )
    missing_headers = sorted([field.name for field in fields if field.required and field.name not in mapped_headers])
    errors: list[dict[str, Any]] = []
    if unknown_headers:
        errors.append({"line": None, "error": f"包含未知列: {unknown_headers}"})
    if duplicate_headers:
        errors.append({"line": None, "error": f"存在重复映射列: {duplicate_headers}"})
    if missing_headers:
        errors.append({"line": None, "error": f"缺少必填列: {missing_headers}"})

    valid_payloads = []
    if not errors:
        for row in rows:
            payload = {
                header_map[key]: value
                for key, value in row["payload"].items()
                if key in header_map and header_map[key] in expected
            }
            try:
                valid_payloads.append(validate_record_payload(project, payload))
            except ValueError as exc:
                errors.append({"line": row["line"], "error": str(exc)})

    return {
        "success": len(errors) == 0,
        "headers": headers,
        "mapped_headers": [
            {"source": header, "field": header_map.get(header)}
            for header in headers
            if header in header_map
        ],
        "unknown_headers": unknown_headers,
        "duplicate_headers": duplicate_headers,
        "missing_headers": missing_headers,
        "row_count": len(rows),
        "valid_count": len(valid_payloads),
        "error_count": len(errors),
        "errors": errors,
    }


def commit_import(project: Project, uploaded_file: Any) -> dict[str, Any]:
    preview = preview_import(project, uploaded_file)
    if not preview["success"]:
        return preview

    _headers, rows, _read_error = _read_uploaded_table(uploaded_file)
    fields = list(project.fields.filter(is_active=True).order_by("sort_order", "id"))
    header_map = {field.name: field.name for field in fields}
    header_map.update({field.label: field.name for field in fields})
    created: list[DatasetRecord] = []
    with transaction.atomic():
        for row in rows:
            payload = {
                header_map[key]: value
                for key, value in row["payload"].items()
                if key in header_map
            }
            values = validate_record_payload(project, payload)
            created.append(DatasetRecord.objects.create(project=project, values=values))
    return {
        "success": True,
        "imported_count": len(created),
        "record_ids": [record.id for record in created],
    }


def export_csv_response(project: Project) -> HttpResponse:
    fields = list(project.fields.filter(is_active=True).order_by("sort_order", "id"))
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[field.name for field in fields])
    writer.writeheader()
    for record in project.records.order_by("id"):
        writer.writerow({field.name: record.values.get(field.name) for field in fields})
    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8-sig")
    filename = f"{slugify(project.name) or 'dataset'}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def export_csv_template_response(project: Project) -> HttpResponse:
    fields = list(project.fields.filter(is_active=True).order_by("sort_order", "id"))
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[field.name for field in fields])
    writer.writeheader()
    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8-sig")
    filename = f"{slugify(project.name) or 'dataset'}_template.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def output_task_type(field: FieldDefinition) -> str:
    if field.field_type in {FIELD_TYPE_CATEGORY, FIELD_TYPE_BOOLEAN}:
        return TASK_TYPE_CLASSIFICATION
    return TASK_TYPE_REGRESSION


def _parse_datetime_parts(value: Any) -> dict[str, float | None]:
    if _is_missing(value):
        return {"timestamp": None, "year": None, "month": None, "day": None}
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return {"timestamp": None, "year": None, "month": None, "day": None}
    py_dt = parsed.to_pydatetime()
    if py_dt.tzinfo is None:
        py_dt = py_dt.replace(tzinfo=timezone.utc)
    return {
        "timestamp": float(py_dt.timestamp()),
        "year": float(py_dt.year),
        "month": float(py_dt.month),
        "day": float(py_dt.day),
    }


def build_feature_row(input_fields: list[FieldDefinition], values: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for field in input_fields:
        value = values.get(field.name)
        if field.field_type == FIELD_TYPE_NUMBER:
            row[field.name] = None if _is_missing(value) else float(value)
        elif field.field_type == FIELD_TYPE_BOOLEAN:
            if _is_missing(value):
                row[field.name] = None
            else:
                row[field.name] = 1 if bool(value) else 0
        elif field.field_type == FIELD_TYPE_DATETIME:
            parts = _parse_datetime_parts(value)
            row[f"{field.name}__timestamp"] = parts["timestamp"]
            row[f"{field.name}__year"] = parts["year"]
            row[f"{field.name}__month"] = parts["month"]
            row[f"{field.name}__day"] = parts["day"]
        else:
            row[field.name] = None if _is_missing(value) else str(value)
    return row


def _target_value(field: FieldDefinition, value: Any) -> Any:
    if _is_missing(value):
        return None
    if field.field_type == FIELD_TYPE_BOOLEAN:
        return "true" if bool(value) else "false"
    if field.field_type == FIELD_TYPE_DATETIME:
        return _parse_datetime_parts(value)["timestamp"]
    if field.field_type == FIELD_TYPE_NUMBER:
        return float(value)
    return str(value)


def prepare_training_frame(project: Project, target_field: FieldDefinition) -> tuple[pd.DataFrame, pd.Series, list[str], list[str], list[str]]:
    input_fields = list(
        project.fields.filter(role=FIELD_ROLE_INPUT, is_active=True).order_by("sort_order", "id")
    )
    if not input_fields:
        raise UserFacingError("missing_input_fields", "请先配置至少一个输入字段")

    rows: list[dict[str, Any]] = []
    targets: list[Any] = []
    for record in project.records.order_by("id"):
        target = _target_value(target_field, record.values.get(target_field.name))
        if target is None:
            continue
        rows.append(build_feature_row(input_fields, record.values))
        targets.append(target)

    if len(rows) < MIN_TRAINING_ROWS:
        raise UserFacingError(
            "not_enough_rows",
            f"{target_field.label} 至少需要 {MIN_TRAINING_ROWS} 条带目标值的数据",
            {"field": target_field.label, "min_rows": MIN_TRAINING_ROWS},
        )

    X = pd.DataFrame(rows)
    y = pd.Series(targets, name=target_field.name)
    numeric_features = [
        column
        for column in X.columns
        if column.endswith("__timestamp")
        or column.endswith("__year")
        or column.endswith("__month")
        or column.endswith("__day")
        or next((field.field_type for field in input_fields if field.name == column), None)
        in {FIELD_TYPE_NUMBER, FIELD_TYPE_BOOLEAN}
    ]
    categorical_features = [
        column
        for column in X.columns
        if column not in numeric_features
    ]
    return X, y, list(X.columns), numeric_features, categorical_features


def _one_hot_encoder() -> OneHotEncoder:
    return OneHotEncoder(handle_unknown="ignore", sparse_output=False)


def build_preprocessor(numeric_features: list[str], categorical_features: list[str], *, scale_numeric: bool = False) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    transformers: list[tuple[str, Any, list[str]]] = []
    if numeric_features:
        transformers.append(("num", Pipeline(numeric_steps), numeric_features))
    if categorical_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", _one_hot_encoder()),
                    ]
                ),
                categorical_features,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop")


def _build_pipeline(model: Any, numeric_features: list[str], categorical_features: list[str], *, scale_numeric: bool = False) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", build_preprocessor(numeric_features, categorical_features, scale_numeric=scale_numeric)),
            ("model", model),
        ]
    )


def regression_candidates(numeric_features: list[str], categorical_features: list[str]) -> list[Candidate]:
    return [
        Candidate("ridge", "Ridge", lambda: _build_pipeline(Ridge(alpha=1.0), numeric_features, categorical_features, scale_numeric=True)),
        Candidate(
            "random_forest",
            "RandomForestRegressor",
            lambda: _build_pipeline(RandomForestRegressor(n_estimators=160, random_state=42), numeric_features, categorical_features),
        ),
        Candidate(
            "extra_trees",
            "ExtraTreesRegressor",
            lambda: _build_pipeline(ExtraTreesRegressor(n_estimators=160, random_state=42), numeric_features, categorical_features),
        ),
        Candidate(
            "gradient_boosting",
            "GradientBoostingRegressor",
            lambda: _build_pipeline(GradientBoostingRegressor(random_state=42), numeric_features, categorical_features),
        ),
        Candidate("svr_rbf", "SVR RBF", lambda: _build_pipeline(SVR(kernel="rbf"), numeric_features, categorical_features, scale_numeric=True)),
    ]


def classification_candidates(numeric_features: list[str], categorical_features: list[str]) -> list[Candidate]:
    return [
        Candidate(
            "logistic_regression",
            "LogisticRegression",
            lambda: _build_pipeline(
                LogisticRegression(max_iter=1000, class_weight="balanced"),
                numeric_features,
                categorical_features,
                scale_numeric=True,
            ),
        ),
        Candidate(
            "random_forest",
            "RandomForestClassifier",
            lambda: _build_pipeline(RandomForestClassifier(n_estimators=160, random_state=42, class_weight="balanced"), numeric_features, categorical_features),
        ),
        Candidate(
            "extra_trees",
            "ExtraTreesClassifier",
            lambda: _build_pipeline(ExtraTreesClassifier(n_estimators=160, random_state=42, class_weight="balanced"), numeric_features, categorical_features),
        ),
        Candidate(
            "gradient_boosting",
            "GradientBoostingClassifier",
            lambda: _build_pipeline(GradientBoostingClassifier(random_state=42), numeric_features, categorical_features),
        ),
        Candidate(
            "svc_rbf",
            "SVC RBF",
            lambda: _build_pipeline(SVC(kernel="rbf", class_weight="balanced", probability=True), numeric_features, categorical_features, scale_numeric=True),
        ),
    ]


def _safe_regression_metrics(y_true: pd.Series, y_pred: Any) -> dict[str, Any]:
    mse = mean_squared_error(y_true, y_pred)
    try:
        r2 = r2_score(y_true, y_pred)
    except Exception:
        r2 = None
    if r2 is not None and not math.isfinite(float(r2)):
        r2 = None
    return {
        "r2": None if r2 is None else round(float(r2), 6),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 6),
        "rmse": round(float(math.sqrt(mse)), 6),
    }


def _safe_classification_metrics(y_true: pd.Series, y_pred: Any) -> dict[str, Any]:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 6),
    }


def _model_storage_paths(project: Project, target_field: FieldDefinition, candidate_key: str) -> tuple[Path, Path]:
    safe_project = slugify(project.name) or f"project_{project.id}"
    stem = f"{safe_project}_{target_field.name}_{candidate_key}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    model_path = Path(settings.EASY_ML_MODEL_DIR) / "trained" / f"{stem}.joblib"
    meta_path = Path(settings.EASY_ML_MODEL_DIR) / "metadata" / f"{stem}.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    return model_path, meta_path


def _sort_key_for_run(task_type: str, run: ModelRun) -> tuple[int, float]:
    if run.error_message:
        return (1, 0.0)
    if task_type == TASK_TYPE_REGRESSION:
        mae = run.metrics.get("mae")
        return (0, float(mae) if mae is not None else 999999999.0)
    f1 = run.metrics.get("f1_macro")
    return (0, -float(f1) if f1 is not None else 999999999.0)


def train_project_models(project: Project, *, target_field_id: int | None = None) -> dict[str, Any]:
    targets = project.fields.filter(role=FIELD_ROLE_OUTPUT, is_active=True).order_by("sort_order", "id")
    if target_field_id is not None:
        targets = targets.filter(id=target_field_id)
    target_list = list(targets)
    if not target_list:
        raise UserFacingError("missing_output_fields", "请先配置至少一个输出字段")

    payload: dict[str, Any] = {"success": True, "training_status": "completed", "targets": {}}
    for target_field in target_list:
        task_type = output_task_type(target_field)
        runs: list[ModelRun] = []
        try:
            X, y, feature_columns, numeric_features, categorical_features = prepare_training_frame(project, target_field)
            test_size = max(1, int(round(len(X) * 0.2)))
            if task_type == TASK_TYPE_CLASSIFICATION:
                class_counts = y.value_counts()
                if y.nunique() > 1 and class_counts.min() >= 2:
                    test_size = max(test_size, int(y.nunique()))
                    stratify = y
                else:
                    stratify = None
            else:
                stratify = None
            test_size = min(test_size, len(X) - 1)
            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=test_size,
                random_state=42,
                stratify=stratify,
            )
            candidates = (
                regression_candidates(numeric_features, categorical_features)
                if task_type == TASK_TYPE_REGRESSION
                else classification_candidates(numeric_features, categorical_features)
            )
            input_fields = list(project.fields.filter(role=FIELD_ROLE_INPUT, is_active=True).order_by("sort_order", "id"))
            input_meta = [serialize_field(field) for field in input_fields]

            with transaction.atomic():
                ModelRun.objects.filter(project=project, target_field=target_field).update(
                    is_recommended=False,
                    is_active=False,
                )
                for candidate in candidates:
                    try:
                        split_pipeline = candidate.build_pipeline()
                        split_pipeline.fit(X_train, y_train)
                        predictions = split_pipeline.predict(X_test)
                        metrics = (
                            _safe_regression_metrics(y_test, predictions)
                            if task_type == TASK_TYPE_REGRESSION
                            else _safe_classification_metrics(y_test, predictions)
                        )
                        final_pipeline = candidate.build_pipeline()
                        final_pipeline.fit(X, y)
                        model_path, meta_path = _model_storage_paths(project, target_field, candidate.key)
                        artifact = ModelArtifact(
                            pipeline=final_pipeline,
                            project_id=project.id,
                            target_field=target_field.name,
                            target_label=target_field.label,
                            target_type=target_field.field_type,
                            task_type=task_type,
                            input_fields=input_meta,
                            feature_columns=feature_columns,
                            numeric_features=numeric_features,
                            categorical_features=categorical_features,
                            candidate_key=candidate.key,
                            candidate_label=candidate.label,
                        )
                        joblib.dump(artifact, model_path)
                        metadata = {
                            "project": serialize_project(project),
                            "target_field": serialize_field(target_field),
                            "task_type": task_type,
                            "candidate_key": candidate.key,
                            "candidate_label": candidate.label,
                            "metrics": metrics,
                            "feature_fields": feature_columns,
                            "numeric_features": numeric_features,
                            "categorical_features": categorical_features,
                            "training_sample_count": int(len(X)),
                            "train_size": int(len(X_train)),
                            "test_size": int(len(X_test)),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
                        run = ModelRun.objects.create(
                            project=project,
                            target_field=target_field,
                            task_type=task_type,
                            candidate_key=candidate.key,
                            candidate_label=candidate.label,
                            metrics=metrics,
                            feature_fields=feature_columns,
                            model_path=str(model_path),
                            metadata_path=str(meta_path),
                            training_sample_count=len(X),
                        )
                    except Exception as exc:  # noqa: BLE001
                        run = ModelRun.objects.create(
                            project=project,
                            target_field=target_field,
                            task_type=task_type,
                            candidate_key=candidate.key,
                            candidate_label=candidate.label,
                            metrics={},
                            feature_fields=feature_columns,
                            model_path="",
                            training_sample_count=len(X),
                            error_message=str(exc),
                        )
                    runs.append(run)

                successful = [run for run in runs if not run.error_message]
                if successful:
                    best = sorted(successful, key=lambda run: _sort_key_for_run(task_type, run))[0]
                    best.is_recommended = True
                    best.is_active = True
                    best.save(update_fields=["is_recommended", "is_active"])

            payload["targets"][target_field.name] = {
                "success": bool([run for run in runs if not run.error_message]),
                "task_type": task_type,
                "runs": [serialize_model_run(ModelRun.objects.get(pk=run.pk)) for run in runs],
            }
        except Exception as exc:  # noqa: BLE001
            error_payload: dict[str, Any] = {
                "success": False,
                "task_type": task_type,
                "error": str(exc),
                "runs": [],
            }
            if isinstance(exc, UserFacingError):
                error_payload["error_code"] = exc.code
                error_payload["error_params"] = exc.params
            payload["targets"][target_field.name] = error_payload
    successful_count = sum(1 for target in payload["targets"].values() if target.get("success"))
    failed_count = len(payload["targets"]) - successful_count
    payload["successful_target_count"] = successful_count
    payload["failed_target_count"] = failed_count
    if successful_count == 0:
        payload["success"] = False
        payload["training_status"] = "failed"
    elif failed_count:
        payload["training_status"] = "partial"
    return payload


def activate_model(project: Project, model_run_id: int) -> ModelRun:
    run = ModelRun.objects.select_related("target_field").get(project=project, pk=model_run_id)
    if run.error_message or not run.model_path:
        raise UserFacingError("failed_model_activation", "不能启用训练失败的模型")
    ModelRun.objects.filter(project=project, target_field=run.target_field).update(is_active=False)
    run.is_active = True
    run.save(update_fields=["is_active"])
    return run


def model_summary(project: Project) -> dict[str, Any]:
    targets = list(project.fields.filter(role=FIELD_ROLE_OUTPUT, is_active=True).order_by("sort_order", "id"))
    result: dict[str, Any] = {"success": True, "targets": []}
    for target in targets:
        runs = list(ModelRun.objects.filter(project=project, target_field=target).select_related("target_field"))
        result["targets"].append(
            {
                "target": serialize_field(target),
                "task_type": output_task_type(target),
                "active_model": next((serialize_model_run(run) for run in runs if run.is_active), None),
                "recommended_model": next((serialize_model_run(run) for run in runs if run.is_recommended), None),
                "runs": [serialize_model_run(run) for run in runs],
            }
        )
    return result


def _prediction_to_output(artifact: ModelArtifact, prediction: Any) -> Any:
    if artifact.task_type == TASK_TYPE_CLASSIFICATION:
        if artifact.target_type == FIELD_TYPE_BOOLEAN:
            return str(prediction).lower() in {"true", "1", "yes"}
        return str(prediction)
    value = float(prediction)
    if artifact.target_type == FIELD_TYPE_DATETIME:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    return value


def predict(project: Project, payload: dict[str, Any]) -> dict[str, Any]:
    input_fields = list(project.fields.filter(role=FIELD_ROLE_INPUT, is_active=True).order_by("sort_order", "id"))
    input_values = {}
    for field in input_fields:
        input_values[field.name] = normalize_value(field, payload.get(field.name), required_override=True)

    active_runs = list(
        ModelRun.objects.filter(project=project, is_active=True)
        .select_related("target_field")
        .order_by("target_field__sort_order", "id")
    )
    if not active_runs:
        raise UserFacingError("no_active_model", "当前项目没有已启用模型，请先训练或启用模型")

    results = {}
    for run in active_runs:
        artifact: ModelArtifact = joblib.load(run.model_path)
        feature_row = build_feature_row(input_fields, input_values)
        X = pd.DataFrame([feature_row])
        X = X.reindex(columns=artifact.feature_columns)
        prediction_value = artifact.pipeline.predict(X)[0]
        results[run.target_field.name] = {
            "target_label": run.target_field.label,
            "task_type": run.task_type,
            "prediction": _prediction_to_output(artifact, prediction_value),
            "model": serialize_model_run(run),
            "features_used": input_values,
        }
    return {"success": True, "results": results}


def dashboard_summary(project: Project) -> dict[str, Any]:
    fields = list(project.fields.filter(is_active=True).order_by("sort_order", "id"))
    input_count = sum(1 for field in fields if field.role == FIELD_ROLE_INPUT)
    output_count = sum(1 for field in fields if field.role == FIELD_ROLE_OUTPUT)
    total_records = project.records.count()
    missingness = []
    for field in fields:
        present = 0
        for record in project.records.all():
            if not _is_missing(record.values.get(field.name)):
                present += 1
        missing = max(total_records - present, 0)
        missingness.append(
            {
                "field": field.name,
                "label": field.label,
                "role": field.role,
                "present_count": present,
                "missing_count": missing,
                "missing_ratio": round(missing / total_records, 4) if total_records else 0.0,
            }
        )
    return {
        "success": True,
        "project": serialize_project(project),
        "totals": {
            "field_count": len(fields),
            "input_count": input_count,
            "output_count": output_count,
            "record_count": total_records,
            "model_run_count": project.model_runs.count(),
            "active_model_count": project.model_runs.filter(is_active=True).count(),
        },
        "missingness": missingness,
    }
