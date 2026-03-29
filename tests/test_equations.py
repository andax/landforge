"""
Unit tests for IPC-7351B tolerance equations.

Tests are verified against:
1. Worked example in IPC-7351B page 11 (SO16 component)
2. Known good results for common chip components
3. Boundary conditions and edge cases
"""

import math
import pytest

from generator.core.ipc_equations import (
    DensityLevel,
    ComponentDimensions,
    ComponentDimensionsFromSpec,
    LandPatternResult,
    calculate_land_pattern,
    calculate_courtyard,
    calculate_bga_land_diameter,
    round_to,
    round_down_to,
)
from generator.core.tables import (
    TABLE_3_2,
    TABLE_3_5,
    TABLE_3_6,
    TABLE_3_7,
    TABLE_3_13,
    TABLE_3_15,
    TABLE_3_17,
    TABLE_3_22,
    TABLES,
)


class TestRounding:
    """Test IPC rounding rules."""

    def test_round_to_005(self):
        assert round_to(1.42, 0.05) == 1.45
        assert round_to(1.40, 0.05) == 1.40
        assert round_to(1.41, 0.05) == 1.45
        assert round_to(1.001, 0.05) == 1.05

    def test_round_down_to_005(self):
        assert round_down_to(1.48, 0.05) == 1.45
        assert round_down_to(1.50, 0.05) == 1.50
        assert round_down_to(1.49, 0.05) == 1.45

    def test_round_to_002(self):
        """Small chip components use 0.02mm rounding."""
        assert round_to(0.51, 0.02) == 0.52
        assert round_to(0.50, 0.02) == 0.50
        assert round_to(0.501, 0.02) == 0.52

    def test_round_down_to_002(self):
        assert round_down_to(0.51, 0.02) == 0.50
        assert round_down_to(0.52, 0.02) == 0.52


class TestRMSToleranceAccumulation:
    """Test RMS tolerance calculation from IPC-7351B page 11."""

    def test_so16_rms_tolerance(self):
        """Verify the SO16 worked example from IPC-7351B page 11.

        Given: L_min=5.8, L_max=6.2, T_min=0.4, T_max=1.27
        L_tol = 0.4, T_tol = 0.87
        S_tol(RMS) = sqrt(0.4^2 + 2*0.87^2) = sqrt(0.16 + 1.5138) = 1.294
        """
        spec = ComponentDimensionsFromSpec(
            L_min=5.8, L_max=6.2,
            T_min=0.4, T_max=1.27,
            W_min=0.31, W_max=0.51,
        )

        L_tol = spec.L_max - spec.L_min
        T_tol = spec.T_max - spec.T_min
        assert L_tol == pytest.approx(0.4)
        assert T_tol == pytest.approx(0.87)

        S_tol_rms = math.sqrt(L_tol**2 + 2 * T_tol**2)
        # IPC standard gives ~1.30 (they round to 2 decimal places)
        assert S_tol_rms == pytest.approx(1.294, abs=0.01)

        comp = spec.to_component_dimensions()

        # The S range should be narrower than worst-case due to RMS adjustment
        S_min_worst = spec.L_min - 2 * spec.T_max  # 5.8 - 2*1.27 = 3.26
        S_max_worst = spec.L_max - 2 * spec.T_min  # 6.2 - 2*0.4 = 5.40
        S_tol_worst = S_max_worst - S_min_worst  # 2.14

        assert comp.S_min > S_min_worst  # RMS tightens the range
        assert comp.S_max < S_max_worst
        assert (comp.S_max - comp.S_min) == pytest.approx(S_tol_rms, abs=0.01)

    def test_so16_g_dimension(self):
        """Verify G_min calculation for SO16 using Table 3-2 Level B.

        IPC-7351B page 12 shows a general example with J=0.5 (not from Table 3-2).
        Here we verify the actual Table 3-2 Level B calculation (J_H=0.35).

        G_raw = S_max - 2*J_H - sqrt(CS^2 + F^2 + P^2)
        With RMS-adjusted S_max and Table 3-2 Level B (J_H=0.35), F=0.10, P=0.05.
        """
        spec = ComponentDimensionsFromSpec(
            L_min=5.8, L_max=6.2,
            T_min=0.4, T_max=1.27,
            W_min=0.31, W_max=0.51,
        )
        comp = spec.to_component_dimensions()

        result = calculate_land_pattern(
            comp, TABLE_3_2, DensityLevel.B,
            fab_tol=0.10, place_tol=0.05,
        )

        # G should be positive and smaller than S_max
        assert result.G > 0
        assert result.G < comp.S_max
        # Manually verify: G_raw = S_max - 2*0.35 - sqrt(CS^2 + 0.1^2 + 0.05^2)
        rss = math.sqrt(comp.CS**2 + 0.10**2 + 0.05**2)
        G_raw = comp.S_max - 2 * 0.35 - rss
        # G should be G_raw rounded down to 0.05mm grid
        assert result.G == pytest.approx(math.floor(G_raw / 0.05) * 0.05, abs=0.001)


