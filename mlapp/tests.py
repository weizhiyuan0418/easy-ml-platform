from __future__ import annotations

import json
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import DatasetRecord, FieldDefinition, ModelRun, Project
from .services import (
    commit_import,
    preview_import,
    train_project_models,
)


class GenericMlPlatformTests(TestCase):
    def setUp(self) -> None:
        self.project = Project.objects.create(name="测试项目", description="UTF-8 测试")
        self.model_files: list[Path] = []

    def tearDown(self) -> None:
        for run in ModelRun.objects.all():
            for raw_path in [run.model_path, run.metadata_path]:
                if raw_path:
                    try:
                        Path(raw_path).unlink(missing_ok=True)
                    except OSError:
                        pass
        for path in self.model_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def add_standard_fields(self) -> None:
        FieldDefinition.objects.create(
            project=self.project,
            name="x",
            label="数值输入",
            role="input",
            field_type="number",
            required=True,
            sort_order=1,
        )
        FieldDefinition.objects.create(
            project=self.project,
            name="kind",
            label="类别输入",
            role="input",
            field_type="category",
            choices=["A", "B"],
            sort_order=2,
        )
        FieldDefinition.objects.create(
            project=self.project,
            name="flag",
            label="布尔输入",
            role="input",
            field_type="boolean",
            sort_order=3,
        )
        FieldDefinition.objects.create(
            project=self.project,
            name="when",
            label="日期输入",
            role="input",
            field_type="datetime",
            sort_order=4,
        )
        FieldDefinition.objects.create(
            project=self.project,
            name="score",
            label="数值输出",
            role="output",
            field_type="number",
            required=True,
            sort_order=5,
        )
        FieldDefinition.objects.create(
            project=self.project,
            name="level",
            label="类别输出",
            role="output",
            field_type="category",
            choices=["low", "high"],
            required=True,
            sort_order=6,
        )

    def add_training_records(self, count: int = 20) -> None:
        for index in range(count):
            DatasetRecord.objects.create(
                project=self.project,
                values={
                    "x": float(index),
                    "kind": "A" if index % 2 else "B",
                    "flag": bool(index % 2),
                    "when": f"2026-02-{(index % 20) + 1:02d}T00:00:00",
                    "score": float(index * 3 + 2),
                    "level": "high" if index >= count / 2 else "low",
                },
            )

    def test_field_validation_rejects_invalid_and_duplicate_names(self) -> None:
        response = self.client.post(
            "/api/fields/",
            data=json.dumps(
                {
                    "name": "1bad",
                    "label": "非法字段",
                    "role": "input",
                    "field_type": "number",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_code"], "invalid_field_name")

        payload = {
            "name": "valid_name",
            "label": "合法字段",
            "role": "input",
            "field_type": "number",
        }
        first = self.client.post("/api/fields/", data=json.dumps(payload), content_type="application/json")
        second = self.client.post("/api/fields/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)

    def test_api_error_response_keeps_error_and_adds_stable_code(self) -> None:
        upload_response = self.client.post("/api/import/preview/")
        upload_payload = upload_response.json()
        self.assertEqual(upload_response.status_code, 400)
        self.assertIn("error", upload_payload)
        self.assertEqual(upload_payload["error_code"], "upload_required")

        train_response = self.client.post(
            "/api/train/",
            data=json.dumps({"project_id": self.project.pk}),
            content_type="application/json",
        )
        train_payload = train_response.json()
        self.assertEqual(train_response.status_code, 400)
        self.assertIn("error", train_payload)
        self.assertEqual(train_payload["error_code"], "missing_output_fields")

    def test_csv_import_accepts_utf8_sig_and_chinese_headers(self) -> None:
        self.add_standard_fields()
        csv_text = (
            "数值输入,类别输入,布尔输入,日期输入,数值输出,类别输出\n"
            "1,A,true,2026-01-01T00:00:00,3,low\n"
            "2,B,false,2026-01-02T00:00:00,6,high\n"
        )
        uploaded = SimpleUploadedFile(
            "中文数据.csv",
            csv_text.encode("utf-8-sig"),
            content_type="text/csv",
        )
        preview = preview_import(self.project, uploaded)
        self.assertTrue(preview["success"], preview)

        uploaded = SimpleUploadedFile(
            "中文数据.csv",
            csv_text.encode("utf-8-sig"),
            content_type="text/csv",
        )
        result = commit_import(self.project, uploaded)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(DatasetRecord.objects.filter(project=self.project).count(), 2)

    def test_training_selects_active_models_for_regression_and_classification(self) -> None:
        self.add_standard_fields()
        self.add_training_records()
        result = train_project_models(self.project)
        self.assertTrue(result["success"], result)

        active_runs = ModelRun.objects.filter(project=self.project, is_active=True)
        recommended_runs = ModelRun.objects.filter(project=self.project, is_recommended=True)
        self.assertEqual(active_runs.count(), 2)
        self.assertEqual(recommended_runs.count(), 2)

        score_run = active_runs.get(target_field__name="score")
        level_run = active_runs.get(target_field__name="level")
        self.assertIn("mae", score_run.metrics)
        self.assertIn("f1_macro", level_run.metrics)

    def test_manual_model_activation_overrides_active_model(self) -> None:
        self.add_standard_fields()
        self.add_training_records()
        train_project_models(self.project)

        target = FieldDefinition.objects.get(project=self.project, name="score")
        current = ModelRun.objects.get(project=self.project, target_field=target, is_active=True)
        alternative = (
            ModelRun.objects.filter(project=self.project, target_field=target, error_message="")
            .exclude(pk=current.pk)
            .first()
        )
        self.assertIsNotNone(alternative)

        response = self.client.post(
            "/api/models/activate/",
            data=json.dumps({"project_id": self.project.pk, "model_run_id": alternative.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        current.refresh_from_db()
        alternative.refresh_from_db()
        self.assertFalse(current.is_active)
        self.assertTrue(alternative.is_active)

    def test_api_end_to_end_training_and_prediction(self) -> None:
        self.add_standard_fields()
        self.add_training_records()

        train_response = self.client.post(
            "/api/train/",
            data=json.dumps({"project_id": self.project.pk}),
            content_type="application/json",
        )
        self.assertEqual(train_response.status_code, 200, train_response.content)

        predict_response = self.client.post(
            "/api/predict/",
            data=json.dumps(
                {
                    "project_id": self.project.pk,
                    "x": 5,
                    "kind": "A",
                    "flag": True,
                    "when": "2026-02-05T00:00:00",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(predict_response.status_code, 200, predict_response.content)
        payload = predict_response.json()
        self.assertTrue(payload["success"])
        self.assertIn("score", payload["results"])
        self.assertIn("level", payload["results"])
