#!/usr/bin/env python3
"""
Summer Breeze - A friendly CLI tool for managing SummerCart64
"""

import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()

# Use platform-appropriate binary
if platform.system() == "Windows":
    SC64_DEPLOYER = SCRIPT_DIR / "sc64deployer.exe"
else:
    SC64_DEPLOYER = SCRIPT_DIR / "sc64deployer"
LOCAL_ROMS_DIR = SCRIPT_DIR / "roms"
MENU_VERSIONS_DIR = SCRIPT_DIR / "menu_versions"
MENU_MUSIC_DIR = SCRIPT_DIR / "menu_music"

# SC64 menu file locations on SD card
SD_MENU_PATH = "/sc64menu.n64"
SD_MENU_MUSIC_PATH = "/menu/bg.mp3"

# ROM file extensions
ROM_EXTENSIONS = {".z64", ".n64", ".v64"}


def run_sc64_command(args: list[str], capture_output=True) -> tuple[int, str, str]:
    """Run sc64deployer with given arguments."""
    cmd = [str(SC64_DEPLOYER)] + args
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, cwd=str(SCRIPT_DIR))
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Error: sc64deployer not found at {SC64_DEPLOYER}"


def check_device_connected() -> bool:
    """Check if SC64 device is connected."""
    code, stdout, stderr = run_sc64_command(["list"])
    return code == 0 and "Found devices:" in stdout


def is_sd_card_accessible() -> bool:
    """Check if SD card is actually accessible by trying to list files."""
    code, stdout, stderr = run_sc64_command(["sd", "ls"])
    # If we get any output with the pipe separator, the SD card is working
    return code == 0 and "|" in stdout


def list_sd_card_files(path: str = None) -> list[dict]:
    """List files on the SD card at given path."""
    # If no path specified, list root (sc64deployer uses no arg for root)
    if path is None or path == "/":
        code, stdout, stderr = run_sc64_command(["sd", "ls"])
    else:
        code, stdout, stderr = run_sc64_command(["sd", "ls", path])

    if code != 0:
        return []

    files = []
    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        # Parse format: "d ---- 2024-06-01 12:00:00 | /menu" or "f  32M 2025-12-01 19:03:12 | file.z64"
        if "|" not in line:
            continue

        parts = line.split("|", 1)
        if len(parts) != 2:
            continue

        meta = parts[0].strip()
        name = parts[1].strip()

        # First char is d (dir) or f (file)
        file_type = "dir" if meta.startswith("d") else "file"

        # Extract size if present (for files)
        size_str = ""
        meta_parts = meta.split()
        if len(meta_parts) >= 2:
            size_str = meta_parts[1]

        files.append(
            {"name": name, "type": file_type, "size": size_str, "path": name if name.startswith("/") else f"/{name}"}
        )
    return files


def get_all_sd_roms(path: str = None, found: list = None) -> list[str]:
    """Recursively get all ROM files from SD card."""
    if found is None:
        found = []

    files = list_sd_card_files(path)
    for f in files:
        if f["type"] == "dir":
            # Recurse into subdirectory
            get_all_sd_roms(f["path"], found)
        else:
            # Check if it's a ROM file
            name_lower = f["name"].lower()
            if any(name_lower.endswith(ext) for ext in ROM_EXTENSIONS):
                found.append(f)
    return found


def list_local_roms() -> list[Path]:
    """List all ROM files in the local roms directory."""
    if not LOCAL_ROMS_DIR.exists():
        return []

    roms = []
    for file in LOCAL_ROMS_DIR.rglob("*"):
        if file.is_file() and file.suffix.lower() in ROM_EXTENSIONS:
            roms.append(file)
    return sorted(roms, key=lambda x: x.name.lower())


def normalize_rom_name(name: str) -> str:
    """Normalize ROM name for comparison."""
    # Remove extension and convert to lowercase for comparison
    for ext in ROM_EXTENSIONS:
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
            break
    return name.lower().strip()


