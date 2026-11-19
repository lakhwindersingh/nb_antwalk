"""
Enterprise UI Design System Token & Contract Validator Engine
Validates W3C Design Tokens, Theme Palettes, 8px Spatial Rhythm,
and Universal Data Grid Contracts against JSON Schemas.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


class UITokenValidator:
    """Validator for Enterprise UI design tokens, spatial invariants, and UI component contracts."""

    REPO_ROOT = Path(__file__).resolve().parents[2]
    CONTRACTS_DIR = REPO_ROOT / ".nb" / "context" / "contracts"

    # Standard Control Height Scale
    CONTROL_HEIGHTS = {
        "control-height-xs": "24px",
        "control-height-sm": "32px",
        "control-height-md": "40px",
        "control-height-lg": "48px",
        "control-height-xl": "56px",
    }

    # Standard 8px Spatial Scale
    SPATIAL_SCALE = {
        "space-0": "0px",
        "space-0-5": "4px",
        "space-1": "8px",
        "space-1-5": "12px",
        "space-2": "16px",
        "space-2-5": "20px",
        "space-3": "24px",
        "space-4": "32px",
        "space-5": "40px",
        "space-6": "48px",
        "space-8": "64px",
        "space-10": "80px",
        "space-12": "96px",
    }

    # Themes supported
    CERTIFIED_THEMES = ["corporate-light", "enterprise-dark", "pro-oled"]

    @classmethod
    def load_contract(cls, contract_name: str) -> Dict[str, Any]:
        """Loads a JSON schema contract from .nb/context/contracts/."""
        contract_path = cls.CONTRACTS_DIR / f"{contract_name}.json"
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract {contract_name} not found at {contract_path}")
        with open(contract_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def validate_spatial_value(cls, value_px: str) -> bool:
        """Verifies if a pixel value conforms strictly to the 8px grid (or 4px micro-increment)."""
        match = re.match(r"^(\d+)px$", value_px.strip())
        if not match:
            return False
        px = int(match.group(1))
        if px == 0 or px == 4:
            return True
        return px % 8 == 0 or px % 4 == 0

    @classmethod
    def validate_theme_dictionary(cls, theme_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates a complete theme dictionary against UIThemeTokenContract."""
        errors: List[str] = []
        if not theme_data.get("version"):
            errors.append("Missing required field: version")

        themes = theme_data.get("themes", [])
        if len(themes) < 3:
            errors.append("Must specify at least 3 certified themes (corporate-light, enterprise-dark, pro-oled)")

        found_theme_ids = set()
        for t in themes:
            tid = t.get("id")
            found_theme_ids.add(tid)
            if tid not in cls.CERTIFIED_THEMES:
                errors.append(f"Unrecognized theme id: {tid}")
            for req in ["name", "bg_app", "surface_card", "text_primary"]:
                if not t.get(req):
                    errors.append(f"Theme {tid} missing required color token: {req}")
            # Check status colors (support both semantic and legacy token names)
            has_success = t.get("color_status_success") or t.get("color_finance_gain")
            has_error = t.get("color_status_error") or t.get("color_finance_loss")
            if not has_success:
                errors.append(f"Theme {tid} missing success color token")
            if not has_error:
                errors.append(f"Theme {tid} missing error color token")

        for expected in cls.CERTIFIED_THEMES:
            if expected not in found_theme_ids:
                errors.append(f"Missing certified theme: {expected}")

        # Check spatial grid
        grid = theme_data.get("spatial_grid", {})
        if grid.get("base_unit_px") != 8:
            errors.append("spatial_grid.base_unit_px must be 8")

        scale = grid.get("scale", {})
        for token, expected_val in cls.SPATIAL_SCALE.items():
            if token in ["space-0-5", "space-1", "space-2", "space-3", "space-4", "space-6", "space-8"]:
                val = scale.get(token)
                if val != expected_val:
                    errors.append(f"Spatial scale token {token} must be {expected_val}, got {val}")

        # Check control heights
        heights = theme_data.get("control_heights", {})
        for token, expected_val in cls.CONTROL_HEIGHTS.items():
            val = heights.get(token)
            if val != expected_val:
                errors.append(f"Control height token {token} must be {expected_val}, got {val}")

        return (len(errors) == 0, errors)

    @classmethod
    def validate_data_grid_row(cls, row: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates a virtualized data grid row payload."""
        errors: List[str] = []
        required_fields = [
            "row_id",
            "name",
            "category",
            "status",
            "primary_metric",
            "secondary_metric",
            "timestamp",
        ]
        for f in required_fields:
            if f not in row:
                errors.append(f"Data grid row missing required field: {f}")

        status = row.get("status")
        valid_statuses = ["ACTIVE", "PENDING", "WARNING", "ERROR", "ARCHIVED", "OPEN", "COMPLETED"]
        if status not in valid_statuses:
            errors.append(f"Invalid row status: {status}")

        if "primary_metric" in row and not isinstance(row["primary_metric"], (int, float)):
            errors.append("primary_metric must be a numeric value")

        return (len(errors) == 0, errors)

    @classmethod
    def calculate_contrast_ratio(cls, lum1: float, lum2: float) -> float:
        """Calculates relative luminance contrast ratio between two values."""
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)
