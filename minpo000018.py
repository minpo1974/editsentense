
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import io
import chardet
import streamlit as st
import openai
import PyPDF2
import time
from streamlit_extras.buy_me_a_coffee import button

button(username="minpo", floating=True, width=221)

# OpenAI API 키와 모델 목록을 불러오는 함수
def load_model_list(filename):
    with open(filename, "r") as file:
        models = file.read().splitlines()
    return models

# 파일 내용을 문장 단위로 분리하는 함수
def split_into_sentences(text, min_words=10):
    sentences = []
    for sentence in text.split('. '):
        if len(sentence.split()) >= min_words:
            sentences.append(sentence)
    return sentences

# 업로드된 파일의 내용을 읽는 함수
def read_uploaded_file(uploaded_file):
    raw_data = uploaded_file.read()
    encoding = chardet.detect(raw_data)['encoding']
    return raw_data.decode(encoding)

# PDF 파일을 텍스트로 변환하는 함수
def pdf_to_text(uploaded_file):
    with io.BytesIO(uploaded_file.getvalue()) as open_pdf_file:
        reader = PyPDF2.PdfReader(open_pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def correct_text_with_gpt_full_text(text, model, api_key):
    # 전체 텍스트를 대화로 처리
    conversation_history = [
        {"role": "system", "content": "너는 이제 첨삭 전문가이다. 너는 언어학자이고 전문 교정 전문가이다. 모든 분야에 박학다식하다. 문장은 복사해서 입력으로 들어올 수도 있고, 다양한 포맷의 첨부가 들어올 수도 있다. 전체적인 맥락을 살펴보면서, 하나의 문장 단위로 반복해서 처리하고 교정된 문장에 대해, 원문, 교정, 교정된 이유에 대해, 다음의 형식으로 출력해줘.[원문] : '' [교정] : '' [교정된 이유] : ''"},
        {"role": "user", "content": text}
    ]

    # OpenAI ChatGPT를 사용하여 첨삭 수행
    response = openai.ChatCompletion.create(
        model=model,
        messages=conversation_history,
        api_key=api_key
    )

    # 첨삭된 결과 반환
    return response.choices[0].message['content']

# '[교정] :' 부분을 찾아서 해당 내용만 모으는 함수
def extract_corrections(text):
    corrections = []
    lines = text.split('\n')
    for line in lines:
        if '[교정] :' in line:
            # '[교정] :' 부분과 그 뒤의 내용을 추출
            correction = line.split('[교정] :')[1].split('[')[0].strip()
            corrections.append(correction)
    return corrections

# 스트림릿 인터페이스 설정
st.title("첨삭 서비스 with ChatGPT")
uploaded_file = st.file_uploader("파일 업로드", type=['pdf', 'txt'])
model_list = load_model_list("models.txt")
selected_model = st.selectbox("모델 선택", model_list)
openai_key = st.text_input('OpenAI API Key', type="password")

# 모델에 따라 다른 옵션 제공
if selected_model == "gpt-3.5-turbo":
    # gpt-3.5-turbo 모델을 사용하는 경우
    sentence_split_count = st.number_input("문장 분할 단위 선택 (기본값: 2)", min_value=1, value=2)
else:
    # 다른 모델을 사용하는 경우
    processing_choice = st.radio("처리 방식 선택", ["전체 텍스트", "문장 분할"])
    if processing_choice == "문장 분할":
        sentence_split_count = st.number_input("문장 분할 단위 선택", min_value=1, value=2)
    else:
        sentence_split_count = None

# 모든 교정 내용을 저장할 리스트
all_corrections = []

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        file_content = pdf_to_text(uploaded_file)
    else:  # txt 파일인 경우
        file_content = read_uploaded_file(uploaded_file)

    if selected_model != "gpt-3.5-turbo":
        if processing_choice == "전체 텍스트":
            # 전체 텍스트 처리 로직
            corrected_text = correct_text_with_gpt_full_text(file_content, selected_model, openai_key)
            
            # 교정된 부분만 추출하여 저장
            extracted_corrections = extract_corrections(corrected_text)
            all_corrections.extend(extracted_corrections)
            
            # 현재 단계의 교정 내용 출력
            st.write("처리된 텍스트:")
            st.write(corrected_text)
            st.write("교정된 내용:")
            for correction in extracted_corrections:
                st.write(correction)
        else:
            # 문장 분할 처리 로직
            sentences = split_into_sentences(file_content)
            for i in range(0, len(sentences), sentence_split_count):
                batch = sentences[i:i+sentence_split_count]
                combined_sentence = ' '.join(batch)
                corrected_text = correct_text_with_gpt_full_text(combined_sentence, selected_model, openai_key)
                
                extracted_corrections = extract_corrections(corrected_text)
                all_corrections.extend(extracted_corrections)
                
                st.write("처리된 텍스트:")
                st.write(corrected_text)
                st.write("교정된 내용:")
                for correction in extracted_corrections:
                    st.write(correction)
                st.write("---")
    else:
        # gpt-3.5-turbo 모델을 사용하는 경우의 로직
        sentences = split_into_sentences(file_content)
        for i in range(0, len(sentences), sentence_split_count):
            batch = sentences[i:i+sentence_split_count]
            combined_sentence = ' '.join(batch)
            corrected_text = correct_text_with_gpt_full_text(combined_sentence, selected_model, openai_key)
            
            extracted_corrections = extract_corrections(corrected_text)
            all_corrections.extend(extracted_corrections)
            
            st.write("처리된 텍스트:")
            st.write(corrected_text)
            st.write("교정된 내용:")
            for correction in extracted_corrections:
                st.write(correction)
            st.write("---")

# 모든 처리가 완료된 후 교정된 내용 출력
st.write("모든 교정된 내용:")
for correction in all_corrections:
    st.write(correction)
