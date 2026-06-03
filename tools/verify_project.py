from __future__ import annotations

import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django  # noqa: E402
from django.core.management import call_command  # noqa: E402


def main() -> None:
    django.setup()

    from mlapp.models import DatasetRecord, FieldDefinition, ModelRun, Project  # noqa: E402
    from mlapp.services import predict, train_project_models  # noqa: E402

    call_command("check", verbosity=0)
    call_command("migrate", interactive=False, verbosity=0)

    project = Project.objects.create(name="verify_project_utf8", description="验证 UTF-8 与训练预测")
    model_paths: list[Path] = []
    try:
        fields = [
            FieldDefinition.objects.create(project=project, name="x1", label="数值输入", role="input", field_type="number", required=True, sort_order=1),
            FieldDefinition.objects.create(project=project, name="kind", label="类别输入", role="input", field_type="category", choices=["A", "B"], sort_order=2),
            FieldDefinition.objects.create(project=project, name="flag", label="布尔输入", role="input", field_type="boolean", sort_order=3),
            FieldDefinition.objects.create(project=project, name="when", label="日期输入", role="input", field_type="datetime", sort_order=4),
            FieldDefinition.objects.create(project=project, name="target", label="数值输出", role="output", field_type="number", required=True, sort_order=5),
        ]
        _ = fields
        for index in range(10):
            DatasetRecord.objects.create(
                project=project,
                values={
                    "x1": float(index),
                    "kind": "A" if index % 2 else "B",
                    "flag": bool(index % 2),
                    "when": f"2026-01-{index + 1:02d}T00:00:00",
                    "target": float(index * 2 + 1),
                },
            )
        result = train_project_models(project)
        if not result.get("success"):
            raise RuntimeError(result)
        active_runs = list(ModelRun.objects.filter(project=project, is_active=True))
        if not active_runs:
            raise RuntimeError("没有自动启用模型")
        for run in ModelRun.objects.filter(project=project):
            if run.model_path:
                model_paths.append(Path(run.model_path))
            if run.metadata_path:
                model_paths.append(Path(run.metadata_path))
        prediction = predict(
            project,
            {"x1": 3, "kind": "A", "flag": True, "when": "2026-01-03T00:00:00"},
        )
        if not prediction.get("success") or "target" not in prediction.get("results", {}):
            raise RuntimeError(f"预测结果异常: {prediction}")
        print("verify_project: OK")
    finally:
        project.delete()
        for path in model_paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    main()
