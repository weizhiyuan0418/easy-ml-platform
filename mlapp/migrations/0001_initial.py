# Generated manually for Easy ML Platform.
from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.CreateModel(
            name="DatasetRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("values", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="records", to="mlapp.project"),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="FieldDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("label", models.CharField(max_length=160)),
                ("role", models.CharField(choices=[("input", "输入"), ("output", "输出")], max_length=16)),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("number", "数值"),
                            ("category", "类别"),
                            ("boolean", "布尔"),
                            ("datetime", "日期/时间"),
                        ],
                        max_length=16,
                    ),
                ),
                ("unit", models.CharField(blank=True, default="", max_length=64)),
                ("required", models.BooleanField(default=False)),
                ("choices", models.JSONField(blank=True, default=list)),
                ("sort_order", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="mlapp.project"),
                ),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ModelRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_type", models.CharField(choices=[("regression", "回归"), ("classification", "分类")], max_length=24)),
                ("candidate_key", models.CharField(max_length=80)),
                ("candidate_label", models.CharField(max_length=160)),
                ("metrics", models.JSONField(default=dict)),
                ("feature_fields", models.JSONField(default=list)),
                ("model_path", models.TextField()),
                ("metadata_path", models.TextField(blank=True, default="")),
                ("is_recommended", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=False)),
                ("training_sample_count", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="model_runs", to="mlapp.project"),
                ),
                (
                    "target_field",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="model_runs", to="mlapp.fielddefinition"),
                ),
            ],
            options={"ordering": ["target_field__sort_order", "-created_at", "candidate_key"]},
        ),
        migrations.AddConstraint(
            model_name="fielddefinition",
            constraint=models.UniqueConstraint(fields=("project", "name"), name="unique_field_name_per_project"),
        ),
        migrations.AddIndex(
            model_name="modelrun",
            index=models.Index(fields=["project", "target_field", "is_active"], name="mlapp_model_active_idx"),
        ),
    ]
