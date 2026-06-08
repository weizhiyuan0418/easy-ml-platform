from __future__ import annotations

from typing import Any

from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DatasetRecord, FieldDefinition, Project
from .services import (
    UserFacingError,
    activate_model,
    commit_import,
    create_sample_project,
    create_or_update_field,
    dashboard_summary,
    default_project,
    export_csv_response,
    export_csv_template_response,
    model_summary,
    predict,
    preview_import,
    records_payload,
    serialize_field,
    serialize_model_run,
    serialize_project,
    serialize_record,
    train_project_models,
    validate_record_payload,
)


def index(request):
    project = default_project()
    return render(request, "mlapp/index.html", {"project": project})


def _project_from_request(request) -> Project:
    raw = (
        request.query_params.get("project_id")
        if hasattr(request, "query_params")
        else request.GET.get("project_id")
    )
    if not raw and hasattr(request, "data") and isinstance(request.data, dict):
        raw = request.data.get("project_id")
    if raw:
        try:
            project_id = int(raw)
        except (TypeError, ValueError) as exc:
            raise UserFacingError("invalid_project_id", "项目 ID 无效", {"project_id": raw}) from exc
        try:
            return Project.objects.get(pk=project_id)
        except Project.DoesNotExist as exc:
            raise UserFacingError("invalid_project_id", "项目不存在", {"project_id": project_id}) from exc
    return default_project()


def _error_code_for_message(message: str) -> tuple[str | None, dict[str, Any]]:
    if "项目名称不能为空" in message:
        return "project_name_required", {}
    if "请上传文件" in message:
        return "upload_required", {}
    if "为必填" in message:
        return "field_required", {"field": message.split(" 为必填", 1)[0]}
    if "必须是数值" in message or "必须是有限数值" in message:
        return "invalid_number", {"field": message.split(" 必须是", 1)[0]}
    if "必须是布尔值" in message:
        return "invalid_boolean", {"field": message.split(" 必须是", 1)[0]}
    if "必须是合法日期/时间" in message:
        return "invalid_datetime", {"field": message.split(" 必须是", 1)[0]}
    if "必须是候选值之一" in message:
        return "invalid_choice", {"field": message.split(" 必须是", 1)[0]}
    if "字段名不能为空" in message or "字段名只能包含" in message:
        return "invalid_field_name", {}
    if "请先配置至少一个输入字段" in message:
        return "missing_input_fields", {}
    if "请先配置至少一个输出字段" in message:
        return "missing_output_fields", {}
    if "当前项目没有已启用模型" in message:
        return "no_active_model", {}
    if "模型运行不存在" in message:
        return "model_run_not_found", {}
    if "模型文件不存在" in message:
        return "model_file_missing", {}
    if "至少需要" in message and "带目标值的数据" in message:
        return "not_enough_rows", {}
    if "上传文件为空" in message:
        return "empty_upload", {}
    if "仅支持 .csv 或 .xlsx 文件" in message:
        return "unsupported_file_type", {}
    if "读取失败" in message:
        return "import_read_failed", {}
    if "包含未知字段" in message or "包含未知列" in message:
        return "unknown_field", {}
    if "不能启用训练失败的模型" in message:
        return "failed_model_activation", {}
    return None, {}


