from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
from pytube import YouTube
# Function to get available transcripts in different languages
def get_available_languages(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        return [(transcript.language, transcript.language_code) for transcript in transcript_list]
    except CouldNotRetrieveTranscript:
        return []
    
# Function to extract video ID from a YouTube URL
def get_video_id(url):
    if 'watch?v=' in url:
        return url.split('watch?v=')[-1]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[-1]
    else:
        return None



# Function to extract transcription based on the chosen language
def extract_transcription(video_id, language_code):
    try:
        # Get transcript with timeframes
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])

        # Generate plain transcription (concatenated text)
        plain_transcription = " ".join([entry['text'] for entry in transcript])

        # Generate transcription with timeframes
        transcript_with_times = [
            {
                'text': entry['text'],
                'start': entry['start'],
                'duration': entry['duration']
            }
            for entry in transcript
        ]
        
        # Return both plain transcription and transcription with timeframes
        return plain_transcription, transcript_with_times

    except NoTranscriptFound:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[f'a.{language_code}'])

            plain_transcription = " ".join([entry['text'] for entry in transcript])
            transcript_with_times = [
                {
                    'text': entry['text'],
                    'start': entry['start'],
                    'duration': entry['duration']
                }
                for entry in transcript
            ]
            return plain_transcription, transcript_with_times
        except (NoTranscriptFound, TranscriptsDisabled):
            return "No captions or transcripts available in the selected language.", []
    except TranscriptsDisabled:
        return "Transcriptions are disabled for this video.", []

# Function to get video details using pytube
def get_video_details(video_url):
    try:
        # Initialize the YouTube object
        yt = YouTube(video_url)
        
        # Extract video details
        title = yt.title
        description = yt.description
        channel_name = yt.author

        return {
            'title': title,
            'description': description,
            'channel_name': channel_name
        }
    except Exception as e:
        return {
            'title': 'Error retrieving title',
            'description': 'Error retrieving description',
            'channel_name': f'Error retrieving channel name: {e}'
        }