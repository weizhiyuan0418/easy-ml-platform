from __future__ import annotations

from django.apps import AppConfig


class MlappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mlapp"
    verbose_name = "通用机器学习平台"
