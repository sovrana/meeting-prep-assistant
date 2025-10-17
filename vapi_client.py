"""
Vapi API client for making outbound calls and retrieving transcripts.
"""
import requests
import time
from typing import Dict, Optional, Tuple


class VapiClient:
    """Client for interacting with Vapi API."""

    BASE_URL = "https://api.vapi.ai"

    def __init__(self, api_key: str, phone_number_id: Optional[str] = None):
        """Initialize Vapi client with API key."""
        self.api_key = api_key
        self.phone_number_id = phone_number_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_phone_numbers(self) -> list:
        """
        Get available phone numbers in your Vapi account.

        Returns:
            List of phone number objects
        """
        response = requests.get(
            f"{self.BASE_URL}/phone-number",
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get phone numbers: {response.status_code} - {response.text}")

    def create_assistant(self, meeting_description: str) -> Dict:
        """
        Create a Vapi assistant configured for meeting preparation calls.

        Args:
            meeting_description: Description of the meeting

        Returns:
            Assistant configuration dict
        """
        assistant_config = {
            "name": "Alex - Meeting Prep Assistant",
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "systemPrompt": f"""You are Alex, a polite and professional AI meeting preparation assistant working for Marc.

Your task:
1. Introduce yourself: "Hi [name], this is Alex, Marc's meeting preparation assistant. I'm an AI agent calling to help Marc prepare for your meeting about {meeting_description}. Do you have 2 minutes for a couple of quick questions? You can end this call anytime if you're not comfortable."

2. If they agree, ask these 3 questions ONE AT A TIME. IMPORTANT: Wait patiently for their COMPLETE answer before moving on:

   Question 1: "What are your main goals for this meeting?"
   - Wait for their full response. They may list multiple goals.
   - When they finish, acknowledge what you heard: "Got it, thank you."
   - If they pause briefly, wait 3-4 seconds before assuming they're done.
   - Before moving on, ask: "Is there anything else you'd like to add about your goals?"

   Question 2: "Are there any specific topics or questions you want to cover?"
   - Wait for their full response. They may list multiple topics.
   - When they finish, acknowledge: "Perfect, I've noted that."
   - If they pause, wait patiently.
   - Before moving on, ask: "Any other topics?"

   Question 3: "Do you have any current pain points or challenges relevant to this meeting?"
   - Wait for their full response. Listen patiently for all pain points.
   - When they finish, acknowledge: "Thank you for sharing that."
   - If they pause, wait 3-4 seconds.
   - Before ending, ask: "Anything else I should note?"

3. If they decline: Thank them politely and end the call.

4. If a response is unclear: Ask for clarification once, then move on if still unclear.

5. After all questions: Thank them and say "Thanks so much for your time. Marc will review this before the meeting. Have a great day!"

CRITICAL: Be patient. Do not rush to the next question. Wait for complete answers. Brief pauses are normal - wait 3-4 seconds before assuming they're done. Always confirm they're finished before moving to the next question."""
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Rachel voice - professional
            },
            "firstMessage": "Hi, is this [name]?",
            "endCallMessage": "Thank you for your time. Goodbye!",
            "endCallPhrases": ["goodbye", "end call", "hang up", "not interested"],
            "recordingEnabled": True,
            "maxDurationSeconds": 300,  # 5 minute max
        }

        response = requests.post(
            f"{self.BASE_URL}/assistant",
            headers=self.headers,
            json=assistant_config
        )

        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create assistant: {response.status_code} - {response.text}")

    def make_call(
        self,
        phone_number: str,
        attendee_name: str,
        meeting_description: str,
        assistant_id: Optional[str] = None
    ) -> str:
        """
        Initiate an outbound call.

        Args:
            phone_number: Phone number to call (E.164 format)
            attendee_name: Name of the person being called
            meeting_description: Description of the meeting
            assistant_id: Optional pre-created assistant ID

        Returns:
            Call ID
        """
        # Get phone number ID if not set
        phone_number_id = self.phone_number_id
        if not phone_number_id:
            # Try to get the first available phone number
            try:
                phone_numbers = self.get_phone_numbers()
                if phone_numbers and len(phone_numbers) > 0:
                    phone_number_id = phone_numbers[0].get('id')
                    print(f"Using phone number: {phone_numbers[0].get('number', 'N/A')}")
                else:
                    raise Exception(
                        "No phone numbers found in your Vapi account.\n"
                        "Please purchase or import a phone number at https://dashboard.vapi.ai/phone-numbers\n"
                        "Then either:\n"
                        "  1. Add VAPI_PHONE_NUMBER_ID=your_number_id to your .env file, or\n"
                        "  2. The tool will automatically use your first available number"
                    )
            except Exception as e:
                raise Exception(f"Failed to get phone number: {e}")

        # Use inline assistant configuration
        call_payload = {
            "phoneNumberId": phone_number_id,
            "assistant": {
                "model": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You are Alex, a polite and professional AI meeting preparation assistant working for Marc.

Your task:
1. Introduce yourself: "Hi {attendee_name}, this is Alex, Marc's meeting preparation assistant. I'm an AI agent calling to help Marc prepare for your meeting about {meeting_description}. Do you have 2 minutes for a couple of quick questions? You can end this call anytime if you're not comfortable."

2. If they agree, ask these 3 questions ONE AT A TIME. IMPORTANT: Wait patiently for their COMPLETE answer before moving on:

   Question 1: "What are your main goals for this meeting?"
   - Wait for their full response. They may list multiple goals.
   - When they finish, acknowledge what you heard: "Got it, thank you."
   - If they pause briefly, wait 3-4 seconds before assuming they're done.
   - Before moving on, ask: "Is there anything else you'd like to add about your goals?"

   Question 2: "Are there any specific topics or questions you want to cover?"
   - Wait for their full response. They may list multiple topics.
   - When they finish, acknowledge: "Perfect, I've noted that."
   - If they pause, wait patiently.
   - Before moving on, ask: "Any other topics?"

   Question 3: "Do you have any current pain points or challenges relevant to this meeting?"
   - Wait for their full response. Listen patiently for all pain points.
   - When they finish, acknowledge: "Thank you for sharing that."
   - If they pause, wait 3-4 seconds.
   - Before ending, ask: "Anything else I should note?"

3. If they decline: Thank them politely and end the call.

4. If a response is unclear: Ask for clarification once, then move on if still unclear.

5. After all questions: Thank them and say "Thanks so much for your time. Marc will review this before the meeting. Have a great day!"

CRITICAL: Be patient. Do not rush to the next question. Wait for complete answers. Brief pauses are normal - wait 3-4 seconds before assuming they're done. Always confirm they're finished before moving to the next question."""
                        }
                    ]
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "21m00Tcm4TlvDq8ikWAM"
                },
                "firstMessage": f"Hi, is this {attendee_name}?",
                "recordingEnabled": True,
                "endCallMessage": "Thank you for your time. Goodbye!",
                "endCallPhrases": ["goodbye", "end call", "hang up", "not interested"],
                "maxDurationSeconds": 300
            },
            "customer": {
                "number": phone_number,
                "name": attendee_name
            }
        }

        response = requests.post(
            f"{self.BASE_URL}/call/phone",
            headers=self.headers,
            json=call_payload
        )

        if response.status_code == 201:
            call_data = response.json()
            return call_data.get('id')
        else:
            raise Exception(f"Failed to initiate call: {response.status_code} - {response.text}")

    def get_call_status(self, call_id: str) -> Dict:
        """
        Get the status of a call.

        Args:
            call_id: The call ID

        Returns:
            Call status dict
        """
        response = requests.get(
            f"{self.BASE_URL}/call/{call_id}",
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get call status: {response.status_code} - {response.text}")

    def wait_for_call_completion(
        self,
        call_id: str,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Poll for call completion.

        Args:
            call_id: The call ID
            poll_interval: Seconds between polls (default: 5)
            timeout: Maximum time to wait in seconds (default: 300 = 5 minutes)

        Returns:
            Tuple of (success, call_data)
        """
        start_time = time.time()
        print(f"Waiting for call to complete (timeout: {timeout}s)...")

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print(f"\nTimeout reached after {timeout} seconds")
                return False, None

            try:
                call_data = self.get_call_status(call_id)
                status = call_data.get('status')

                print(f"\rCall status: {status} (elapsed: {int(elapsed)}s)", end='', flush=True)

                if status in ['ended', 'completed']:
                    print("\n\nCall completed!")
                    return True, call_data
                elif status in ['failed', 'busy', 'no-answer']:
                    print(f"\n\nCall failed with status: {status}")
                    return False, call_data

            except Exception as e:
                print(f"\nError polling call status: {e}")
                return False, None

            time.sleep(poll_interval)

    def get_transcript(self, call_id: str) -> Optional[str]:
        """
        Get the transcript of a completed call.

        Args:
            call_id: The call ID

        Returns:
            Transcript string or None
        """
        try:
            call_data = self.get_call_status(call_id)

            # Try to get transcript from various possible locations
            transcript = call_data.get('transcript')
            if transcript:
                return transcript

            # Check messages array
            messages = call_data.get('messages', [])
            if messages:
                # Combine all messages into a transcript
                transcript_parts = []
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    transcript_parts.append(f"{role}: {content}")
                return "\n".join(transcript_parts)

            # Check artifact for recording/transcript URL
            artifact = call_data.get('artifact')
            if artifact:
                transcript_url = artifact.get('transcriptUrl')
                if transcript_url:
                    # Fetch transcript from URL
                    resp = requests.get(transcript_url)
                    if resp.status_code == 200:
                        return resp.text

            return None

        except Exception as e:
            print(f"Error retrieving transcript: {e}")
            return None

    def get_assistant_intro(self, attendee_name: str, meeting_description: str) -> str:
        """
        Get the introduction that Alex will use.

        Args:
            attendee_name: Name of the person being called
            meeting_description: Description of the meeting

        Returns:
            Introduction text
        """
        return f"""Alex will introduce itself as follows:

"Hi {attendee_name}, this is Alex, Marc's meeting preparation assistant. I'm an AI agent calling to help Marc prepare for your meeting about {meeting_description}. Do you have 2 minutes for a couple of quick questions? You can end this call anytime if you're not comfortable."

If they agree, Alex will ask:
1. What are your main goals for this meeting?
2. Are there any specific topics or questions you want to cover?
3. Do you have any current pain points or challenges relevant to this meeting?

The call will be recorded and a transcript will be generated."""
