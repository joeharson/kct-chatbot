import streamlit as st
import time
import os
import json
from datetime import datetime
import hashlib

# Check if vectorstore exists and initialize if needed
def check_and_initialize():
    """Check if system is properly initialized"""
    if not os.path.exists("vectorstore"):
        st.warning("⚠️ Vectorstore not found. Initializing system...")
        try:
            from scripts.query_bot import initialize_system
            initialize_system()
            st.success("✅ System initialized successfully!")
        except Exception as e:
            st.error(f"❌ Initialization failed: {e}")
            return False
    return True

def create_unique_key(text, max_length=50):
    """Create a unique key for widgets"""
    return hashlib.md5(text.encode()).hexdigest()[:max_length]

def initialize_chat_session():
    """Initialize chat session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = ""

def save_chat_history():
    """Save chat history to file"""
    if st.session_state.messages:
        chat_data = {
            "chat_id": st.session_state.chat_id,
            "timestamp": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "context": st.session_state.conversation_context
        }
        
        os.makedirs("chat_history", exist_ok=True)
        filename = f"chat_history/chat_{st.session_state.chat_id}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)

def load_chat_history(chat_id):
    """Load chat history from file"""
    filename = f"chat_history/chat_{chat_id}.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def clear_chat_history():
    """Clear current chat history"""
    st.session_state.messages = []
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.conversation_context = ""

def main():
    # Page configuration
    st.set_page_config(
        page_title="KCT InfoBot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"  # Start with sidebar collapsed
    )

    # Custom CSS for styling
    st.markdown("""
    <style>
    /* Main container styles */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .welcome-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1.5rem;
        border: 2px solid #e1e8ed;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        background: linear-gradient(to right, #f8f9fa, #ffffff);
        border: 2px solid #667eea !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #764ba2 !important;
        box-shadow: 0 4px 20px rgba(118, 75, 162, 0.2);
        transform: translateY(-2px);
    }

    /* Send button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 2rem !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Placeholder text styling */
    .stTextInput > div > div > input::placeholder {
        color: #9fa6b2;
        font-style: italic;
    }

    /* Input container layout */
    .input-container {
        display: flex;
        gap: 1rem;
        align-items: center;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        margin-bottom: 1rem;
    }
    
    /* Quick questions button */
    .quick-questions-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .css-1d391kg button {
        background: white;
        color: #764ba2;
        border-radius: 10px;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    .css-1d391kg button:hover {
        transform: translateX(5px);
        background: #f0f0f0;
    }
    
    /* User message styling - Blue theme */
    .user-message {
        background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1.5rem 0;
        margin-left: 15%;
        margin-right: 2%;
        box-shadow: 0 4px 15px rgba(33, 147, 176, 0.3);
        font-size: 16px;
        position: relative;
    }
    
    .user-message::before {
        content: '👤';
        position: absolute;
        top: -25px;
        left: 0;
        font-size: 20px;
        background: #2193b0;
        padding: 8px;
        border-radius: 50%;
        box-shadow: 0 4px 15px rgba(33, 147, 176, 0.3);
    }
    
    /* Assistant message styling - Purple theme */
    .assistant-message {
        background: linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1.5rem 0;
        margin-right: 15%;
        margin-left: 2%;
        box-shadow: 0 4px 15px rgba(142, 45, 226, 0.3);
        font-size: 16px;
        position: relative;
    }
    
    .assistant-message::before {
        content: '🤖';
        position: absolute;
        top: -25px;
        right: 0;
        font-size: 20px;
        background: #8E2DE2;
        padding: 8px;
        border-radius: 50%;
        box-shadow: 0 4px 15px rgba(142, 45, 226, 0.3);
    }
    
    /* Message header styling */
    .user-header {
        background: rgba(33, 147, 176, 0.9);
        color: white;
        padding: 8px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        font-size: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .assistant-header {
        background: rgba(142, 45, 226, 0.9);
        color: white;
        padding: 8px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        font-size: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .message-content {
        line-height: 1.6;
        font-size: 16px;
        padding: 10px 5px;
    }
    
    .timestamp {
        font-size: 12px;
        opacity: 0.9;
        font-style: italic;
    }
    
    /* Chat container styling */
    .chat-container {
        height: 600px;
        overflow-y: auto;
        padding: 2rem;
        border-radius: 15px;
        background: #f8f9fa;
        border: 2px solid #e1e8ed;
        margin-top: 2rem;
    }
    
    /* Scrollbar styling */
    .chat-container::-webkit-scrollbar {
        width: 10px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #2193b0 0%, #8E2DE2 100%);
        border-radius: 10px;
    }
    
    /* Bottom input container */
    .bottom-input-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        background: white;
        padding: 15px;
        border-radius: 20px;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
        z-index: 100;
        border: 2px solid #e1e8ed;
    }
    
    /* Adjust chat container height to accommodate fixed input */
    .adjusted-chat-container {
        height: calc(600px - 100px);
        overflow-y: auto;
        padding: 2rem;
        border-radius: 15px;
        background: #f8f9fa;
        border: 2px solid #e1e8ed;
        margin-top: 2rem;
        margin-bottom: 100px; /* Space for fixed input */
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state for sidebar visibility
    if 'show_sidebar' not in st.session_state:
        st.session_state.show_sidebar = False

    # Quick Questions Button (top right corner)
    col1, col2, col3 = st.columns([1, 1, 0.1])
    with col3:
        if st.button('💡', help='Quick Questions'):
            st.session_state.show_sidebar = not st.session_state.show_sidebar
            st.rerun()

    # Sidebar with quick questions
    if st.session_state.show_sidebar:
        with st.sidebar:
            st.markdown("### 💡 Quick Questions")
            
            # Quick Questions buttons
            questions = [
                "What courses does KCT offer?",
                "Tell me about admissions",
                "What are the facilities?",
                "How is the placement record?",
                "What about hostel facilities?",
                "Tell me about faculty",
                "What are the fees?",
                "Campus life at KCT"
            ]
            
            for question in questions:
                if st.button(question, key=f"quick_{question}"):
                    # Process the question
                    if "messages" not in st.session_state:
                        st.session_state.messages = []
                    
                    user_message = {
                        "role": "user",
                        "content": question,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                    st.session_state.messages.append(user_message)
                    
                    try:
                        from scripts.query_bot import query_knowledge_base
                        response = query_knowledge_base(question)
                        
                        bot_message = {
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                        st.session_state.messages.append(bot_message)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Clear chat button at bottom of sidebar
            if st.button("🗑️ Clear Chat", type="primary"):
                st.session_state.messages = []
                st.rerun()

    # Main chat interface
    st.markdown("""
    <div class="main-header">
        <h1>🤖 KCT InfoBot</h1>
        <p>Your AI-Powered Assistant for Kumaraguru College of Technology</p>
    </div>
    """, unsafe_allow_html=True)

    # Welcome message
    st.markdown("""
    <div class="welcome-section">
        <h4>👋 Welcome to KCT InfoBot!</h4>
        <p>Ask me anything about Kumaraguru College of Technology</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages in a single container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; color: #666; padding: 2rem;">
                💬 Your conversation will appear here...
            </div>
            """, unsafe_allow_html=True)
        else:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <div class="user-header">
                            <span>YOU ASKED</span>
                            <span class="timestamp">🕒 {message['timestamp']}</span>
                        </div>
                        <div class="message-content">
                            {message['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-message">
                        <div class="assistant-header">
                            <span>KCT ASSISTANT</span>
                            <span class="timestamp">🕒 {message['timestamp']}</span>
                        </div>
                        <div class="message-content">
                            {message['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Chat input at the bottom
    st.markdown('<div class="bottom-input-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your question here...",
            placeholder="e.g., What courses does KCT offer?",
            label_visibility="collapsed",
            key="chat_input"
        )
    
    with col2:
        send_button = st.button("🚀 Send", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Process user input
    if send_button and user_input.strip():
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        try:
            from scripts.query_bot import query_knowledge_base
            response = query_knowledge_base(user_input)
            
            bot_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.messages.append(bot_message)
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()