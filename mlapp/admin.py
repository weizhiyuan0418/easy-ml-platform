from __future__ import annotations

from django.contrib import admin

from .models import DatasetRecord, FieldDefinition, ModelRun, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at")
    search_fields = ("name",)


@admin.register(FieldDefinition)
class FieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "label", "role", "field_type", "required", "is_active", "sort_order")
    list_filter = ("role", "field_type", "is_active")
    search_fields = ("name", "label")


@admin.register(DatasetRecord)
class DatasetRecordAdmin(admin.ModelAdmin):
    list_display = ("project", "id", "updated_at")
    list_filter = ("project",)


@admin.register(ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "target_field",
        "task_type",
        "candidate_key",
        "is_recommended",
        "is_active",
        "training_sample_count",
        "created_at",
    )
    list_filter = ("task_type", "is_recommended", "is_active")
