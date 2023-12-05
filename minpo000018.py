
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


import io
import chardet
import streamlit as st
import PyPDF2
import time
import openai

def load_model_list(filename):
    with open(filename, "r") as file:
        models = file.read().splitlines()
    return models

def split_into_sentences(text, min_words=10):
    sentences = []
    for sentence in text.split('. '):
        if len(sentence.split()) >= min_words:
            sentences.append(sentence)
    return sentences

def read_uploaded_file(uploaded_file):
    raw_data = uploaded_file.read()
    encoding = chardet.detect(raw_data)['encoding']
    return raw_data.decode(encoding)

def pdf_to_text(uploaded_file):
    with io.BytesIO(uploaded_file.getvalue()) as open_pdf_file:
        reader = PyPDF2.PdfReader(open_pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def correct_text_with_gpt_full_text(text, model, prompt):
    conversation_history = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]

    try :
        response = openai.chat.completions.create(
            model=model,
            messages=conversation_history,
            timeout=120
        )
        return response.choices[0].message.content
    except openai.APIConnectionError as e:
        print(f"API 연결 오류: {e}")
        return None
    except openai.OpenAIError as e:
        print(f"OpenAI 에러: {e}")
        return None    
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return None



default_prompt = "너는 이제 첨삭 전문가이다. 너는 언어학자이고 전문 교정 전문가이다. 모든 분야에 박학다식하다. 문장은 복사해서 입력으로 들어올 수도 있고, 다양한 포맷의 첨부가 들어올 수도 있다. 전체적인 맥락을 살펴보면서, 하나의 문장 단위로 반복해서 처리하고 교정된 문장에 대해, 원문, 교정, 교정된 이유에 대해, 다음의 형식으로 출력해줘.[원문] : '' [교정] : '' [교정된 이유] : ''"
user_prompt = st.text_area("Prompt 입력", value=default_prompt, height=150)

st.title("첨삭 서비스 with ChatGPT")
uploaded_file = st.file_uploader("파일 업로드", type=['pdf', 'txt'])
model_list = load_model_list("models.txt")
selected_model = st.selectbox("모델 선택", model_list)
openai.api_key = st.text_input('OpenAI API Key', type="password")

if selected_model == "gpt-3.5-turbo":
    sentence_split_count = st.number_input("문장 분할 단위 선택 (기본값: 2)", min_value=1, value=2)
else:
    processing_choice = st.radio("처리 방식 선택", ["전체 텍스트", "문장 분할"])
    if processing_choice == "문장 분할":
        sentence_split_count = st.number_input("문장 분할 단위 선택", min_value=1, value=2)
    else:
        sentence_split_count = None

all_corrections = []

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        file_content = pdf_to_text(uploaded_file)
    else:
        file_content = read_uploaded_file(uploaded_file)

    if selected_model != "gpt-3.5-turbo":
        if processing_choice == "전체 텍스트":
            corrected_text = correct_text_with_gpt_full_text(file_content, selected_model, user_prompt)        
            st.write("처리된 텍스트:")
            st.write(corrected_text)
        else:
            sentences = split_into_sentences(file_content)
            for i in range(0, len(sentences), sentence_split_count):
                batch = sentences[i:i+sentence_split_count]
                combined_sentence = ' '.join(batch)
                corrected_text = correct_text_with_gpt_full_text(combined_sentence, selected_model, user_prompt)
                st.write("처리된 텍스트:")
                st.write(corrected_text)
                st.write("---")
    else:
        sentences = split_into_sentences(file_content)
        for i in range(0, len(sentences), sentence_split_count):
            batch = sentences[i:i+sentence_split_count]
            combined_sentence = ' '.join(batch)
            corrected_text = correct_text_with_gpt_full_text(combined_sentence, selected_model, user_prompt)
            st.write("처리된 텍스트:")
            st.write(corrected_text)
            st.write("---")