class TestChipComponentCalculation:
    """Test chip component (RESC, CAPC) calculations using Table 3-5."""

    def test_0603_resistor_level_b(self):
        """0603 (1608) chip resistor at density Level B.

        Typical 0603: L=1.6±0.1, W=0.8±0.1, T=0.3±0.1
        L_min=1.5, L_max=1.7, S_min=0.7, S_max=1.1, W_min=0.7, W_max=0.9
        (S derived from L and T)
        """
        spec = ComponentDimensionsFromSpec(
            L_min=1.50, L_max=1.70,
            T_min=0.20, T_max=0.40,
            W_min=0.70, W_max=0.90,
        )
        comp = spec.to_component_dimensions()
        result = calculate_land_pattern(comp, TABLE_3_5, DensityLevel.B)

        # Pad dimensions should be reasonable for a 0603
        assert 0.7 < result.pad_length < 1.2
        assert 0.7 < result.pad_width < 1.2
        assert 1.0 < result.pad_center_to_center < 2.0

        # Z should be larger than component
        assert result.Z > comp.L_max
        # G should be smaller than inner termination distance
        assert result.G < comp.S_max

    def test_0603_density_ordering(self):
        """Verify A > B > C for pad dimensions and courtyard."""
        spec = ComponentDimensionsFromSpec(
            L_min=1.50, L_max=1.70,
            T_min=0.20, T_max=0.40,
            W_min=0.70, W_max=0.90,
        )
        comp = spec.to_component_dimensions()

        results = {
            level: calculate_land_pattern(comp, TABLE_3_5, level)
            for level in DensityLevel
        }

        # Level A should have largest pads (most land protrusion)
        assert results[DensityLevel.A].Z >= results[DensityLevel.B].Z
        assert results[DensityLevel.B].Z >= results[DensityLevel.C].Z

        # Level A should have widest pads
        assert results[DensityLevel.A].X >= results[DensityLevel.B].X
        assert results[DensityLevel.B].X >= results[DensityLevel.C].X

        # Level A should have smallest gap (more overlap with component)
        assert results[DensityLevel.A].G <= results[DensityLevel.B].G
        assert results[DensityLevel.B].G <= results[DensityLevel.C].G

    def test_small_chip_uses_finer_rounding(self):
        """Components < 0603 should use 0.02mm rounding (Table 3-6)."""
        assert TABLE_3_6.roundoff == 0.02

        # 0402 (1005) chip
        spec = ComponentDimensionsFromSpec(
            L_min=0.90, L_max=1.10,
            T_min=0.15, T_max=0.35,
            W_min=0.40, W_max=0.60,
        )
        comp = spec.to_component_dimensions()
        result = calculate_land_pattern(comp, TABLE_3_6, DensityLevel.B)

        # Check that results are on 0.02mm grid
        assert result.Z * 100 % 2 == pytest.approx(0, abs=0.001)
        assert result.X * 100 % 2 == pytest.approx(0, abs=0.001)


class TestMoldedBodyCalculation:
    """Test molded body (CAPMP, DIOM) using Table 3-13."""

    def test_table_3_13_reversed_toe_heel(self):
        """Table 3-13 has toe for inner (G) and heel for outer (Z).

        The heel value (outer) should be larger than toe (inner).
        """
        # Level B: heel=0.50 (outer), toe=0.15 (inner)
        assert TABLE_3_13.fillet_B.heel > TABLE_3_13.fillet_B.toe


class TestQFNCalculation:
    """Test QFN calculations using Table 3-15."""

    def test_qfn_heel_is_zero(self):
        """QFN heel fillet is always zero (component sits directly on pad)."""
        for level in DensityLevel:
            assert TABLE_3_15.fillet(level).heel == 0.0

    def test_qfn_side_is_negative(self):
        """QFN side fillet is negative (pad narrower than terminal)."""
        for level in DensityLevel:
            assert TABLE_3_15.fillet(level).side < 0.0