def _error_response(exc: Exception, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    message = str(exc)
    if isinstance(exc, UserFacingError):
        error_code, error_params = exc.code, exc.params
    else:
        error_code, error_params = _error_code_for_message(message)
    payload: dict[str, Any] = {"success": False, "error": message}
    if error_code:
        payload["error_code"] = error_code
        payload["error_params"] = error_params
    return Response(payload, status=http_status)


class ProjectListView(APIView):
    def get(self, request):
        projects = [serialize_project(project) for project in Project.objects.order_by("name", "id")]
        if not projects:
            projects = [serialize_project(default_project())]
        return Response({"success": True, "projects": projects})

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        try:
            name = str(payload.get("name") or "").strip()
            if not name:
                raise UserFacingError("project_name_required", "项目名称不能为空")
            if Project.objects.filter(name=name).exists():
                raise UserFacingError("duplicate_project_name", f"项目名称已存在: {name}", {"project": name})
            project = Project.objects.create(
                name=name,
                description=str(payload.get("description") or "").strip(),
            )
            return Response({"success": True, "project": serialize_project(project)}, status=status.HTTP_201_CREATED)
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ExampleProjectView(APIView):
    def post(self, request):
        try:
            return Response(create_sample_project(), status=status.HTTP_201_CREATED)
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class DashboardSummaryView(APIView):
    def get(self, request):
        try:
            return Response(dashboard_summary(_project_from_request(request)))
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class FieldCollectionView(APIView):
    def get(self, request):
        try:
            project = _project_from_request(request)
            fields = [serialize_field(field) for field in project.fields.order_by("sort_order", "id")]
            return Response({"success": True, "project": serialize_project(project), "fields": fields})
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)

    def post(self, request):
        try:
            project = _project_from_request(request)
            field = create_or_update_field(project, request.data)
            return Response({"success": True, "field": serialize_field(field)}, status=status.HTTP_201_CREATED)
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class FieldDetailView(APIView):
    def patch(self, request, field_id: int):
        try:
            project = _project_from_request(request)
            field = get_object_or_404(FieldDefinition, project=project, pk=field_id)
            field = create_or_update_field(project, request.data, field=field)
            return Response({"success": True, "field": serialize_field(field)})
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)

    def delete(self, request, field_id: int):
        try:
            project = _project_from_request(request)
            field = get_object_or_404(FieldDefinition, project=project, pk=field_id)
            field.delete()
            return Response({"success": True})
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class RecordCollectionView(APIView):
    def get(self, request):
        try:
            project = _project_from_request(request)
            return Response(
                records_payload(
                    project,
                    page=request.query_params.get("page"),
                    page_size=request.query_params.get("page_size"),
                )
            )
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)

    def post(self, request):
        try:
            project = _project_from_request(request)
            values = validate_record_payload(project, request.data)
            record = DatasetRecord.objects.create(project=project, values=values)
            return Response({"success": True, "record": serialize_record(record)}, status=status.HTTP_201_CREATED)
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class RecordDetailView(APIView):
    def patch(self, request, record_id: int):
        try:
            project = _project_from_request(request)
            record = get_object_or_404(DatasetRecord, project=project, pk=record_id)
            updates = validate_record_payload(project, request.data, partial=True)
            values: dict[str, Any] = dict(record.values)
            values.update(updates)
            record.values = values
            record.save(update_fields=["values", "updated_at"])
            return Response({"success": True, "record": serialize_record(record)})
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)

    def delete(self, request, record_id: int):
        try:
            project = _project_from_request(request)
            record = get_object_or_404(DatasetRecord, project=project, pk=record_id)
            record.delete()
            return Response({"success": True})
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ImportPreviewView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            project = _project_from_request(request)
            uploaded_file = request.FILES.get("file")
            if uploaded_file is None:
                raise UserFacingError("upload_required", "请上传文件")
            return Response(preview_import(project, uploaded_file))
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ImportCommitView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            project = _project_from_request(request)
            uploaded_file = request.FILES.get("file")
            if uploaded_file is None:
                raise UserFacingError("upload_required", "请上传文件")
            return Response(commit_import(project, uploaded_file))
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ExportCsvView(APIView):
    def get(self, request):
        try:
            project = _project_from_request(request)
            return export_csv_response(project)
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ExportCsvTemplateView(APIView):
    def get(self, request):
        try:
            project = _project_from_request(request)
            return export_csv_template_response(project)
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class TrainView(APIView):
    def post(self, request):
        try:
            project = _project_from_request(request)
            target_field_id = None
            if isinstance(request.data, dict) and request.data.get("target_field_id"):
                target_field_id = int(request.data["target_field_id"])
            return Response(train_project_models(project, target_field_id=target_field_id))
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ModelSummaryView(APIView):
    def get(self, request):
        try:
            return Response(model_summary(_project_from_request(request)))
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class ModelActivateView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            project = _project_from_request(request)
            raw_model_run_id = request.data.get("model_run_id")
            if not raw_model_run_id:
                raise UserFacingError("model_run_id_required", "缺少模型运行 ID")
            try:
                model_run_id = int(raw_model_run_id)
            except (TypeError, ValueError) as exc:
                raise UserFacingError("model_run_id_required", "模型运行 ID 无效") from exc
            run = activate_model(project, model_run_id)
            return Response({"success": True, "model": serialize_model_run(run)})
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)


class PredictView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            project = _project_from_request(request)
            payload = request.data if isinstance(request.data, dict) else {}
            return Response(predict(project, payload))
        except Exception as exc:  # noqa: BLE001
            return _error_response(exc)
