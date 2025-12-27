# SC64 ROM Manager

A user-friendly CLI tool for managing ROMs on your SummerCart64 flash cart.

## Requirements

- Python 3.10+
- SummerCart64 connected via USB
- `sc64deployer.exe` (must be placed in this directory)

## Setup

1. Download the latest `sc64deployer` release from the [SummerCart64 releases page](https://github.com/Polprzewodnikowy/SummerCart64/releases)
2. Extract `sc64deployer.exe` and place it in this directory (same folder as `sc64manager.py`)
3. The `.exe` is ignored by git, so you'll need to do this manually

## Directory Structure

```
sc64-deployer-windows-v2.20.2/
├── sc64manager.py      # This CLI tool
├── sc64deployer.exe    # Official SC64 deployer (you must add this)
├── roms/               # Put your ROM files here
│   ├── Game1.z64
│   ├── Game2.n64
│   └── ...
├── menu_versions/      # Put SC64 menu files here for updates
│   ├── sc64menu-v1.0.z64
│   └── ...
├── menu_music/         # Put MP3 files here for menu background music
│   └── background.mp3
└── README.md
```

## Usage

### Interactive Menu

Run without arguments for a menu-driven interface:

```bash
python sc64manager.py
```

The interactive menu provides these options:

1. Show Status
2. List Local ROMs
3. List Cart Contents
4. Compare (show what's missing on cart)
5. Upload ROMs to Cart
6. Quick Upload
7. Update SC64 Menu
8. Set Menu Background Music
9. Sync RTC Clock
10. Browse SD Card
11. Exit

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `status` | `s` | Show device connection and SD card status |
| `local` | `l` | List all ROMs in your local `roms/` folder |
| `cart` | `c` | List all ROMs on the SD card |
| `compare` | `d` | Show which local ROMs are missing from the cart |
| `upload` | `u` | Interactive upload - select ROMs and destination |
| `quick` | `q` | Quick upload to SD card root |
| `menu` | `m` | Update SC64 menu on cart |
| `music` | `bgm` | Set menu background music |
| `rtc` | `clock` | Sync RTC clock with system time |
| `browse` | `sd` | Browse SD card contents |
| `--help` | `-h` | Show help message |

### Examples

```bash
# Check if your SC64 is connected
python sc64manager.py status

# See what ROMs you have locally
python sc64manager.py local

# See what's on your cart
python sc64manager.py cart

# Find ROMs you haven't uploaded yet
python sc64manager.py compare

# Upload new ROMs to cart
python sc64manager.py upload

# Update the SC64 menu
python sc64manager.py menu

# Sync the RTC clock
python sc64manager.py rtc
```

## Features

### Update SC64 Menu

Update the SC64 menu firmware on your cart:

1. Place menu `.z64`, `.n64`, or `.v64` files in the `menu_versions/` folder
2. Run `python sc64manager.py menu` or select option 7 from the interactive menu
3. Select a menu version from the paginated list (9 items per page, use N/P to navigate)
4. The current menu is automatically backed up with a timestamp before updating

### Menu Background Music

Set custom background music for the SC64 menu (requires [custom SC64 menu by TheLeggett](https://github.com/TheLeggett/N64FlashcartMenu)):

1. Place MP3 files in the `menu_music/` folder
2. Run `python sc64manager.py music` or select option 8 from the interactive menu
3. Select an MP3 file or choose to remove existing music

### Sync RTC Clock

Synchronize the SC64's real-time clock with your PC's system time:

```bash
python sc64manager.py rtc
```

### Browse SD Card

Interactive browser for navigating and viewing SD card contents:

```bash
python sc64manager.py browse
```

## Important: SD Card Access

The SC64's SD card is only accessible when your **N64 is powered ON**.

If you see "SD card: Not initialized", turn on your N64 and try again.

## Uploading ROMs

When using `upload` or `quick`:

1. The tool shows ROMs not yet on the cart
2. Select ROMs by number (e.g., `1,3,5`) or type `all`
3. Choose destination folder (root `/` or custom path like `/games`)
4. ROMs are uploaded one at a time with progress shown

## Supported ROM Formats

- `.z64` - Big-endian (native N64 format)
- `.n64` - Little-endian
- `.v64` - Byte-swapped

## Troubleshooting

### "Device: NOT CONNECTED"
- Check USB cable connection
- Try a different USB port
- Ensure SC64 is properly seated in the N64 cartridge slot

### "SD card: Not initialized"
- Power ON your N64 console
- Wait a few seconds for the menu to boot
- Try the command again

### Upload fails
- Ensure you have enough space on the SD card
- Check that the N64 is still powered on
- Try uploading to the root directory `/`

### "sc64deployer.exe not found"
- Download `sc64deployer.exe` from the [SummerCart64 releases](https://github.com/Polprzewodnikowy/SummerCart64/releases)
- Place it in the same directory as `sc64manager.py`

## Credits

- [SummerCart64](https://github.com/Polprzewodnikowy/SummerCart64) by Polprzewodnikowy
- [N64FlashcartMenu](https://github.com/Polprzewodnikowy/N64FlashcartMenu) (sc64menu.n64)
