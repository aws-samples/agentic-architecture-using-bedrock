import streamlit as st
import boto3
import json
import logging
import pprint
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Set the page configuration
st.set_page_config(page_title="Octank Pet Store")

# Set up logging
logging.basicConfig(
    format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set up AWS clients
region = 'us-west-2'
session = boto3.Session(region_name=region)
lambda_client = session.client('lambda')
bedrock_agent_runtime_client = session.client('bedrock-agent-runtime')

# Background Image and Styling
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)), url("https://worldanimalfoundation.org/wp-content/uploads/2023/09/Cute-dogs.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    .supervisor-text {
        font-size: 32px;
        font-weight: bold;
        color: #333;
        margin-bottom: 20px;
        text-align: center; /* Center the supervisor text */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Define the invokeAgent function
def invokeAgent(query, session_id, enable_trace=True, session_state=dict()):
    end_session = False
    agentResponse = bedrock_agent_runtime_client.invoke_agent(
        inputText=query,
        agentId='1DI7IG3BJJ',
        agentAliasId='TSTALIASID',
        sessionId=session_id,
        enableTrace=enable_trace, 
        endSession=end_session,
        sessionState=session_state
    )
    
    # if enable_trace:
    #     logger.info(pprint.pformat(agentResponse))
    
    event_stream = agentResponse['completion']
    try:
        for event in event_stream:        
            if 'chunk' in event:
                data = event['chunk']['bytes']
                if enable_trace:
                    logger.info(f"Final answer ->\n{data.decode('utf8')}")
                agent_answer = data.decode('utf8')
                return agent_answer
            elif 'trace' in event:
                if enable_trace:
                    logger.info(json.dumps(event['trace'], indent=2, cls=DateTimeEncoder))
            else:
                raise Exception("unexpected event.", event)
    except Exception as e:
        raise Exception("unexpected event.", e)

def main():
    # Centered Title
    st.markdown("<h1 style='text-align: center;'>Octank Pet Store</h1>", unsafe_allow_html=True)
    
    # Centered Header
    st.markdown("<h3 style='text-align: center;'>by Amazon Bedrock Agents</h3>", unsafe_allow_html=True)

    # Supervisor Text
    st.markdown('<div class="supervisor-text">Orchestrator Agent:</div>', unsafe_allow_html=True)

    # Chat Input Container
    with st.container():
        if prompt := st.chat_input(key="supervisor", placeholder="How can I help you today?"):
            # Append user input only if it's new
            if not st.session_state.messages or st.session_state.messages[-1]['content'] != prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})

            # Get agent response and append it only if it's new
            sessionId = st.session_state.get('sessionId', "None")
            result = invokeAgent(prompt, sessionId)
            if st.session_state.messages[-1]['content'] != result:
                st.session_state.messages.append({"role": "assistant", "content": result})

    # Display previous chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if 'sessionId' not in st.session_state:
        st.session_state['sessionId'] = "None"

    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Footer
    st.markdown(
        """
        <div class="footer">
            For inquiries, contact <a href="mailto:wchemz@amazon.com">wchemz@amazon.com</a>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == '__main__':
    main()
