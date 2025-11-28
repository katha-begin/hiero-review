# Quick Start Guide

Get up and running with Hiero Review Tool in 5 minutes!

## Step 1: Launch Hiero

Use the custom launcher to start Hiero with the tool pre-configured:

**Windows:**
```batch
hiero_launcher.bat
```

**Linux/Mac:**
```bash
python hiero_launcher.py
```

## Step 2: Open the Review Tool

1. In Hiero, go to **Tools** menu
2. Click **Review Tool**
3. The main dialog will open

## Step 3: Select Your Content

1. **Project**: Select your project from the dropdown
2. **Episode**: Choose the episode (e.g., Ep01)
3. **Sequence**: Select the sequence to review (e.g., sq0010)

## Step 4: Configure Options

1. **Department**: Choose which department output to view
   - comp (compositing)
   - lighting
   - fx (effects)
   - anim (animation)

2. **Version**: Select version preference
   - Latest: Always use newest version
   - Specific: Choose a specific version number

3. **Media Type**: Choose media format
   - MOV: QuickTime movies
   - Sequence: Image sequences (EXR, DPX, etc.)

## Step 5: Build Timeline

1. Click **Build Timeline**
2. Wait for the scan to complete
3. A new timeline will be created with all shots

## Working with the Timeline

### Navigate Versions

- **Previous Version**: Click ◀ or press `[`
- **Next Version**: Click ▶ or press `]`
- **Latest Version**: Click ⏭ or press `L`

### Switch Departments

1. Select shots in the timeline
2. Right-click → **Switch Department**
3. Choose the target department

### Update All Versions

1. Click **Update Versions** in the main dialog
2. All shots will update to the selected version preference

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `[` | Previous version |
| `]` | Next version |
| `L` | Latest version |
| `Ctrl+R` | Refresh scan |
| `Ctrl+B` | Build timeline |

## Tips

1. **Use caching**: The tool caches scan results. Click "Refresh" only when files have changed.

2. **Batch operations**: Select multiple shots before switching departments or versions.

3. **Check the log**: The status log at the bottom shows progress and any errors.

4. **Save preferences**: Your last selections are remembered between sessions.

## Troubleshooting

### "No episodes found"
- Check that your project root path is correct
- Verify the folder structure matches the expected pattern (Ep##/sq####/SH####)

### "Media not found"
- Ensure media files exist in the version folders
- Check file naming conventions match the project config

### Timeline is empty
- Verify at least one shot has media in the selected department
- Check the status log for specific errors

## Next Steps

- Read the full [User Guide](README.md)
- Check the [API Reference](API.md) for scripting
- See [Installation Guide](INSTALLATION.md) for advanced setup

