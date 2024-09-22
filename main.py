import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import yaml
from youtube_details import get_video_id, get_available_languages, extract_transcription, get_video_details

# Set page configuration to use wide mode
st.set_page_config(page_title="YouTube Video Processor", layout="wide")

# Apply custom CSS to adjust column widths and scrolling
st.markdown(
    """
    <style>
    /* Custom CSS to make columns 40% and 60% */
    div.block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-width: 100% !important;
    }
    .stColumn:nth-child(1) {
        flex: 0.4;
    }
    .stColumn:nth-child(2) {
        flex: 0.6;
    }
    .message { margin-bottom: 10px; display: flex; align-items: flex-start; gap: 10px; }
    .user-message, .bot-message { padding: 10px 15px; border-radius: 15px; max-width: 80%; word-wrap: break-word; font-size: 16px; }
    .user-message { background-color: #007bff; color: white; margin-left: auto; text-align: right; }
    .bot-message { margin-top: 15px; background-color: #f1f0f0; color: black; text-align: left; margin-bottom: 15px; }
    .bot-avatar { margin-top: 15px; width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; }
    .bot-container { display: flex; align-items: top; gap: 10px; }
    .user-container { display: flex; justify-content: flex-end; }
    .chat-container { max-height: 400px; overflow-y: auto; margin-bottom: 10px; }
    </style>
    """, 
    unsafe_allow_html=True
)

# Initialize session state variables if they don't exist
if 'video_url' not in st.session_state:
    st.session_state.video_url = ""
if 'transcription' not in st.session_state:
    st.session_state.transcription = None
if 'chat_sessions' not in st.session_state:
    st.session_state.chat_sessions = []
if 'embed_url' not in st.session_state:
    st.session_state.embed_url = ""

# Two-column layout: Left for video input, Right for chatbot conversation
col1, col2 = st.columns([0.3, 0.7])

# LEFT COLUMN: YouTube Video Input
with col1:
    st.markdown("### YouTube Video Processor")

    # Container to display video or placeholder image
    video_container = st.empty()
    
    # Display the video if available, otherwise show a placeholder
    if st.session_state.embed_url:
        video_container.video(st.session_state.embed_url)
    else:
        placeholder_image_url = "https://via.placeholder.com/480x300.png?text=Video+will+appear+here"
        video_container.image(placeholder_image_url)

    # Input field for YouTube URL
    st.session_state.video_url = st.text_input("Enter YouTube Video URL", st.session_state.video_url)

    # "Process" button to process video URL and fetch transcription
    process_button = st.button("Process")

    if process_button and st.session_state.video_url:
        # Extract video ID
        video_id = get_video_id(st.session_state.video_url)
        if video_id:
            try:
                # Display the video using the embed link
                st.session_state.embed_url = f"https://www.youtube.com/embed/{video_id}"
                video_container.video(st.session_state.embed_url)

                # Fetch available languages for the video
                languages = get_available_languages(video_id)
                if languages:
                    st.session_state.transcription, transcription_with_timeframes = extract_transcription(video_id, languages[0][1])

                    if st.session_state.transcription:
                        st.success("Video processed successfully!")
                    else:
                        st.error("Some error occurred; this video can't be processed.")
                else:
                    st.error("Some error occurred; this video can't be processed.")
            except Exception as e:
                st.error(f"Error processing video: {e}")
        else:
            st.error("Invalid YouTube URL")

# RIGHT COLUMN: Chatbot conversation (disabled until video is processed)
with col2:
    with open('config.yaml') as config_file:
        config = yaml.safe_load(config_file)
        os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]
    llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)

    st.markdown("### Youtube-RAG")
    chat_container = st.container(height=450)
    if st.session_state.transcription:
        # User prompt
        # Display conversation history in a scrollable container
        
        prompt = st.chat_input("Ask something about the video", key="unique_chat_input_key")
        
        if prompt:
            system_message = f"""
            You have access to the transcription of a YouTube video. Here is a snippet of the transcription:

            Transcription: {st.session_state.transcription}

            You should assist the user by providing answers to their specific questions based on the content of the video transcription. Only share relevant parts of the transcription in response to their queries. 

            If the user asks about something unrelated to the video, respond naturally with a friendly and conversational tone.
            """

            ai_response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=prompt)
            ])
            # Store the chat in session state
            st.session_state.chat_sessions.append({
                'input': prompt,
                'response': ai_response.content
            })
           
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            if st.session_state.chat_sessions:
                for chat in st.session_state.chat_sessions:
                    st.markdown(f'<div class="user-container"><div class="user-message">{chat["input"]}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bot-container"><div class="bot-message">{chat["response"]}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("The chatbot will be available once you process a video.")
