# Changelog

## [Unreleased] - 2026-01-29

### Added (Latest Update)

- **Detached Mode Execution**
  - Applications now run in background with `nohup`
  - Logs automatically saved to `./output/` directory
  - PID files created for process management
  - Automatic log tailing after startup
  - Graceful shutdown support via PID files

### Added
- **New Docling + GutenOCR Combined UI** (`src/docling_gradio_ui.py`)
  - Dedicated web interface for advanced document processing
  - Runs on port 7861 (separate from standard UI on 7860)
  - Features:
    - Combined processor initialization with Docling and GutenOCR
    - Document structure extraction
    - Table detection and extraction
    - Multi-format support (PDF, DOCX, PPTX, images, HTML, Markdown)
    - Three processing modes: Combined, Docling Only, GutenOCR Only
    - Comprehensive help system
  - Tabs:
    - Setup: Processor configuration and capabilities display
    - Single Document: Individual document processing with options
    - Batch Processing: Directory-based document processing
    - Help: Complete usage guide and troubleshooting

- **New Start Script Mode**
  - Added `--mode docling-ui` option to start the new combined UI
  - Usage: `./scripts/start.sh --mode docling-ui`
  - Supports `--cpu` and `--model` flags

### Updated

#### Documentation
- **README.md**
  - Added Docling + GutenOCR UI section in Quick Start
  - Updated features list with dual web interfaces
  - Added detailed usage instructions for the new UI
  - Updated project structure to include new component
  - Added Python API examples for combined processing

- **docs/ARCHITECTURE.md**
  - Updated system architecture diagram with dual UI ports
  - Added detailed section for Docling + GutenOCR UI component
  - Enhanced Combined Processor documentation
  - Added new data flow diagram for document processing
  - Updated component descriptions with processing modes

- **docs/DEPLOYMENT.md**
  - Added deployment instructions for Docling UI
  - Updated application URLs section
  - Added examples for both UIs in local deployment

- **docs/FLOWCHARTS.md**
  - Added comprehensive Docling UI Processing Flow diagram
  - Updated Application Startup Flow with new mode
  - Enhanced flowcharts with detailed processing steps
  - Added processing mode decision trees

#### Scripts
- **scripts/start.sh**
  - Added `docling-ui` mode support
  - Updated help text to include new mode
  - Configured port 7861 for Docling UI
  - **Detached mode execution:**
    - Applications run in background with `nohup`
    - Logs saved to `./output/[app]_[timestamp].log`
    - PID files saved to `./output/[app].pid`
    - Automatic log tailing with `tail -f`
    - Ctrl+C stops log viewing but app continues running

- **scripts/stop.sh**
  - Enhanced to use PID files for graceful shutdown
  - Stops processes by reading PID files
  - Fallback to process search if PID files missing
  - Cleans up PID files after stopping

### Technical Details

#### New Files
- `src/docling_gradio_ui.py` (437 lines)
  - DoclingGutenOCRUI class with full UI implementation
  - Integration with docling_gutenocr_combined.py
  - Gradio-based interface with 4 tabs
  - Progress tracking and error handling
  - JSON output with metadata

#### Modified Files
- `scripts/start.sh` - Added docling-ui mode
- `README.md` - Comprehensive updates
- `docs/ARCHITECTURE.md` - Architecture updates
- `docs/DEPLOYMENT.md` - Deployment updates
- `docs/FLOWCHARTS.md` - New flowcharts

### Features Comparison

| Feature | Standard UI (7860) | Docling UI (7861) |
|---------|-------------------|-------------------|
| OCR Processing | ✅ | ✅ |
| Document Structure | ❌ | ✅ |
| Table Extraction | ❌ | ✅ |
| PDF Support | ✅ | ✅ |
| DOCX/PPTX Support | ❌ | ✅ |
| HTML/Markdown | ❌ | ✅ |
| Processing Modes | Single | Combined/Docling/GutenOCR |
| Batch Processing | ✅ | ✅ |

### Usage Examples

#### Start Standard UI (Detached Mode)
```bash
./scripts/start.sh --mode gradio
# Application runs in background
# Logs: ./output/gradio_ui_[timestamp].log
# PID: ./output/gradio_ui.pid
# Access at http://localhost:7860
# Press Ctrl+C to stop viewing logs (app continues)
```

#### Start Docling UI (Detached Mode)
```bash
./scripts/start.sh --mode docling-ui
# Application runs in background
# Logs: ./output/docling_ui_[timestamp].log
# PID: ./output/docling_ui.pid
# Access at http://localhost:7861
# Press Ctrl+C to stop viewing logs (app continues)
```

#### Stop Applications
```bash
# Stop all local processes
./scripts/stop.sh --mode local

# Stop specific app by removing PID file and killing process
rm ./output/gradio_ui.pid
./scripts/stop.sh --mode local
```

#### View Logs
```bash
# View latest Gradio UI logs
tail -f ./output/gradio_ui_*.log

# View latest Docling UI logs
tail -f ./output/docling_ui_*.log
```

### Testing
- ✅ Python syntax validation passed
- ✅ Code structure verification passed
- ✅ Start script help output verified
- ✅ Import structure validated
- ⚠️ Full runtime testing requires dependencies installation

### Notes
- Both UIs can run simultaneously on different ports
- Applications run in detached mode (background)
- Logs are automatically saved to `./output/` directory
- PID files enable graceful shutdown
- Press Ctrl+C to stop viewing logs without stopping the app
- Use `./scripts/stop.sh --mode local` to stop all applications
- Docling UI requires `docling` package for full functionality
- Falls back to GutenOCR-only mode if Docling is unavailable
- All existing functionality remains unchanged

### Breaking Changes
None - This is a purely additive update

### Migration Guide
No migration needed. Existing users can continue using the standard UI, while new users can choose the appropriate UI for their needs.

---

**Made with Bob** 🤖