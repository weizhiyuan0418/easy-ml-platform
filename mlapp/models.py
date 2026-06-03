from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


FIELD_ROLE_INPUT = "input"
FIELD_ROLE_OUTPUT = "output"
FIELD_ROLE_CHOICES = (
    (FIELD_ROLE_INPUT, "输入"),
    (FIELD_ROLE_OUTPUT, "输出"),
)

FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_CATEGORY = "category"
FIELD_TYPE_BOOLEAN = "boolean"
FIELD_TYPE_DATETIME = "datetime"
FIELD_TYPE_CHOICES = (
    (FIELD_TYPE_NUMBER, "数值"),
    (FIELD_TYPE_CATEGORY, "类别"),
    (FIELD_TYPE_BOOLEAN, "布尔"),
    (FIELD_TYPE_DATETIME, "日期/时间"),
)

TASK_TYPE_REGRESSION = "regression"
TASK_TYPE_CLASSIFICATION = "classification"
TASK_TYPE_CHOICES = (
    (TASK_TYPE_REGRESSION, "回归"),
    (TASK_TYPE_CLASSIFICATION, "分类"),
)


class Project(models.Model):
    name = models.CharField(max_length=160, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class FieldDefinition(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=80)
    label = models.CharField(max_length=160)
    role = models.CharField(max_length=16, choices=FIELD_ROLE_CHOICES)
    field_type = models.CharField(max_length=16, choices=FIELD_TYPE_CHOICES)
    unit = models.CharField(max_length=64, blank=True, default="")
    required = models.BooleanField(default=False)
    choices = models.JSONField(default=list, blank=True)
    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "name"], name="unique_field_name_per_project"),
        ]

    def clean(self) -> None:
        if not self.name.replace("_", "").isalnum() or self.name[0].isdigit():
            raise ValidationError({"name": "字段名只能包含字母、数字、下划线，且不能以数字开头。"})
        if not isinstance(self.choices, list):
            raise ValidationError({"choices": "候选值必须是列表。"})

    def __str__(self) -> str:
        return f"{self.project.name}.{self.name}"


class DatasetRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="records")
    values = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.project.name} #{self.pk}"


class ModelRun(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="model_runs")
    target_field = models.ForeignKey(FieldDefinition, on_delete=models.CASCADE, related_name="model_runs")
    task_type = models.CharField(max_length=24, choices=TASK_TYPE_CHOICES)
    candidate_key = models.CharField(max_length=80)
    candidate_label = models.CharField(max_length=160)
    metrics = models.JSONField(default=dict)
    feature_fields = models.JSONField(default=list)
    model_path = models.TextField()
    metadata_path = models.TextField(blank=True, default="")
    is_recommended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    training_sample_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["target_field__sort_order", "-created_at", "candidate_key"]
        indexes = [
            models.Index(fields=["project", "target_field", "is_active"], name="mlapp_model_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.target_field.name}: {self.candidate_key}"