def upload_rom_to_sd(local_path: Path, sd_path: str = "/") -> bool:
    """Upload a ROM file to the SD card."""
    dest = f"{sd_path.rstrip('/')}/{local_path.name}"
    print(f"Uploading: {local_path.name}")
    print(f"      To: {dest}")

    code, stdout, stderr = run_sc64_command(["sd", "upload", str(local_path), dest])
    if code == 0:
        print("  Upload complete!")
        return True
    else:
        print(f"  Upload failed: {stderr}")
        return False


def print_header(text: str):
    """Print a styled header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_menu(options: list[str], title: str = "Options"):
    """Print a numbered menu."""
    print()
    print(f"{title}:")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    print()


def get_choice(max_val: int, prompt: str = "Enter choice") -> int:
    """Get a numeric choice from user."""
    while True:
        try:
            choice = input(f"{prompt} (1-{max_val}, or 0 to cancel): ").strip()
            if choice == "0":
                return 0
            val = int(choice)
            if 1 <= val <= max_val:
                return val
            print(f"Please enter a number between 1 and {max_val}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print()
            return 0


def get_multi_choice(max_val: int, prompt: str = "Enter choices") -> list[int]:
    """Get multiple numeric choices from user (comma-separated or 'all')."""
    while True:
        try:
            raw = input(f"{prompt} (e.g. 1,3,5 or 'all', or 0 to cancel): ").strip().lower()
            if raw == "0":
                return []
            if raw == "all":
                return list(range(1, max_val + 1))

            choices = []
            for part in raw.split(","):
                val = int(part.strip())
                if 1 <= val <= max_val:
                    choices.append(val)
                else:
                    print(f"Skipping invalid choice: {val}")
            return sorted(set(choices))
        except ValueError:
            print("Please enter valid numbers separated by commas")
        except KeyboardInterrupt:
            print()
            return []


def cmd_status():
    """Show device and SD card status."""
    print_header("SC64 Status")

    if not check_device_connected():
        print("Device: NOT CONNECTED")
        print("\nMake sure your SummerCart64 is plugged in via USB.")
        return False

    print("Device: CONNECTED")

    code, stdout, stderr = run_sc64_command(["info"])
    if code == 0:
        # Extract key info
        for line in stdout.split("\n"):
            if any(k in line for k in ["Firmware version", "Boot mode"]):
                print(f"  {line.strip()}")

    # Check actual SD card accessibility
    if is_sd_card_accessible():
        print("  SD card:         Accessible")
        return True
    else:
        print("  SD card:         Not accessible")
        print("\n  Note: SD card access requires the N64 to be powered ON")
        return False


def cmd_list_local():
    """List ROMs in local directory."""
    print_header("Local ROMs")
    print(f"Directory: {LOCAL_ROMS_DIR}")
    print()

    roms = list_local_roms()
    if not roms:
        print("No ROM files found.")
        print(f"Add .z64, .n64, or .v64 files to: {LOCAL_ROMS_DIR}")
        return

    for i, rom in enumerate(roms, 1):
        size_mb = rom.stat().st_size / (1024 * 1024)
        print(f"  [{i:2}] {rom.name} ({size_mb:.1f} MB)")

    print(f"\nTotal: {len(roms)} ROM(s)")


def cmd_list_cart():
    """List ROMs on the SD card."""
    print_header("Cart SD Card Contents")

    if not is_sd_card_accessible():
        print("SD card is not accessible.")
        print("Make sure your N64 is powered ON to access the SD card.")
        return

    # Show root directory
    print("SD Card Root:")
    files = list_sd_card_files()
    if not files:
        print("  (empty or not accessible)")
        return

    roms_in_root = []
    dirs = []

    for f in files:
        if f["type"] == "dir":
            dirs.append(f)
            icon = "[DIR]"
        else:
            is_rom = any(f["name"].lower().endswith(e) for e in ROM_EXTENSIONS)
            if is_rom:
                roms_in_root.append(f)
            icon = "[ROM]" if is_rom else "[   ]"

        size_info = f" ({f['size']})" if f.get("size") and f["size"] != "----" else ""
        print(f"  {icon} {f['name']}{size_info}")

    # Show ROMs in subdirectories
    print("\nAll ROMs on cart:")
    all_roms = get_all_sd_roms()

    if not all_roms:
        print("  No ROM files found on SD card.")
    else:
        for i, rom in enumerate(all_roms, 1):
            size_info = f" ({rom['size']})" if rom.get("size") and rom["size"] != "----" else ""
            print(f"  [{i:2}] {rom['name']}{size_info}")
        print(f"\nTotal: {len(all_roms)} ROM(s)")


def cmd_compare():
    """Compare local ROMs with cart and show what's missing on cart."""
    print_header("Compare Local vs Cart")

    local_roms = list_local_roms()
    if not local_roms:
        print("No local ROMs found.")
        return []

    if not is_sd_card_accessible():
        print("SD card is not accessible - showing all local ROMs as 'missing on cart'")
        print("(Power on your N64 to enable SD card access for accurate comparison)")
        print()

        for i, rom in enumerate(local_roms, 1):
            size_mb = rom.stat().st_size / (1024 * 1024)
            print(f"  [{i:2}] {rom.name} ({size_mb:.1f} MB)")

        return local_roms

    # Get all ROMs from SD card
    print("Scanning SD card...")
    sd_roms = get_all_sd_roms()
    sd_rom_names = {normalize_rom_name(r["name"]) for r in sd_roms}

    print(f"Found {len(sd_roms)} ROM(s) on cart")

    # Find ROMs not on cart
    missing = []
    on_cart = []
    for rom in local_roms:
        normalized = normalize_rom_name(rom.name)
        if normalized not in sd_rom_names:
            missing.append(rom)
        else:
            on_cart.append(rom)

    if on_cart:
        print(f"\nAlready on cart ({len(on_cart)}):")
        for rom in on_cart:
            print(f"  [OK] {rom.name}")

    if not missing:
        print("\nAll local ROMs are already on the cart!")
        return []

    print(f"\nNOT on cart ({len(missing)}):")
    for i, rom in enumerate(missing, 1):
        size_mb = rom.stat().st_size / (1024 * 1024)
        print(f"  [{i:2}] {rom.name} ({size_mb:.1f} MB)")

    return missing


