"""
Percipience Platform Configuration Manager
Provides centralized externalization of all system parameters, ports, endpoints,
quotas, TTLs, timeouts, model pricing rates, and cryptographic ledger limits.

Resolution Precedence:
1. Process Environment Variables (e.g. PERCIPIENCE_*, PORTAL_*, OTEL_*)
2. Platform Configuration File (.nb/config/platform_config.yaml)
3. Safe Built-in Hardcoded Defaults (for zero-config fallback)
"""

import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

try:
    import yaml
    try:
        from yaml import CSafeLoader as SafeLoader
    except ImportError:
        from yaml import SafeLoader
except ImportError:
    yaml = None
    SafeLoader = None


class ConfigManager:
    """Thread-safe singleton managing externalized platform configuration."""

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __init__(self, workspace_root: Optional[Path] = None):
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        else:
            cur = Path(__file__).resolve()
            if len(cur.parents) >= 3 and cur.parents[1].name in (".nb", "workplace"):
                self.workspace_root = cur.parents[2]
            else:
                self.workspace_root = cur.parents[1]

        self._config_data: Dict[str, Any] = {}
        self.reload()

    @classmethod
    def get_instance(cls, workspace_root: Optional[Path] = None) -> "ConfigManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(workspace_root)
            return cls._instance

    def reload(self) -> None:
        """Reloads configuration from YAML file and merges environment overrides."""
        config_path = self.workspace_root / ".nb" / "config" / "platform_config.yaml"
        loaded = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    if yaml and SafeLoader:
                        loaded = yaml.load(f, Loader=SafeLoader) or {}
                    elif yaml:
                        loaded = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️ ConfigManager: Failed to read {config_path}: {e}", file=sys.stderr)

        self._config_data = loaded

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value by dot-notated key path (e.g., 'portal.port').
        First checks matching environment variables, then YAML configuration, then default.
        """
        # 1. Check direct environment variable mappings
        env_var_name = self._to_env_var_name(key_path)
        if env_var_name in os.environ:
            val = os.environ[env_var_name]
            return self._cast_like_default(val, default)

        # Also check specific legacy environment variables
        legacy_env = self._get_legacy_env(key_path)
        if legacy_env and legacy_env in os.environ:
            return self._cast_like_default(os.environ[legacy_env], default)

        # 2. Check loaded configuration dict
        current = self._config_data
        for part in key_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current if current is not None else default

    def get_str(self, key_path: str, default: str = "") -> str:
        val = self.get(key_path, default)
        return str(val) if val is not None else default

    def get_int(self, key_path: str, default: int = 0) -> int:
        val = self.get(key_path, default)
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def get_float(self, key_path: str, default: float = 0.0) -> float:
        val = self.get(key_path, default)
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key_path: str, default: bool = False) -> bool:
        val = self.get(key_path, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "on")
        if isinstance(val, (int, float)):
            return bool(val)
        return default

    def get_list(self, key_path: str, default: Optional[List[Any]] = None) -> List[Any]:
        val = self.get(key_path, default or [])
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [x.strip() for x in val.split(",") if x.strip()]
        return default or []

    def get_dict(self, key_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        val = self.get(key_path, default or {})
        return val if isinstance(val, dict) else (default or {})

    @staticmethod
    def _to_env_var_name(key_path: str) -> str:
        """Converts dot-path e.g. portal.port to PERCIPIENCE_PORTAL_PORT."""
        sanitized = key_path.replace(".", "_").replace("-", "_").upper()
        return f"PERCIPIENCE_{sanitized}"

    @staticmethod
    def _get_legacy_env(key_path: str) -> Optional[str]:
        """Maps common standard environment variable aliases."""
        mapping = {
            "portal.port": "PORTAL_PORT",
            "portal.host": "PORTAL_HOST",
            "daemon.endpoint_url": "PERCIPIENCE_DAEMON_URL",
            "redis.url": "PERCIPIENCE_REDIS_URL",
            "otel.service_name": "OTEL_SERVICE_NAME",
            "otel.otlp_endpoint": "OTEL_EXPORTER_OTLP_ENDPOINT",
            "worktree.default_ttl_seconds": "WORKTREE_TTL",
        }
        return mapping.get(key_path)

    @staticmethod
    def _cast_like_default(val: str, default: Any) -> Any:
        if default is None:
            return val
        if isinstance(default, bool):
            return val.lower() in ("true", "1", "yes", "on")
        if isinstance(default, int):
            try:
                return int(val)
            except ValueError:
                return default
        if isinstance(default, float):
            try:
                return float(val)
            except ValueError:
                return default
        return val


# Module-level convenience singleton
config = ConfigManager.get_instance()
