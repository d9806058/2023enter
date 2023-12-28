import streamlit as st
import sqlite3
import pandas as pd
import random
import time


def main():
  con = sqlite3.connect("database.db", check_same_thread=False)
  cur = con.cursor()
  cur.execute('''
    CREATE TABLE IF NOT EXISTS users
    (id TEXT PRIMARY KEY,
    name TEXT,
    point INTEGER,
    stockvalue INTEGER)
    ''')

  st.title("2023 ENTER PROJECT")

  if "user" not in st.session_state:
    st.session_state.user = None

  if "choose" not in st.session_state:
    st.session_state.choose = "로그인"

  if "enteradmin" not in st.session_state:
    st.session_state.admin = False

  with st.sidebar:
    st.session_state.choose = st.selectbox(
        "MENU", ["로그인", "랭킹", "가상 주식 투자", "관리자 페이지"]
        if st.session_state.admin else ["로그인", "랭킹", "가상 주식 투자"])

  if st.session_state.choose == "로그인":
    if st.session_state.user is None:
      st.subheader('로그인')
      login_id = st.text_input('학번', placeholder='학번 5자리를 입력하세요')
      login_pw = st.text_input('이름', placeholder='이름을 입력하세요')
      login_btn = st.button(label='로그인', key=2)
      if login_btn:
        if login_id == '' or login_pw == '':
          st.error('학번과 이름을 모두 입력해주세요.')
        else:
          if login_id == '12429' and login_pw == 'enteradmin':
            st.session_state.user = {'id': '12429', 'name': 'enteradmin'}
            st.session_state.admin = True
            st.session_state.choose = "관리자 페이지"
            st.success('관리자 로그인 성공!')
          else:
            cur.execute('SELECT * FROM users WHERE id=? AND name=?',
                        (login_id, login_pw))
            data = cur.fetchone()
            if data is None:
              cur.execute(
                  "INSERT INTO users (id, name, point, stockvalue) VALUES (?, ?, 0, 0)",
                  (login_id, login_pw))
              con.commit()
              st.success('회원가입 성공!')
              st.session_state.user = {
                  'id': login_id,
                  'name': login_pw,
                  'point': 0,
                  'stockvalue': 0
              }
            else:
              st.success('로그인 성공!')
              st.session_state.user = {
                  'id': data[0],
                  'name': data[1],
                  'point': data[2],
                  'stockvalue': data[3]
              }
    else:
      st.info(
          f"이미 {st.session_state.user['name']}님의 계정이 로그인 상태입니다. 로그아웃을 원하신다면 새로고침(F5)를 눌러주세요."
      )
  elif st.session_state.choose == "관리자 페이지":
    st.subheader("관리자 페이지")
    admin_id = st.text_input('학번', placeholder='학번 5자리를 입력하세요')
    admin_name = st.text_input('이름', placeholder='이름을 입력하세요')
    search_btn = st.button(label='조회', key=3)

    # 데이터베이스에서 사용자 정보 검색
    cur.execute('SELECT * FROM users WHERE id=? AND name=?',
                (admin_id, admin_name))
    data = cur.fetchone()

    # 검색 결과가 없을 경우, 새로운 사용자 생성
    if data is None and search_btn:
      cur.execute(
          "INSERT INTO users (id, name, point, stockvalue) VALUES (?, ?, 0, 0)",
          (admin_id, admin_name))
      con.commit()
      st.success('자동 회원가입 완료!')
      data = (admin_id, admin_name, 0, 0)

    if data is not None:
      # 정보 출력
      st.write(
          f"ID: {data[0]}, Name: {data[1]}, Point: {data[2]}, StockValue: {data[3]}"
      )

      # 계정 삭제 버튼
      delete_btn = st.button(label='계정 삭제', key=4)
      if delete_btn:
        cur.execute("DELETE FROM users WHERE id=? AND name=?",
                    (admin_id, admin_name))
        con.commit()
        st.success('계정 삭제 완료!')

      # 포인트 조정 버튼
      with st.form(key='adjust_form'):
        new_point = st.number_input('새로운 포인트', min_value=0)
        adjust_btn = st.form_submit_button(label='포인트 조정')
        if adjust_btn:
          try:
            cur.execute("UPDATE users SET point=? WHERE id=? AND name=?",
                        (new_point, admin_id, admin_name))
            con.commit()
            st.success('포인트 조정 완료!')
          except Exception as e:
            st.error(f"포인트 조정 중 에러 발생: {e}")

  elif st.session_state.choose == "랭킹":
    st.subheader("랭킹")

    rank_query = '''
        SELECT id, name, point
        FROM users
        ORDER BY point DESC
        LIMIT 20
    '''
    cur.execute(rank_query)
    data = cur.fetchall()

    def create_ranking_df(data):
      if len(data) == 0:
        st.write("아직 등록된 사용자가 없습니다.")
        return None
      df = pd.DataFrame(data, columns=['학번', '이름', '포인트'])
      df.index = df.index + 1  # 순위는 1부터 시작
      return df

    df = create_ranking_df(data)
    if df is not None:
      st.table(df)

    # 일정 시간(5초) 후에 페이지 새로고침
    time.sleep(5)
    st.experimental_rerun()

  elif st.session_state.user is None:
    st.error('서비스를 이용하시려면 먼저 로그인해주세요.')

  con.close()
  user = st.session_state.user
  if user is not None:
    # Database connection
    con = sqlite3.connect("database.db", check_same_thread=False)
    cur = con.cursor()

    # Get user info from the database
    cur.execute(
        f"SELECT name, point, stockvalue FROM users WHERE id = {user['id']}")
    user_info = cur.fetchone()

    user_name = user_info[0]
    user_point = user_info[1]
    user_stockvalue = user_info[2]

    if st.session_state.admin:
      st.sidebar.markdown("**관리자 계정으로 로그인 상태입니다.**")
    else:
      st.sidebar.markdown(f"**{user_name}님 환영합니다!**")
      st.sidebar.markdown(f"보유 포인트: {user_point}")
  else:
    st.sidebar.markdown("로그인이 필요합니다.")


main()

con.close()

