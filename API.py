import streamlit as st
from openai import OpenAI
import pandas as pd
import numpy as np
from utils import get_context_from_query, custom_prompt, text_embedding, cosine_test
import json

file_name = open('credentials.json')
config_env = json.load(file_name)

df_vector_store = pd.read_pickle('df_vector_store.pkl')
vector_respuestas = pd.read_pickle('vector_respuestas.pkl')

def main_page():
  if "temperature" not in st.session_state:
      st.session_state.temperature = 0.0
  if "model" not in st.session_state:
      st.session_state.model = "gpt-3.5-turbo"
  if "message_history" not in st.session_state:
      st.session_state.message_history = []

  with st.sidebar:
    st.image('usta.png', use_column_width="always")
    st.header(body="Chat personalizado :robot_face:")
    st.subheader('Configuración del modelo :level_slider:')

    model_name = st.radio("**Elije el modelo a usar**:", ("GPT-3.5", "GPT-4"))
    if model_name == "GPT-3.5":
      st.session_state.model = "gpt-3.5-turbo"
    elif model_name == "GPT-4":
      st.session_state.model = "gpt-4"
    
    st.session_state.temperature = st.slider("**Nivel de creatividad de respuesta**  \n  [Poco creativo ►►► Muy creativo]",
                                             min_value = 0.0,
                                             max_value = 1.0,
                                             step      = 0.1,
                                             value     = 0.0)
    if st.button("Calcular"):
       if st.session_state.message_history == []:
          st.error("No se ha hecho ninguna pregunta")
       else:
          ultima_respuesta = st.session_state.message_history[-1]["content"]
          vector_chat = np.array(text_embedding(ultima_respuesta))
          similitudes = []
          for vector in vector_respuestas:
             similitudes.append(cosine_test(vector, vector_chat))
          resultado = max(similitudes)
          st.info(f"La similitu con la respuesta propia es de: {resultado}")
       
  if st.session_state.get('generar_pressed', False):
    for message in st.session_state.message_history:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

  if prompt := st.chat_input("¿Cuál es tu consulta?"):

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        Context_List = get_context_from_query(query = prompt,
                                              vector_store = df_vector_store,
                                              n_chunks = 5)
        client = OpenAI(api_key=config_env["openai_key"])
        completion = client.chat.completions.create(
           model=st.session_state.model,
           temperature = st.session_state.temperature,
           messages=[{"role": "system", "content": f"{custom_prompt.format(source = str(Context_List))}"}] + 
           st.session_state.message_history + [{"role": "user", "content": prompt}])

        full_response = completion.choices[0].message.content
        message_placeholder.markdown(full_response)

    st.session_state.message_history.append({"role": "user", "content": prompt})
    st.session_state.message_history.append({"role": "assistant", "content": full_response})
    st.session_state.generar_pressed = True
       
if __name__ == "__main__":
    main_page()