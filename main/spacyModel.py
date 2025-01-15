import sys
import os
import spacy
import sqlite3

def load_spacy_model():
    """
    spaCy 모델을 로드하거나 로컬 디렉토리에서 찾습니다.
    """
    if getattr(sys, 'frozen', False):  # PyInstaller로 패키징된 경우
        base_path = sys._MEIPASS  # PyInstaller 임시 디렉토리
        model_path = os.path.join(base_path, "en_core_web_sm")
    else:  # 개발 환경
        model_path = "en_core_web_sm"

    try:
        return spacy.load(model_path)
    except Exception as e:
        print(f"spaCy 모델 로드 실패: {e}")
        sys.exit(1)

def create_database():
    """
    데이터베이스와 테이블을 생성합니다.
    """
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    
    # texts 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    """)
    
    # parts 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            pos TEXT NOT NULL,
            dep TEXT NOT NULL,
            FOREIGN KEY (text_id) REFERENCES texts (id)
        )
    """)
    connection.commit()
    connection.close()

def save_to_database(input_text, results):
    """
    분석 결과를 데이터베이스에 저장합니다.
    """
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    
    # texts 테이블에 문장 삽입
    cursor.execute("INSERT INTO texts (content) VALUES (?)", (input_text,))
    text_id = cursor.lastrowid  # 삽입된 문장의 ID 가져오기
    
    # parts 테이블에 단어 분석 결과 삽입
    for token_data in results:
        cursor.execute("""
            INSERT INTO parts (text_id, token, pos, dep)
            VALUES (?, ?, ?, ?)
        """, (text_id, token_data["token"], token_data["pos"], token_data["dep"]))
    
    connection.commit()
    connection.close()

def analyze_sentence(text):
    """
    주어진 문장을 분석하고 결과를 반환합니다.
    """
    nlp = load_spacy_model()
    doc = nlp(text)

    results = []
    for token in doc:
        results.append({
            "token": token.text,
            "pos": token.pos_,
            "dep": token.dep_
        })
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py 'sentence_to_analyze'")
        sys.exit(1)

    input_text = sys.argv[1]

    # 데이터베이스 초기화
    create_database()

    try:
        # 문장 분석 및 결과 출력
        analysis_results = analyze_sentence(input_text)
        for result in analysis_results:
            print(f"{result['token']}: {result['pos']}, {result['dep']}")

        # 데이터베이스에 저장
        save_to_database(input_text, analysis_results)
        print("분석 결과가 데이터베이스에 저장되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
