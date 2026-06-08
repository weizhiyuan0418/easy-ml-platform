from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import DatasetRecord, FieldDefinition, ModelRun, Project
from .services import (
    cleanup_orphan_model_artifacts,
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
        self.assertEqual(second.json()["error_code"], "duplicate_field_name")

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
        self.assertEqual(result["training_status"], "completed")

        active_runs = ModelRun.objects.filter(project=self.project, is_active=True)
        recommended_runs = ModelRun.objects.filter(project=self.project, is_recommended=True)
        self.assertEqual(active_runs.count(), 2)
        self.assertEqual(recommended_runs.count(), 2)

        score_run = active_runs.get(target_field__name="score")
        level_run = active_runs.get(target_field__name="level")
        self.assertIn("mae", score_run.metrics)
        self.assertIn("f1_macro", level_run.metrics)

    def test_training_with_insufficient_data_returns_failed_status(self) -> None:
        self.add_standard_fields()
        response = self.client.post(
            "/api/train/",
            data=json.dumps({"project_id": self.project.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["training_status"], "failed")
        self.assertEqual(payload["successful_target_count"], 0)
        self.assertEqual(payload["failed_target_count"], 2)
        self.assertEqual(payload["targets"]["score"]["error_code"], "not_enough_rows")

    def test_sample_project_endpoint_creates_independent_project(self) -> None:
        response = self.client.post("/api/examples/sample-project/")
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()
        project_id = payload["project"]["id"]
        self.assertEqual(payload["record_count"], 12)
        self.assertEqual(Project.objects.get(pk=project_id).fields.count(), 6)
        self.assertEqual(DatasetRecord.objects.filter(project_id=project_id).count(), 12)
        self.assertNotEqual(project_id, self.project.pk)

    def test_csv_template_uses_active_field_names_for_selected_project(self) -> None:
        self.add_standard_fields()
        response = self.client.get(f"/api/export/template/csv/?project_id={self.project.pk}")
        self.assertEqual(response.status_code, 200)
        header = response.content.decode("utf-8-sig").splitlines()[0]
        self.assertEqual(header, "x,kind,flag,when,score,level")

    def test_project_scoped_field_api_keeps_projects_separate(self) -> None:
        other = Project.objects.create(name="另一个项目")
        FieldDefinition.objects.create(project=other, name="other_x", label="Other X", role="input", field_type="number")
        FieldDefinition.objects.create(project=self.project, name="x", label="X", role="input", field_type="number")
        response = self.client.get(f"/api/fields/?project_id={self.project.pk}")
        self.assertEqual(response.status_code, 200)
        names = [field["name"] for field in response.json()["fields"]]
        self.assertEqual(names, ["x"])

    def test_invalid_project_id_returns_stable_error_code(self) -> None:
        response = self.client.get("/api/fields/?project_id=not-a-number")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_code"], "invalid_project_id")

    def test_record_api_supports_pagination_and_full_compat(self) -> None:
        self.add_standard_fields()
        self.add_training_records(count=7)

        full_response = self.client.get(f"/api/records/?project_id={self.project.pk}")
        self.assertEqual(full_response.status_code, 200)
        full_payload = full_response.json()
        self.assertEqual(len(full_payload["records"]), 7)
        self.assertFalse(full_payload["pagination"]["enabled"])

        page_response = self.client.get(f"/api/records/?project_id={self.project.pk}&page=2&page_size=3")
        self.assertEqual(page_response.status_code, 200)
        page_payload = page_response.json()
        self.assertEqual(len(page_payload["records"]), 3)
        self.assertTrue(page_payload["pagination"]["enabled"])
        self.assertEqual(page_payload["pagination"]["total_count"], 7)
        self.assertEqual(page_payload["pagination"]["page"], 2)
        self.assertTrue(page_payload["pagination"]["has_previous"])
        self.assertTrue(page_payload["pagination"]["has_next"])

        invalid_response = self.client.get(f"/api/records/?project_id={self.project.pk}&page=bad&page_size=3")
        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(invalid_response.json()["error_code"], "invalid_pagination")

    def test_dashboard_summary_includes_data_quality(self) -> None:
        self.add_standard_fields()
        DatasetRecord.objects.create(
            project=self.project,
            values={
                "x": 1,
                "kind": "A",
                "flag": True,
                "when": "2026-02-01T00:00:00",
                "score": 3,
                "level": "low",
            },
        )
        DatasetRecord.objects.create(
            project=self.project,
            values={
                "x": 5,
                "kind": "B",
                "flag": False,
                "when": "2026-02-02T00:00:00",
                "score": 9,
            },
        )

        response = self.client.get(f"/api/dashboard/summary/?project_id={self.project.pk}")
        self.assertEqual(response.status_code, 200)
        data_quality = response.json()["data_quality"]
        self.assertEqual(data_quality["missing_field_count"], 1)
        numeric = {item["field"]: item for item in data_quality["numeric_ranges"]}
        self.assertEqual(numeric["x"]["min"], 1)
        self.assertEqual(numeric["x"]["max"], 5)
        categories = {item["field"]: item for item in data_quality["category_uniques"]}
        self.assertEqual(categories["kind"]["unique_count"], 2)

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

    def test_model_activation_requires_model_run_id(self) -> None:
        response = self.client.post(
            "/api/models/activate/",
            data=json.dumps({"project_id": self.project.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_code"], "model_run_id_required")

    def test_successful_retraining_deletes_replaced_model_files(self) -> None:
        self.add_standard_fields()
        self.add_training_records()
        train_project_models(self.project)
        old_runs = list(ModelRun.objects.filter(project=self.project))
        old_paths = [Path(run.model_path) for run in old_runs if run.model_path]
        self.assertTrue(old_paths)

        result = train_project_models(self.project)
        self.assertTrue(result["success"], result)
        self.assertFalse(ModelRun.objects.filter(pk__in=[run.pk for run in old_runs]).exists())
        self.assertTrue(all(not path.exists() for path in old_paths))
        self.assertEqual(ModelRun.objects.filter(project=self.project, is_active=True).count(), 2)

    def test_training_failure_preserves_previous_active_model(self) -> None:
        self.add_standard_fields()
        self.add_training_records()
        train_project_models(self.project)
        active_before = list(ModelRun.objects.filter(project=self.project, is_active=True).values_list("pk", flat=True))
        self.assertEqual(len(active_before), 2)

        DatasetRecord.objects.filter(project=self.project).delete()
        result = train_project_models(self.project)
        self.assertFalse(result["success"])
        self.assertEqual(result["training_status"], "failed")
        active_after = list(ModelRun.objects.filter(project=self.project, is_active=True).values_list("pk", flat=True))
        self.assertEqual(sorted(active_after), sorted(active_before))
        self.assertIsNotNone(result["targets"]["score"]["preserved_active_model"])

    def test_missing_model_file_prediction_returns_stable_error_code(self) -> None:
        self.add_standard_fields()
        self.add_training_records()
        train_project_models(self.project)
        active = ModelRun.objects.filter(project=self.project, is_active=True).first()
        self.assertIsNotNone(active)
        Path(active.model_path).unlink(missing_ok=True)

        response = self.client.post(
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
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_code"], "model_file_missing")

    def test_import_file_errors_return_stable_error_codes(self) -> None:
        self.add_standard_fields()
        empty = SimpleUploadedFile("empty.csv", b"", content_type="text/csv")
        empty_response = self.client.post(
            f"/api/import/preview/?project_id={self.project.pk}",
            data={"file": empty},
        )
        self.assertEqual(empty_response.status_code, 400)
        self.assertEqual(empty_response.json()["error_code"], "empty_upload")

        text = SimpleUploadedFile("data.txt", b"x,score\n1,2\n", content_type="text/plain")
        type_response = self.client.post(
            f"/api/import/preview/?project_id={self.project.pk}",
            data={"file": text},
        )
        self.assertEqual(type_response.status_code, 400)
        self.assertEqual(type_response.json()["error_code"], "unsupported_file_type")

    def test_cleanup_orphan_model_artifacts_dry_run(self) -> None:
        orphan_dir = Path(settings.EASY_ML_MODEL_DIR) / "trained"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        orphan = orphan_dir / "orphan_test.joblib"
        orphan.write_text("orphan", encoding="utf-8")
        try:
            result = cleanup_orphan_model_artifacts(delete=False)
            self.assertIn(str(orphan), result["orphans"])
            self.assertEqual(result["deleted_count"], 0)
            self.assertTrue(orphan.exists())
        finally:
            orphan.unlink(missing_ok=True)

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
