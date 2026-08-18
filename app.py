import streamlit as st
import sqlite3
from groq import Groq
from tavily import TavilyClient

# Page Config aur Styling (ChatGPT Dark Theme Look)
st.set_page_config(page_title="Personal GPT", page_icon="🔐", layout="centered")

# Custom CSS for Premium Design
st.markdown("""
    <style>
    .stApp {
        background-color: #131314;
    }
    .stRadio > label {
        color: #e3e3e3 !important;
        font-weight: bold;
    }
    div[data-testid="stSidebar"] {
        background-color: #1e1f20 !important;
    }
    h1 {
        color: #f0f4f9 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Keys Configuration Check
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    tavily_key = st.secrets["TAVILY_API_KEY"]
except Exception as e:
    st.error("Secrets missing! Please add GROQ_API_KEY and TAVILY_API_KEY in Streamlit Settings.")
    st.stop()

# Initialize Clients
groq_client = Groq(api_key=groq_key)
tavily_client = TavilyClient(api_key=tavily_key)

# 2. SQL Database Setup
conn = sqlite3.connect("my_premium_diary.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS SecretVault (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        information TEXT
    )
''')
conn.commit()

# --- HEADER TITLE ---
st.markdown("<h1>🔐 My Personal ChatGPT Vault</h1>", unsafe_allow_html=True)

# --- SIDEBAR (DATA TRAIN / SAVE SECTION) ---
st.sidebar.markdown("<h2 style='color:#f0f4f9;'>🧠 Train Your AI</h2>", unsafe_allow_html=True)
topic_input = st.sidebar.text_input("Topic Name (e.g., Papa Birthday)")
info_input = st.sidebar.text_area("Secret Detail / Information")

if st.sidebar.button("Save & Teach AI", use_container_width=True):
    if topic_input and info_input:
        cursor.execute("INSERT INTO SecretVault (topic, information) VALUES (?, ?)", 
                       (topic_input, info_input))
        conn.commit()
        st.sidebar.success(f"Sikhaya gaya: {topic_input}!")
    else:
        st.sidebar.error("Dono fields ko bharein!")

# --- MODERN MODE CHANGER ---
mode = st.radio("Sawaal ka jawab kahan se nikalna hai?", 
                ["🔮 Mera Personal SQL Database (RAG)", "🌐 Live Internet Search (Tavily)"],
                horizontal=True)

st.markdown("<hr style='border-color:#333;'/>", unsafe_allow_html=True)

# --- 💬 CHAT HISTORY ENGINE (CHATGPT LOOK) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Main aapka private assistant hoon. Main aapke personal secrets aur internet dono se jawab de sakta hoon. Puchiye kya puchna hai?"}
    ]

# Render Entire Chat History on Screen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Sticky Chat Input at Bottom
user_query = st.chat_input("Message Personal GPT...")

if user_query:
    # 1. Instantly display user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        # 👉 UPDATE: Groq ka sateek aur latest version integration model ID
       ACTIVE_MODEL = "openai/gpt-oss-120b"
        
        
        if mode == "Mera Personal SQL Database (RAG)":
            with st.spinner("Searching SQL Vault..."):
                cursor.execute("SELECT topic, information FROM SecretVault")
                all_records = cursor.fetchall()
                
                diary_context = ""
                for row in all_records:
                    diary_context += f"Topic: {row[0]}, Secret Info: {row[1]}\n"
                
                # Note: gpt-oss-120b me direct instruction context ke sath user flow me dalna behtar kaam karta hai
                user_combined_prompt = f"""
                System Instruction: Aap ek personal private assistant hain. Aapko niche diye gaye DIARY DATA ke aadhar par hi user ke sawal ka hindi/hinglish me jawab dena hai. Agar data me jawab na mile, toh saaf keh dein 'Mujhe is baare me nahi sikhaya gaya hai'.
                
                DIARY DATA:
                {diary_context}
                
                User Sawaal: {user_query}
                """
                
                try:
                    response = groq_client.chat.completions.create(
                        model=ACTIVE_MODEL,
                        messages=[
                            {"role": "user", "content": user_combined_prompt}
                        ]
                    )
                    ai_reply = response.choices.message.content
                except Exception as e:
                    ai_reply = f"Groq Error: {str(e)}"
        
        else:
            # TAVILY WEB SEARCH MODE
            with st.spinner("Searching Internet via Tavily..."):
                try:
                    search_result = tavily_client.search(query=user_query, max_results=3)
                    results = search_result.get('results', [])
                    
                    web_context = ""
                    for res in results:
                        web_context += f"Title: {res.get('title')}\nContent: {res.get('content')}\n\n"
                    
                    user_combined_prompt = f"""
                    System Instruction: Aap ek intelligent web assistant hain. Niche diye gaye internet search data ke aadhar par user ke sawal ka short aur crisp jawab Hindi/Hinglish me banayein.
                    
                    INTERNET DATA:
                    {web_context}
                    
                    User Sawaal: {user_query}
                    """
                    
                    response = groq_client.chat.completions.create(
                        model=ACTIVE_MODEL,
                        messages=[
                            {"role": "user", "content": user_combined_prompt}
                        ]
                    )
                    ai_reply = response.choices.message.content
                except Exception as e:
                    ai_reply = f"Search Error: {str(e)}"
        
        # Display and Save Reply to History
        st.write(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    