def cmd_upload():
    """Interactive upload of ROMs to cart."""
    print_header("Upload ROMs to Cart")

    # First check device
    if not check_device_connected():
        print("SC64 device not connected!")
        return

    if not is_sd_card_accessible():
        print("SD card is not accessible.")
        print("Power ON your N64 to enable SD card access.")
        return

    # Get missing ROMs
    missing = cmd_compare()
    if not missing:
        return

    print("\nWhich ROMs would you like to upload?")
    choices = get_multi_choice(len(missing), "Select ROMs")

    if not choices:
        print("Upload cancelled.")
        return

    # Ask for destination
    print("\nUpload destination on SD card:")
    print("  [1] Root directory (/)")
    print("  [2] Custom path")
    dest_choice = get_choice(2, "Choose destination")

    if dest_choice == 0:
        print("Upload cancelled.")
        return

    dest_path = "/"
    if dest_choice == 2:
        dest_path = input("Enter SD card path (e.g. /roms): ").strip()
        if not dest_path.startswith("/"):
            dest_path = "/" + dest_path

    # Upload selected ROMs
    print()
    success_count = 0
    for idx in choices:
        rom = missing[idx - 1]
        if upload_rom_to_sd(rom, dest_path):
            success_count += 1

    print(f"\nDone! Uploaded {success_count}/{len(choices)} ROM(s).")


