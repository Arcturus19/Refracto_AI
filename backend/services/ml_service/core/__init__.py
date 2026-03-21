"""Core ML utilities for Refracto AI.

Keep imports lazy so offline scripts can import individual core modules without
forcing application settings or model bootstrapping.
"""

from importlib import import_module

__all__ = [
    "RefractoModels",
    "get_models",
    "load_models_on_startup",
    "VisualExplainer",
    "get_explainer",
    "generate_grad_cam",
    "LogicEngine",
    "get_logic_engine",
    "analyze_clinical_risk",
]

_LAZY_IMPORTS = {
    "RefractoModels": (".model_loader", "RefractoModels"),
    "get_models": (".model_loader", "get_models"),
    "load_models_on_startup": (".model_loader", "load_models_on_startup"),
    "VisualExplainer": (".xai_engine", "VisualExplainer"),
    "get_explainer": (".xai_engine", "get_explainer"),
    "generate_grad_cam": (".xai_engine", "generate_grad_cam"),
    "LogicEngine": (".logic_engine", "LogicEngine"),
    "get_logic_engine": (".logic_engine", "get_logic_engine"),
    "analyze_clinical_risk": (".logic_engine", "analyze_clinical_risk"),
}


def __getattr__(name):
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'core' has no attribute {name!r}")

    module_name, attribute_name = _LAZY_IMPORTS[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value

