#!/usr/bin/env python3
"""
Meeting Preparation Assistant CLI Tool
Makes outbound calls to gather meeting preparation information.
"""
import sys
import argparse
from datetime import datetime
import os

import config
from vapi_client import VapiClient
from claude_client import ClaudeClient
from database import DatabaseClient


def get_user_approval(attendee_name: str, phone_number: str, meeting_description: str) -> bool:
    """
    Show the user what Alex will say and get approval to proceed.

    Args:
        attendee_name: Name of the person to call
        phone_number: Phone number to call
        meeting_description: Description of the meeting

    Returns:
        True if user approves, False otherwise
    """
    print("\n" + "=" * 80)
    print("MEETING PREPARATION CALL PREVIEW")
    print("=" * 80)
    print(f"\nCalling: {attendee_name}")
    print(f"Phone: {phone_number}")
    print(f"Meeting: {meeting_description}")
    print("\n" + "-" * 80)
    print("Alex will say:")
    print("-" * 80)
    print(f"""
"Hi {attendee_name}, this is Alex, Marc's meeting preparation assistant.
I'm an AI agent calling to help Marc prepare for your meeting about {meeting_description}.
Do you have 2 minutes for a couple of quick questions?
You can end this call anytime if you're not comfortable."

If they agree, Alex will ask:
  1. What are your main goals for this meeting?
  2. Are there any specific topics or questions you want to cover?
  3. Do you have any current pain points or challenges relevant to this meeting?

The call will be recorded and transcribed.
""")
    print("=" * 80)

    while True:
        response = input("\nProceed with this call? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")


def save_report(report: str, attendee_name: str, timestamp: datetime) -> str:
    """
    Save the meeting preparation report to a file.

    Args:
        report: The formatted report
        attendee_name: Name of attendee (for filename)
        timestamp: Timestamp for filename

    Returns:
        Path to saved file
    """
    # Create meeting-notes directory if it doesn't exist
    os.makedirs('meeting-notes', exist_ok=True)

    # Generate filename
    timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
    safe_name = attendee_name.replace(' ', '_').replace('/', '_')
    filename = f"meeting-notes/{timestamp_str}_{safe_name}.md"

    # Save file
    with open(filename, 'w') as f:
        f.write(report)

    return filename


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Meeting Preparation Assistant - Make calls to gather meeting info'
    )
    parser.add_argument('name', help='Name of the person to call')
    parser.add_argument('phone', help='Phone number in E.164 format (e.g., +1-555-0123)')
    parser.add_argument('meeting', help='Meeting description (e.g., "Q4 Planning Meeting")')

    args = parser.parse_args()

    # Validate configuration
    try:
        config.validate_config()
    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # Initialize clients
    vapi = VapiClient(config.VAPI_API_KEY, config.VAPI_PHONE_NUMBER_ID)
    claude = ClaudeClient(config.ANTHROPIC_API_KEY)
    db = DatabaseClient(config.DATABASE_PATH)

    # Get user approval
    if not get_user_approval(args.name, args.phone, args.meeting):
        print("\nCall cancelled by user.")
        sys.exit(0)

    print("\n" + "=" * 80)
    print("INITIATING CALL")
    print("=" * 80)

    # Make the call
    try:
        print(f"\nCalling {args.name} at {args.phone}...")
        call_id = vapi.make_call(
            phone_number=args.phone,
            attendee_name=args.name,
            meeting_description=args.meeting
        )
        print(f"Call initiated! Call ID: {call_id}")

    except Exception as e:
        print(f"\nERROR: Failed to initiate call: {e}")
        sys.exit(1)

    # Wait for call to complete
    print("\n" + "-" * 80)
    success, call_data = vapi.wait_for_call_completion(call_id)

    if not success:
        print("\nERROR: Call did not complete successfully.")
        if call_data:
            print(f"Final status: {call_data.get('status')}")
        sys.exit(1)

    # Get transcript
    print("\n" + "=" * 80)
    print("RETRIEVING TRANSCRIPT")
    print("=" * 80)

    transcript = vapi.get_transcript(call_id)

    if not transcript:
        print("\nWARNING: Could not retrieve transcript.")
        print("Call completed but transcript is not available.")
        sys.exit(1)

    print(f"\nTranscript retrieved ({len(transcript)} characters)")

    # Generate summary with Claude
    print("\n" + "=" * 80)
    print("GENERATING SUMMARY WITH CLAUDE")
    print("=" * 80)

    try:
        result = claude.summarize_transcript(
            transcript=transcript,
            attendee_name=args.name,
            meeting_description=args.meeting
        )
        summary = result['summary']
        print("\nSummary generated!")

    except Exception as e:
        print(f"\nERROR: Failed to generate summary: {e}")
        sys.exit(1)

    # Create full report
    timestamp = datetime.now()
    report = claude.format_full_report(
        attendee_name=args.name,
        phone_number=args.phone,
        meeting_description=args.meeting,
        transcript=transcript,
        summary=summary,
        timestamp=timestamp.isoformat()
    )

    # Save report
    try:
        filepath = save_report(report, args.name, timestamp)
        print("\n" + "=" * 80)
        print("REPORT SAVED")
        print("=" * 80)
        print(f"\nReport saved to: {filepath}")

        # Save to database
        print("\nSaving to database...")
        db_id = db.save_call(
            call_id=call_id,
            attendee_name=args.name,
            phone_number=args.phone,
            meeting_description=args.meeting,
            call_timestamp=timestamp,
            call_status=call_data.get('status', 'completed'),
            transcript=transcript,
            summary=summary,
            report_file_path=filepath
        )
        print(f"✓ Saved to database (ID: {db_id})")

        # Display summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\n{summary}\n")

        print("=" * 80)
        print(f"\nFull report available at: {filepath}")
        print(f"View all calls at: http://localhost:5001")

    except Exception as e:
        print(f"\nERROR: Failed to save report: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