def cmd_quick_upload():
    """Quick upload - select from local ROMs and upload immediately."""
    print_header("Quick Upload")

    if not check_device_connected():
        print("SC64 device not connected!")
        return

    if not is_sd_card_accessible():
        print("SD card is not accessible.")
        print("Power ON your N64 to enable SD card access.")
        return

    local_roms = list_local_roms()
    if not local_roms:
        print("No local ROMs found.")
        return

    print("Select ROM(s) to upload:")
    for i, rom in enumerate(local_roms, 1):
        size_mb = rom.stat().st_size / (1024 * 1024)
        print(f"  [{i:2}] {rom.name} ({size_mb:.1f} MB)")

    choices = get_multi_choice(len(local_roms), "Select ROMs")
    if not choices:
        print("Upload cancelled.")
        return

    print()
    for idx in choices:
        rom = local_roms[idx - 1]
        upload_rom_to_sd(rom, "/")


def ensure_menu_versions_dir():
    """Ensure the menu_versions directory exists."""
    if not MENU_VERSIONS_DIR.exists():
        MENU_VERSIONS_DIR.mkdir()
        print(f"Created directory: {MENU_VERSIONS_DIR}")


def list_local_menu_versions() -> list[Path]:
    """List all menu files in the menu_versions directory."""
    ensure_menu_versions_dir()

    menu_files = []
    for file in MENU_VERSIONS_DIR.iterdir():
        if file.is_file() and file.suffix.lower() in ROM_EXTENSIONS:
            menu_files.append(file)
    return sorted(menu_files, key=lambda x: x.name.lower())


def backup_menu_from_cart() -> bool:
    """Download current sc64menu.n64 from cart and save with timestamp."""
    ensure_menu_versions_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"sc64menu_backup_{timestamp}.n64"
    backup_path = MENU_VERSIONS_DIR / backup_name

    print("Backing up current menu from cart...")
    print(f"  From: {SD_MENU_PATH}")
    print(f"    To: {backup_path}")

    code, stdout, stderr = run_sc64_command(["sd", "download", SD_MENU_PATH, str(backup_path)])
    if code == 0:
        print("  Backup complete!")
        return True
    else:
        print(f"  Backup failed: {stderr}")
        return False


def upload_menu_to_cart(local_path: Path) -> bool:
    """Upload a menu file to the cart, replacing the existing one."""
    print("Uploading new menu to cart...")
    print(f"  From: {local_path.name}")
    print(f"    To: {SD_MENU_PATH}")

    code, stdout, stderr = run_sc64_command(["sd", "upload", str(local_path), SD_MENU_PATH])
    if code == 0:
        print("  Upload complete!")
        return True
    else:
        print(f"  Upload failed: {stderr}")
        return False


def cmd_update_menu():
    """Update the SC64 menu on the cart."""
    print_header("Update SC64 Menu")

    if not check_device_connected():
        print("SC64 device not connected!")
        return

    if not is_sd_card_accessible():
        print("SD card is not accessible.")
        print("Power ON your N64 to enable SD card access.")
        return

    # List available menu versions
    menu_versions = list_local_menu_versions()
    if not menu_versions:
        print(f"No menu files found in: {MENU_VERSIONS_DIR}")
        print("\nAdd .z64, .n64, or .v64 menu files to this directory.")
        return

    # Paginate menu versions (9 per page)
    items_per_page = 9
    total_items = len(menu_versions)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = 0

    selected_menu = None
    while selected_menu is None:
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = menu_versions[start_idx:end_idx]

        print(f"\nAvailable menu versions in {MENU_VERSIONS_DIR.name}/ (Page {current_page + 1}/{total_pages}):")
        for i, menu in enumerate(page_items, 1):
            size_mb = menu.stat().st_size / (1024 * 1024)
            print(f"  [{i:2}] {menu.name} ({size_mb:.1f} MB)")

        # Show navigation options
        nav_options = []
        if current_page > 0:
            nav_options.append("P=Prev")
        if current_page < total_pages - 1:
            nav_options.append("N=Next")
        nav_options.append("0=Cancel")

        nav_str = ", ".join(nav_options)
        prompt = f"Select menu (1-{len(page_items)}) [{nav_str}]: "

        try:
            user_input = input(prompt).strip().lower()
        except KeyboardInterrupt:
            print()
            print("Update cancelled.")
            return

        if user_input == "0":
            print("Update cancelled.")
            return
        elif user_input == "p" and current_page > 0:
            current_page -= 1
        elif user_input == "n" and current_page < total_pages - 1:
            current_page += 1
        else:
            try:
                choice = int(user_input)
                if 1 <= choice <= len(page_items):
                    selected_menu = page_items[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(page_items)}")
            except ValueError:
                print("Invalid input. Enter a number or navigation key.")

    # Confirm before proceeding
    print(f"\nYou selected: {selected_menu.name}")
    print("This will:")
    print("  1. Backup the current menu from cart (with timestamp)")
    print("  2. Upload the selected menu to replace it")
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Update cancelled.")
        return

    # Backup current menu
    print()
    if not backup_menu_from_cart():
        print("\nBackup failed. Aborting update to be safe.")
        return

    # Upload new menu
    print()
    if upload_menu_to_cart(selected_menu):
        print("\nMenu update complete!")
    else:
        print("\nMenu upload failed. Your backup is saved in menu_versions/")


