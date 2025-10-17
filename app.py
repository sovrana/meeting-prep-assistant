#!/usr/bin/env python3
"""
Flask web application for viewing meeting preparation calls.
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import DatabaseClient
from vapi_client import VapiClient
from claude_client import ClaudeClient
import config
from datetime import datetime
import markdown
import threading
import os

app = Flask(__name__)
db = DatabaseClient(config.DATABASE_PATH)
vapi = VapiClient(config.VAPI_API_KEY, config.VAPI_PHONE_NUMBER_ID)
claude = ClaudeClient(config.ANTHROPIC_API_KEY)

# Store call status in memory (in production, use Redis or similar)
call_status_cache = {}


@app.route('/')
def index():
    """Home page showing all calls."""
    calls = db.get_all_calls(limit=100)
    stats = db.get_stats()
    return render_template('index.html', calls=calls, stats=stats)


@app.route('/call/<int:call_id>')
def view_call(call_id):
    """View a specific call details."""
    call = db.get_call_by_id(call_id)
    if not call:
        return "Call not found", 404

    # Parse timestamp
    call['call_timestamp_formatted'] = datetime.fromisoformat(
        call['call_timestamp']
    ).strftime('%B %d, %Y at %I:%M %p')

    return render_template('call_detail.html', call=call)


@app.route('/search')
def search():
    """Search calls."""
    query = request.args.get('q', '')
    if query:
        calls = db.search_calls(query)
    else:
        calls = []
    return render_template('search.html', calls=calls, query=query)


@app.route('/api/calls')
def api_calls():
    """API endpoint for calls list."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    calls = db.get_all_calls(limit=limit, offset=offset)
    return jsonify(calls)


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    stats = db.get_stats()
    return jsonify(stats)


@app.route('/new-call', methods=['POST'])
def new_call():
    """Preview call before making it."""
    attendee_name = request.form.get('attendee_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    meeting_description = request.form.get('meeting_description', '').strip()

    if not all([attendee_name, phone_number, meeting_description]):
        return "Missing required fields", 400

    return render_template('call_preview.html',
                          attendee_name=attendee_name,
                          phone_number=phone_number,
                          meeting_description=meeting_description)


@app.route('/make-call', methods=['POST'])
def make_call():
    """Initiate the actual call."""
    attendee_name = request.form.get('attendee_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    meeting_description = request.form.get('meeting_description', '').strip()

    if not all([attendee_name, phone_number, meeting_description]):
        return "Missing required fields", 400

    try:
        # Initiate the call
        call_id = vapi.make_call(
            phone_number=phone_number,
            attendee_name=attendee_name,
            meeting_description=meeting_description
        )

        # Initialize status
        call_status_cache[call_id] = {
            'status': 'initiated',
            'attendee_name': attendee_name,
            'phone_number': phone_number,
            'meeting_description': meeting_description,
            'db_id': None
        }

        # Start background thread to monitor call and process results
        thread = threading.Thread(
            target=process_call_async,
            args=(call_id, attendee_name, phone_number, meeting_description)
        )
        thread.daemon = True
        thread.start()

        # Return progress page with placeholder db_id
        return render_template('call_progress.html',
                             call_id=call_id,
                             attendee_name=attendee_name,
                             phone_number=phone_number,
                             db_id='null')

    except Exception as e:
        return f"Error initiating call: {str(e)}", 500


@app.route('/api/call-status/<call_id>')
def get_call_status(call_id):
    """Get current status of a call."""
    if call_id in call_status_cache:
        return jsonify(call_status_cache[call_id])
    else:
        return jsonify({'status': 'unknown', 'error': 'Call not found'}), 404


def process_call_async(call_id, attendee_name, phone_number, meeting_description):
    """Background task to monitor call and process results."""
    try:
        # Update status
        call_status_cache[call_id]['status'] = 'in_progress'

        # Wait for call to complete
        success, call_data = vapi.wait_for_call_completion(call_id, poll_interval=5, timeout=300)

        if not success:
            call_status_cache[call_id]['status'] = 'failed'
            call_status_cache[call_id]['error'] = f"Call failed: {call_data.get('status') if call_data else 'Unknown'}"
            return

        # Get transcript
        transcript = vapi.get_transcript(call_id)
        if not transcript:
            call_status_cache[call_id]['status'] = 'failed'
            call_status_cache[call_id]['error'] = 'Could not retrieve transcript'
            return

        # Generate summary
        result = claude.summarize_transcript(
            transcript=transcript,
            attendee_name=attendee_name,
            meeting_description=meeting_description
        )
        summary = result['summary']

        # Save to database
        timestamp = datetime.now()

        # Save markdown file
        os.makedirs('meeting-notes', exist_ok=True)
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        safe_name = attendee_name.replace(' ', '_').replace('/', '_')
        filepath = f"meeting-notes/{timestamp_str}_{safe_name}.md"

        report = claude.format_full_report(
            attendee_name=attendee_name,
            phone_number=phone_number,
            meeting_description=meeting_description,
            transcript=transcript,
            summary=summary,
            timestamp=timestamp.isoformat()
        )

        with open(filepath, 'w') as f:
            f.write(report)

        # Save to database
        db_id = db.save_call(
            call_id=call_id,
            attendee_name=attendee_name,
            phone_number=phone_number,
            meeting_description=meeting_description,
            call_timestamp=timestamp,
            call_status=call_data.get('status', 'completed'),
            transcript=transcript,
            summary=summary,
            report_file_path=filepath
        )

        # Update status
        call_status_cache[call_id]['status'] = 'completed'
        call_status_cache[call_id]['db_id'] = db_id

    except Exception as e:
        call_status_cache[call_id]['status'] = 'error'
        call_status_cache[call_id]['error'] = str(e)


@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown to HTML."""
    return markdown.markdown(text, extensions=['fenced_code', 'tables'])


@app.template_filter('datetime')
def datetime_filter(timestamp_str):
    """Format datetime string."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return timestamp_str


@app.template_filter('date')
def date_filter(timestamp_str):
    """Format date string."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%B %d, %Y')
    except:
        return timestamp_str


@app.template_filter('time')
def time_filter(timestamp_str):
    """Format time string."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%I:%M %p')
    except:
        return timestamp_str


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("MEETING PREP ASSISTANT - WEB INTERFACE")
    print("=" * 80)
    print("\nStarting web server...")
    print("Open your browser and go to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
