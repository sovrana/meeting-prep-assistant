# Meeting Preparation Assistant

An AI-powered CLI tool that makes automated phone calls to meeting attendees to gather preparation information. The assistant "Alex" calls attendees, asks key questions, and generates comprehensive meeting preparation reports.

## Features

- **Automated outbound calls** via Vapi API
- **Professional AI assistant** that introduces itself and asks permission
- **Gathers structured meeting preparation information**
- **Real-time call status monitoring**
- **Automatic transcript retrieval**
- **AI-powered summaries** using Claude
- **Database storage** for all calls (SQLite)
- **Beautiful web interface** to view all calls, summaries, and transcripts
- **Search functionality** to find past calls
- Saves detailed markdown reports for each call

## Prerequisites

- Python 3.8 or higher
- Vapi API account and API key ([Sign up here](https://vapi.ai))
- Anthropic API key ([Get one here](https://console.anthropic.com))

## Installation

### 1. Clone or Download the Repository

```bash
cd /path/to/meeting-prep-assistant
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys:

```
VAPI_API_KEY=your_vapi_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Getting Your API Keys:**

- **Vapi API Key**:
  1. Go to [vapi.ai](https://vapi.ai)
  2. Sign up or log in
  3. Navigate to Settings > API Keys
  4. Create a new API key

- **Anthropic API Key**:
  1. Go to [console.anthropic.com](https://console.anthropic.com)
  2. Sign up or log in
  3. Navigate to API Keys
  4. Create a new API key

### 5. Make the Script Executable (Optional)

```bash
chmod +x prep-meeting.py
```

## Usage

### Basic Command

```bash
python prep-meeting.py "John Smith" "+1-555-0123" "Q4 Planning Meeting - budget discussion"
```

### Arguments

1. **Name** (required): The name of the person to call
2. **Phone** (required): Phone number in E.164 format (e.g., `+1-555-0123`)
3. **Meeting** (required): Description of the meeting

### Example

```bash
python prep-meeting.py "Sarah Johnson" "+1-415-555-7890" "Product Roadmap Review"
```

## Workflow

1. **Preview**: The tool shows you exactly what Alex will say to the attendee
2. **Approval**: You approve or cancel the call
3. **Call Initiation**: The system initiates the outbound call via Vapi
4. **AI Introduction**: Alex introduces itself and asks permission to proceed
5. **Questions**: If approved, Alex asks three key questions:
   - What are your main goals for this meeting?
   - Are there any specific topics or questions you want to cover?
   - Do you have any current pain points or challenges relevant to this meeting?
6. **Monitoring**: The tool monitors the call in real-time
7. **Transcript Retrieval**: Once complete, the transcript is retrieved
8. **Summary Generation**: Claude analyzes the transcript and creates a structured summary
9. **Report Saving**: A comprehensive markdown report is saved to `meeting-notes/`
10. **Database Storage**: Call data is automatically saved to the database
11. **Web Access**: View all your calls at http://localhost:5001

## Output

### Database Storage
All calls are automatically saved to a SQLite database (`meeting_prep.db`) with:
- Call metadata (date, attendee, phone, meeting description)
- Full transcript
- AI-generated summary
- Call status and timestamps

### Markdown Reports
Reports are also saved to the `meeting-notes/` directory:
```
meeting-notes/20241017_143022_John_Smith.md
```

Each report includes:
- Call metadata (date, attendee, phone, meeting description)
- Executive summary with key points
- Main goals identified
- Topics to cover
- Pain points mentioned
- Action items for preparation
- Full transcript

## Web Interface

View all your calls in a beautiful, easy-to-use web interface:

### Starting the Web Server

```bash
# Option 1: Using the startup script
./start-web.sh

# Option 2: Manual start
source venv/bin/activate
python app.py
```

Then open your browser to: **http://localhost:5001**

### Features
- **Dashboard**: View all calls with statistics (total calls, successful calls, recent activity)
- **Call Details**: Click any call to see the full transcript and summary
- **Search**: Find specific calls by attendee name or meeting description
- **Clean Design**: Modern, responsive interface that works on all devices

## What Alex Says

Alex uses a professional, polite tone:

**Introduction:**
> "Hi [name], this is Alex, Marc's meeting preparation assistant. I'm an AI agent calling to help Marc prepare for your [meeting description]. Do you have 2-3 minutes for a couple of quick questions? You can end this call anytime if you're not comfortable."

**Questions:**
1. What are your main goals for this meeting?
2. Are there any specific topics or questions you want to cover?
3. Do you have any current pain points or challenges relevant to this meeting?

**Closing:**
> "Thanks so much for your time. Marc will review this before the meeting. Have a great day!"

## Troubleshooting

### "Missing required environment variables"

Make sure you've created a `.env` file with both `VAPI_API_KEY` and `ANTHROPIC_API_KEY`.

### "Failed to initiate call"

- Check that your Vapi API key is valid
- Ensure the phone number is in E.164 format (+country code + number)
- Verify your Vapi account has sufficient credits

### "Could not retrieve transcript"

- Wait a few moments and the transcript may still be processing
- Check the Vapi dashboard for call details
- Ensure the call completed successfully

### "Failed to generate summary"

- Verify your Anthropic API key is valid
- Check that you have available credits
- Ensure the transcript was retrieved successfully

## Project Structure

```
meeting-prep-assistant/
├── prep-meeting.py      # Main CLI script
├── app.py              # Flask web application
├── config.py           # Configuration and environment variables
├── database.py         # Database client (SQLite)
├── vapi_client.py      # Vapi API client
├── claude_client.py    # Claude API client
├── requirements.txt    # Python dependencies
├── start-web.sh        # Web server startup script
├── templates/          # HTML templates for web interface
│   ├── base.html       # Base template
│   ├── index.html      # Dashboard page
│   ├── call_detail.html # Call detail page
│   └── search.html     # Search page
├── .env.example        # Environment variable template
├── .env                # Your API keys (not in git)
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── meeting_prep.db     # SQLite database (created automatically)
└── meeting-notes/      # Markdown reports directory
```

## Configuration Options

You can customize the assistant behavior by editing `vapi_client.py`:

- **Voice**: Change the `voiceId` in the assistant configuration
- **Max Duration**: Adjust `maxDurationSeconds` (default: 300 seconds)
- **Model**: Change the AI model (default: GPT-4)
- **Temperature**: Adjust response creativity (default: 0.7)

## Privacy & Ethics

- **Transparency**: Alex always identifies itself as an AI agent
- **Consent**: Alex asks for permission before proceeding
- **Opt-out**: Attendees can end the call at any time
- **Recording Notice**: The introduction mentions the call will be recorded
- **Data Storage**: Transcripts are stored locally on your machine

## License

This project is for personal use. Please review Vapi and Anthropic's terms of service.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Vapi documentation: [docs.vapi.ai](https://docs.vapi.ai)
3. Review Anthropic documentation: [docs.anthropic.com](https://docs.anthropic.com)

## Cost Considerations

- **Vapi**: Charges per minute of call time
- **Anthropic**: Charges per token (input + output)
- Estimate: ~$0.50-1.50 per call depending on length and transcript size

Always monitor your API usage and set billing alerts!
