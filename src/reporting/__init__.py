__all__ = ["SavedRunArtifacts", "save_hypersphere_run"]


def __getattr__(name: str):
    if name in __all__:
        from reporting.result_files import SavedRunArtifacts, save_hypersphere_run

        exports = {
            "SavedRunArtifacts": SavedRunArtifacts,
            "save_hypersphere_run": save_hypersphere_run,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
