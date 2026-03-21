"""Compatibility package for integration tests.

The integration test suite imports symbols via `ml_service.*`.
In this repository layout, the ML service code lives directly under
`backend/services/ml_service/`.

This package provides a lightweight import shim so
`from ml_service.core.local_data_manager import LocalDataManager` works.
"""
