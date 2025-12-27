"""Tests for Summer Breeze utility functions."""

from summerbreeze import (
    ROM_EXTENSIONS,
    list_local_roms,
    normalize_rom_name,
)


class TestNormalizeRomName:
    """Tests for ROM name normalization."""

    def test_removes_z64_extension(self):
        assert normalize_rom_name("Super Mario 64.z64") == "super mario 64"

    def test_removes_n64_extension(self):
        assert normalize_rom_name("Zelda.n64") == "zelda"

    def test_removes_v64_extension(self):
        assert normalize_rom_name("Game.v64") == "game"

    def test_case_insensitive_extension(self):
        assert normalize_rom_name("Game.Z64") == "game"
        assert normalize_rom_name("Game.N64") == "game"

    def test_strips_whitespace(self):
        # Whitespace in the name portion is stripped
        assert normalize_rom_name("  Game  .z64") == "game"

    def test_no_extension(self):
        assert normalize_rom_name("game") == "game"


class TestRomExtensions:
    """Tests for ROM extension constants."""

    def test_supported_extensions(self):
        assert ".z64" in ROM_EXTENSIONS
        assert ".n64" in ROM_EXTENSIONS
        assert ".v64" in ROM_EXTENSIONS

    def test_extension_count(self):
        assert len(ROM_EXTENSIONS) == 3


class TestListLocalRoms:
    """Tests for local ROM listing."""

    def test_empty_directory(self, tmp_path, monkeypatch):
        """Test with no ROM files."""
        roms_dir = tmp_path / "roms"
        roms_dir.mkdir()

        # Patch LOCAL_ROMS_DIR to use our temp directory
        import summerbreeze

        monkeypatch.setattr(summerbreeze, "LOCAL_ROMS_DIR", roms_dir)

        result = list_local_roms()
        assert result == []

    def test_finds_rom_files(self, tmp_path, monkeypatch):
        """Test finding ROM files."""
        roms_dir = tmp_path / "roms"
        roms_dir.mkdir()

        # Create test ROM files
        (roms_dir / "game1.z64").write_bytes(b"fake rom data")
        (roms_dir / "game2.n64").write_bytes(b"fake rom data")
        (roms_dir / "game3.v64").write_bytes(b"fake rom data")

        import summerbreeze

        monkeypatch.setattr(summerbreeze, "LOCAL_ROMS_DIR", roms_dir)

        result = list_local_roms()
        assert len(result) == 3
        names = [r.name for r in result]
        assert "game1.z64" in names
        assert "game2.n64" in names
        assert "game3.v64" in names

    def test_ignores_non_rom_files(self, tmp_path, monkeypatch):
        """Test that non-ROM files are ignored."""
        roms_dir = tmp_path / "roms"
        roms_dir.mkdir()

        # Create test files
        (roms_dir / "game.z64").write_bytes(b"fake rom data")
        (roms_dir / "readme.txt").write_text("readme")
        (roms_dir / "save.sra").write_bytes(b"save data")

        import summerbreeze

        monkeypatch.setattr(summerbreeze, "LOCAL_ROMS_DIR", roms_dir)

        result = list_local_roms()
        assert len(result) == 1
        assert result[0].name == "game.z64"

    def test_finds_roms_in_subdirectories(self, tmp_path, monkeypatch):
        """Test finding ROMs in nested directories."""
        roms_dir = tmp_path / "roms"
        roms_dir.mkdir()
        subdir = roms_dir / "subdir"
        subdir.mkdir()

        (roms_dir / "game1.z64").write_bytes(b"fake rom data")
        (subdir / "game2.z64").write_bytes(b"fake rom data")

        import summerbreeze

        monkeypatch.setattr(summerbreeze, "LOCAL_ROMS_DIR", roms_dir)

        result = list_local_roms()
        assert len(result) == 2

    def test_nonexistent_directory(self, tmp_path, monkeypatch):
        """Test with nonexistent directory."""
        roms_dir = tmp_path / "nonexistent"

        import summerbreeze

        monkeypatch.setattr(summerbreeze, "LOCAL_ROMS_DIR", roms_dir)

        result = list_local_roms()
        assert result == []

    def test_sorted_alphabetically(self, tmp_path, monkeypatch):
        """Test that results are sorted alphabetically."""
        roms_dir = tmp_path / "roms"
        roms_dir.mkdir()

        (roms_dir / "zelda.z64").write_bytes(b"data")
        (roms_dir / "mario.z64").write_bytes(b"data")
        (roms_dir / "kirby.z64").write_bytes(b"data")

        import summerbreeze

        monkeypatch.setattr(summerbreeze, "LOCAL_ROMS_DIR", roms_dir)

        result = list_local_roms()
        names = [r.name for r in result]
        assert names == ["kirby.z64", "mario.z64", "zelda.z64"]
