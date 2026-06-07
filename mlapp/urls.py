from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("api/projects/", views.ProjectListView.as_view(), name="api_projects"),
    path("api/examples/sample-project/", views.ExampleProjectView.as_view(), name="api_example_sample_project"),
    path("api/dashboard/summary/", views.DashboardSummaryView.as_view(), name="api_dashboard_summary"),
    path("api/fields/", views.FieldCollectionView.as_view(), name="api_fields"),
    path("api/fields/<int:field_id>/", views.FieldDetailView.as_view(), name="api_field_detail"),
    path("api/records/", views.RecordCollectionView.as_view(), name="api_records"),
    path("api/records/<int:record_id>/", views.RecordDetailView.as_view(), name="api_record_detail"),
    path("api/import/preview/", views.ImportPreviewView.as_view(), name="api_import_preview"),
    path("api/import/commit/", views.ImportCommitView.as_view(), name="api_import_commit"),
    path("api/export/csv/", views.ExportCsvView.as_view(), name="api_export_csv"),
    path("api/export/template/csv/", views.ExportCsvTemplateView.as_view(), name="api_export_csv_template"),
    path("api/train/", views.TrainView.as_view(), name="api_train"),
    path("api/models/summary/", views.ModelSummaryView.as_view(), name="api_model_summary"),
    path("api/models/activate/", views.ModelActivateView.as_view(), name="api_model_activate"),
    path("api/predict/", views.PredictView.as_view(), name="api_predict"),
]
