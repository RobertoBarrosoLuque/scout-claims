![Scout Demo](assets/fireworks_logo.png)


# Scout | AI Claims Assistant

> **Automated Insurance Claims Processing powered by Fireworks AI**

Scout is an intelligent claims processing assistant that uses advanced AI to analyze vehicle damage, process incident descriptions, and generate comprehensive claim reports. It showcases cutting-edge AI capabilities including computer vision, speech transcription, natural language processing, and autonomous function calling.

## Key Features

- **Automated Damage Analysis**: AI-powered computer vision analyzes damage photos
- **Real-time Speech Transcription**: Live audio processing with Fireworks AI
- **Intelligent Incident Processing**: Advanced NLP extracts structured claim data
- **Autonomous Function Calling**: AI automatically gathers additional context (weather, driver records)
- **Professional PDF Generation**: Comprehensive claim reports with all evidence
- **Real-time Processing**: Sub-30 second end-to-end claim processing

## High-Level Architecture

### Core AI Components (Powered by Fireworks AI)

#### 1. Vision Analysis Module (`image_analysis.py`)
- **Function**: Analyzes damage photos to determine severity, location, and repair estimates
- **Output**: Structured JSON with damage classification and cost estimates

#### 2. Speech Transcription Service (`transcription.py`)
- **Function**: Converts live audio to text with 500ms updates
- **Features**: Automatic speech recognition with live feedback

#### 3. Incident Processing Engine (`incident_processing.py`)
- **Function**: Extracts structured claim data from transcribed incident descriptions
- **Advanced Feature**: **Autonomous Function Calling** (see details below)

#### 4. Report Generation System (`claim_processing.py`)
- **Technology**: AI-driven professional document generation
- **Output**: Comprehensive PDF reports with evidence, analysis, and recommendations
- **Features**: Professional formatting, appendices, and legal disclaimers

### Autonomous Function Calling System
One of Scout's most advanced features is its **autonomous function calling capability**. The AI automatically determines when additional context would be helpful and calls external functions without human intervention.

#### How It Works:

1. **Analysis Phase**: AI analyzes the incident transcript
2. **Decision Making**: Determines which external data would improve assessment accuracy
3. **Autonomous Execution**: Automatically calls relevant functions
4. **Context Integration**: Incorporates results into final claim analysis

#### Available Functions:

| Function | Purpose | Data Retrieved |
|----------|---------|----------------|
| `weather_lookup` | Get weather conditions for incident date/location | Temperature, visibility, precipitation, conditions |
| `driver_record_check` | Verify other party's driving record | License status, insurance status, violation history, risk assessment |

#### Example Function Call Flow:

```
User describes incident → AI extracts date/location → AI calls weather_lookup() →
AI finds other driver name → AI calls driver_record_check() →
AI incorporates weather + driver data into fault assessment
```

This autonomous approach means **no manual intervention required** - the AI intelligently gathers the exact context needed for each unique claim.

## Setup Instructions

### Prerequisites

- Python 3.11+
- Fireworks AI API key ([Get one here](https://fireworks.ai))
- OpenSSL (for HTTPS/microphone access)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd scout-claims-assistant
   ```

2. **Run automated setup**
   ```bash
   make setup
   ```
   This will:
   - Install `uv` package manager
   - Create Python 3.11 virtual environment
   - Install all dependencies
   - Generate SSL certificates for HTTPS

3. **Set your API key**: add FIREWORKS_API_KEY to .env

4. **Launch the application**
   ```bash
   make run
   ```

5. **Open in browser**
   ```
   https://localhost:7860
   ```
   > **Note**: Accept the security warning for self-signed certificates

## How to Use

### Step 1: Upload Damage Photos
- Upload clear photos of vehicle damage
- AI analyzes damage severity, location, and repair costs
- Results appear in real-time

### Step 2: Record Incident Description
- Click the microphone to start recording
- Describe the incident including:
  - **When & Where**: Date, time, location
  - **Who**: Other parties, witnesses
  - **What**: How the accident happened
  - **Injuries**: Any medical concerns
- Watch live transcription appear as you speak

### Step 3: Generate Professional Report
- AI processes all information + calls external functions
- Generates comprehensive PDF claim report
- Download or submit directly

**Powered by Fireworks AI** | **Built for intelligent claims processing**