def ensure_menu_music_dir():
    """Ensure the menu_music directory exists."""
    if not MENU_MUSIC_DIR.exists():
        MENU_MUSIC_DIR.mkdir()
        print(f"Created directory: {MENU_MUSIC_DIR}")


def list_local_music() -> list[Path]:
    """List all MP3 files in the menu_music directory."""
    ensure_menu_music_dir()

    music_files = []
    for file in MENU_MUSIC_DIR.iterdir():
        if file.is_file() and file.suffix.lower() == ".mp3":
            music_files.append(file)
    return sorted(music_files, key=lambda x: x.name.lower())


def check_menu_music_exists() -> bool:
    """Check if background music exists on the cart."""
    code, stdout, stderr = run_sc64_command(["sd", "stat", SD_MENU_MUSIC_PATH])
    return code == 0


def delete_menu_music() -> bool:
    """Delete background music from the cart."""
    print("Removing background music from cart...")
    print(f"  Deleting: {SD_MENU_MUSIC_PATH}")

    code, stdout, stderr = run_sc64_command(["sd", "rm", SD_MENU_MUSIC_PATH])
    if code == 0:
        print("  Removed!")
        return True
    else:
        print(f"  Failed to remove: {stderr}")
        return False


def upload_menu_music(local_path: Path) -> bool:
    """Upload an MP3 file as background music to the cart."""
    print("Uploading background music to cart...")
    print(f"  From: {local_path.name}")
    print(f"    To: {SD_MENU_MUSIC_PATH}")

    code, stdout, stderr = run_sc64_command(["sd", "upload", str(local_path), SD_MENU_MUSIC_PATH])
    if code == 0:
        print("  Upload complete!")
        return True
    else:
        print(f"  Upload failed: {stderr}")
        return False


