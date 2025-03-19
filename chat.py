import os
import random
import time
import streamlit as st
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from yahooquery import Ticker
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()

# Configuração do Azure OpenAI
openai_api_key = os.getenv("AZURE_OAI_KEY")
openai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OAI_DEPLOYMENT")
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX")

llm = AzureChatOpenAI(
    openai_api_key=openai_api_key,
    azure_endpoint=openai_endpoint,
    deployment_name=deployment_name,
    api_version="2024-02-15-preview"
)

# Configuração do Azure Search
search_client = SearchClient(
    endpoint=azure_search_endpoint,
    index_name=azure_search_index,
    credential=AzureKeyCredential(azure_search_key)
)

st.write("Streamlit loves LLMs! 🤖 [Build your own chat app](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps) in minutes, then make it powerful by adding images, dataframes, or even input widgets to the chat.")

st.caption("Note that this demo app isn't actually connected to any LLMs. Those are expensive ;)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Vamos começar a falar!"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Digite?"):

    with st.chat_message("user"):
        st.markdown(prompt)

    # Execute search with the prompt as the search text
    search_results = search_client.search(search_text=prompt, top=5)

    # Aggregate content field from search results
    aggregated_content = ""
    for result in search_results:
        content = result.get("content", "")  # Fetch content
        title = result.get("title", "sem título")
        url = result.get("url", "sem URL")
        
        aggregated_content += f"URL: {url}\nTitle: {title}\nContent:\n{content[:200]}...\n\n"  # Limit content for preview

    # If aggregated_content is still empty, print for debugging
    if not aggregated_content.strip():
        st.write("No content found in search results.")
    else:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            messages = [
                SystemMessage(content="Você é um analista de composição corporal"),
                HumanMessage(content=f"""
                    Dados relevantes:{aggregated_content}.
                    Utilize os dados informados para gerar a resposta. 
                    Sintetize em 300 caracteres.Acrecente ao final uma tabela com os dados{prompt}.
                    Ignore na resposta o texto: Por questões científicas e éticas, os dados devem ser interpretados em conjunto com seu histórico clínico e detalhes das condições de imagem.
                """)
            ]

            call = llm.invoke(messages)
            response = call.content

            # Simulate stream of response with milliseconds delay
            for chunk in response.split():
                response += chunk + " "
                time.sleep(0.05)
                # Add a blinking cursor to simulate typing
                message_placeholder.markdown(response + "▌")
            message_placeholder.markdown(response)
        
        # Add assistant response to chat history
        # st.session_state.messages.append({"role": "assistant", "content": response})