class TestBGACalculation:
    """Test BGA land diameter calculations using Table 3-17."""

    def test_collapsible_ball_0p5mm(self):
        """0.5mm collapsible ball: land should be smaller than ball."""
        for level in DensityLevel:
            land = calculate_bga_land_diameter(0.5, level, collapsible=True)
            assert land < 0.5

    def test_collapsible_density_ordering(self):
        """Level A should give smallest land (most reduction) for collapsible.

        After 0.05mm rounding, adjacent levels may be equal but never reversed.
        """
        land_a = calculate_bga_land_diameter(0.5, DensityLevel.A, collapsible=True)
        land_b = calculate_bga_land_diameter(0.5, DensityLevel.B, collapsible=True)
        land_c = calculate_bga_land_diameter(0.5, DensityLevel.C, collapsible=True)
        assert land_a <= land_b <= land_c

        # Use a larger ball where the difference survives rounding
        land_a = calculate_bga_land_diameter(1.0, DensityLevel.A, collapsible=True)
        land_b = calculate_bga_land_diameter(1.0, DensityLevel.B, collapsible=True)
        land_c = calculate_bga_land_diameter(1.0, DensityLevel.C, collapsible=True)
        assert land_a < land_b < land_c

    def test_non_collapsible_ball(self):
        """Non-collapsible ball: land should be larger than ball."""
        land = calculate_bga_land_diameter(0.4, DensityLevel.B, collapsible=False)
        assert land >= 0.4

    def test_bga_courtyard_is_large(self):
        """BGA courtyard excess is much larger than other packages."""
        assert TABLE_3_17.courtyard.A == 2.00
        assert TABLE_3_17.courtyard.B == 1.00
        assert TABLE_3_17.courtyard.C == 0.50


class TestCourtyardCalculation:
    """Test courtyard dimension calculations."""

    def test_courtyard_exceeds_body_and_pads(self):
        """Courtyard must be larger than both body and land pattern."""
        body_w, body_l = 0.8, 1.6  # 0603 body
        lp = LandPatternResult(Z=2.6, G=0.6, X=1.0)

        cy_w, cy_l = calculate_courtyard(body_w, body_l, lp, TABLE_3_5, DensityLevel.B)

        assert cy_l > max(body_l, lp.Z)
        assert cy_w > max(body_w, lp.X)

    def test_courtyard_on_grid(self):
        """Courtyard dimensions should be on 0.05mm grid."""
        body_w, body_l = 0.8, 1.6
        lp = LandPatternResult(Z=2.6, G=0.6, X=1.0)

        cy_w, cy_l = calculate_courtyard(body_w, body_l, lp, TABLE_3_5, DensityLevel.B)

        assert cy_w * 100 % 5 == pytest.approx(0, abs=0.001)
        assert cy_l * 100 % 5 == pytest.approx(0, abs=0.001)


class TestLandPatternResult:
    """Test derived properties of LandPatternResult."""

    def test_pad_dimensions(self):
        lp = LandPatternResult(Z=3.0, G=1.0, X=0.8)
        assert lp.pad_length == pytest.approx(1.0)  # (3.0 - 1.0) / 2
        assert lp.pad_width == pytest.approx(0.8)
        assert lp.pad_center_to_center == pytest.approx(2.0)  # (3.0 + 1.0) / 2


class TestTableCompleteness:
    """Verify all tables are defined and accessible."""

    def test_all_tables_present(self):
        expected = [
            "3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8", "3-9",
            "3-10", "3-11", "3-12", "3-13", "3-14", "3-15", "3-16",
            "3-17", "3-18", "3-19", "3-20", "3-20L", "3-21", "3-22",
        ]
        for table_id in expected:
            assert table_id in TABLES, f"Table {table_id} missing"
            t = TABLES[table_id]
            assert t.name == table_id
            # All tables must have valid courtyard values
            assert t.courtyard.A >= t.courtyard.B >= t.courtyard.C

    def test_all_tables_have_decreasing_toe_fillet(self):
        """Toe fillet should decrease from A to C for all non-BGA tables."""
        skip = {"3-17", "3-21"}  # BGA/CGA/LGA use different approach
        for table_id, t in TABLES.items():
            if table_id in skip:
                continue
            assert t.fillet_A.toe >= t.fillet_B.toe >= t.fillet_C.toe, (
                f"Table {table_id}: toe fillet not decreasing A>=B>=C"
            )


class TestDensityLevel:
    """Test DensityLevel enum."""

    def test_suffix_mapping(self):
        assert DensityLevel.A.value == "M"  # Most
        assert DensityLevel.B.value == "N"  # Nominal
        assert DensityLevel.C.value == "L"  # Least