def cmd_menu_music():
    """Set or unset menu background music."""
    print_header("Menu Background Music")

    print("NOTE: This feature only works with a customized version of")
    print("      SC64 menu by TheLeggett (as of Dec 22, 2025).")
    print()

    if not check_device_connected():
        print("SC64 device not connected!")
        return

    if not is_sd_card_accessible():
        print("SD card is not accessible.")
        print("Power ON your N64 to enable SD card access.")
        return

    # Check current state
    has_music = check_menu_music_exists()
    if has_music:
        print(f"Current status: Background music IS set ({SD_MENU_MUSIC_PATH} exists)")
    else:
        print(f"Current status: No background music (no {SD_MENU_MUSIC_PATH})")

    # List available music files
    music_files = list_local_music()

    print(f"\nAvailable MP3s in {MENU_MUSIC_DIR.name}/:")
    if not music_files:
        print("  (no MP3 files found)")
    else:
        for i, mp3 in enumerate(music_files, 1):
            size_mb = mp3.stat().st_size / (1024 * 1024)
            print(f"  [{i:2}] {mp3.name} ({size_mb:.1f} MB)")

    # Build options
    print("\nOptions:")
    option_num = 1
    options_map = {}

    if music_files:
        for mp3 in music_files:
            print(f"  [{option_num}] Set music to: {mp3.name}")
            options_map[option_num] = ("set", mp3)
            option_num += 1

    if has_music:
        print(f"  [{option_num}] Remove background music")
        options_map[option_num] = ("remove", None)
        option_num += 1

    if not options_map:
        print("\nNo actions available. Add MP3 files to menu_music/ directory.")
        return

    print()
    choice = get_choice(option_num - 1, "Select option")
    if choice == 0:
        print("Cancelled.")
        return

    action, mp3_file = options_map[choice]

    if action == "remove":
        delete_menu_music()
        print("\nBackground music removed!")
    else:
        # If music already exists, we'll overwrite it
        if has_music:
            print("\nReplacing existing background music...")
        print()
        if upload_menu_music(mp3_file):
            print("\nBackground music set!")
        else:
            print("\nFailed to set background music.")


def cmd_sync_rtc():
    """Synchronize the SC64 real-time clock with the PC's system time."""
    print_header("Sync RTC Clock")

    if not check_device_connected():
        print("SC64 device not connected!")
        return

    print("Synchronizing SC64 clock with system time...")
    returncode, stdout, stderr = run_sc64_command(["set", "rtc"])

    if returncode == 0:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"RTC synchronized to: {current_time}")
    else:
        print("Failed to sync RTC clock.")
        if stderr:
            print(f"Error: {stderr}")


def cmd_browse_sd():
    """Interactive SD card browser for debugging."""
    print_header("SD Card Browser")

    if not check_device_connected():
        print("SC64 device not connected!")
        return

    if not is_sd_card_accessible():
        print("SD card is not accessible.")
        print("Power ON your N64 to enable SD card access.")
        return

    current_path = "/"
    history = []

    while True:
        print()
        print("=" * 50)
        print(f"  Current path: {current_path}")
        print("=" * 50)

        # Get directory contents
        files = list_sd_card_files(current_path if current_path != "/" else None)

        if not files:
            print("  (empty directory)")
        else:
            # Separate dirs and files, sort alphabetically
            dirs = sorted([f for f in files if f["type"] == "dir"], key=lambda x: x["name"].lower())
            regular_files = sorted([f for f in files if f["type"] == "file"], key=lambda x: x["name"].lower())

            # Display directories first
            idx = 1
            item_map = {}

            for d in dirs:
                print(f"  [{idx:2}] [DIR]  {d['name']}/")
                item_map[idx] = d
                idx += 1

            # Then files
            for f in regular_files:
                size_info = f" ({f['size']})" if f.get("size") and f["size"] != "----" else ""
                # Highlight ROM files
                is_rom = any(f["name"].lower().endswith(ext) for ext in ROM_EXTENSIONS)
                marker = "[ROM]" if is_rom else "[   ]"
                print(f"  [{idx:2}] {marker} {f['name']}{size_info}")
                item_map[idx] = f
                idx += 1

        # Navigation options
        print()
        print("Navigation:")
        if current_path != "/":
            print("  [0] Go back (parent directory)")
        print("  [b] Back to main menu")
        if files:
            print(f"  [1-{len(files)}] Enter directory")
        print()

        try:
            choice = input("Enter choice: ").strip().lower()

            if choice == "b":
                print("Returning to main menu...")
                break

            if choice == "0" and current_path != "/":
                # Go to parent directory
                if history:
                    current_path = history.pop()
                else:
                    # Parse parent from path
                    parts = current_path.rstrip("/").rsplit("/", 1)
                    current_path = parts[0] if parts[0] else "/"
                continue

            # Try to parse as number
            try:
                num = int(choice)
                if num in item_map:
                    item = item_map[num]
                    if item["type"] == "dir":
                        # Navigate into directory
                        history.append(current_path)
                        if current_path == "/":
                            current_path = item["path"]
                        else:
                            current_path = f"{current_path.rstrip('/')}/{item['name']}"
                    else:
                        # Show file info
                        print()
                        print(f"  File: {item['name']}")
                        print(f"  Path: {item['path']}")
                        if item.get("size") and item["size"] != "----":
                            print(f"  Size: {item['size']}")
                        input("\n  Press Enter to continue...")
                else:
                    print(f"Invalid choice: {num}")
            except ValueError:
                print(f"Invalid input: {choice}")

        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break


def main_menu():
    """Display main menu and handle navigation."""
    while True:
        print_header("Summer Breeze")

        # Quick status check
        connected = check_device_connected()
        status_icon = "Connected" if connected else "NOT CONNECTED"
        print(f"Device: {status_icon}")

        options = [
            "Show Status",
            "List Local ROMs",
            "List Cart Contents",
            "Compare (show what's missing on cart)",
            "Upload ROMs to Cart",
            "Quick Upload",
            "Update SC64 Menu",
            "Set Menu Background Music",
            "Sync RTC Clock",
            "Browse SD Card",
            "Exit",
        ]

        print_menu(options, "Main Menu")
        choice = get_choice(len(options), "Select option")

        if choice == 0 or choice == 11:
            print("Goodbye!")
            break
        elif choice == 1:
            cmd_status()
        elif choice == 2:
            cmd_list_local()
        elif choice == 3:
            cmd_list_cart()
        elif choice == 4:
            cmd_compare()
        elif choice == 5:
            cmd_upload()
        elif choice == 6:
            cmd_quick_upload()
        elif choice == 7:
            cmd_update_menu()
        elif choice == 8:
            cmd_menu_music()
        elif choice == 9:
            cmd_sync_rtc()
        elif choice == 10:
            cmd_browse_sd()

        input("\nPress Enter to continue...")


def main():
    """Main entry point with CLI argument handling."""
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["status", "s"]:
            cmd_status()
        elif cmd in ["local", "l"]:
            cmd_list_local()
        elif cmd in ["cart", "c"]:
            cmd_list_cart()
        elif cmd in ["compare", "diff", "d"]:
            cmd_compare()
        elif cmd in ["upload", "u"]:
            cmd_upload()
        elif cmd in ["quick", "q"]:
            cmd_quick_upload()
        elif cmd in ["menu", "m"]:
            cmd_update_menu()
        elif cmd in ["music", "bgm"]:
            cmd_menu_music()
        elif cmd in ["browse", "sd"]:
            cmd_browse_sd()
        elif cmd in ["rtc", "clock", "time"]:
            cmd_sync_rtc()
        elif cmd in ["help", "h", "-h", "--help"]:
            print("Summer Breeze - A friendly CLI tool for managing SummerCart64")
            print()
            print("Usage: python summerbreeze.py [command]")
            print()
            print("Commands:")
            print("  status, s   - Show device and SD card status")
            print("  local, l    - List ROMs in local directory")
            print("  cart, c     - List ROMs on the SD card")
            print("  compare, d  - Show ROMs not yet on cart")
            print("  upload, u   - Interactive upload to cart")
            print("  quick, q    - Quick upload from local ROMs")
            print("  menu, m     - Update SC64 menu on cart")
            print("  music, bgm  - Set menu background music")
            print("  rtc, clock  - Sync RTC clock with system time")
            print("  browse, sd  - Browse SD card contents")
            print()
            print("Run without arguments for interactive menu.")
        else:
            print(f"Unknown command: {cmd}")
            print("Run with --help for usage information")
    else:
        main_menu()


if __name__ == "__main__":
    main()
