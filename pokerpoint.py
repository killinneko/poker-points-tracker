import streamlit as st
import json
import os
import hashlib
import math
from datetime import datetime
from zoneinfo import ZoneInfo

# ===== ファイル設定 =====
DATA_FILE = 'poker_points.json'

# ===== データ操作関数 =====

def load_data() -> dict:
    """
    JSON ファイルからユーザデータを読み込みます。
    ファイルがなければ空の dict を返します。
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_last_updated() -> str:
    """
    JSON ファイルの最終更新日時を日本標準時（Asia/Tokyo）で返します。
    ファイルがなければ '-' を返します。
    """
    if os.path.exists(DATA_FILE):
        mtime = os.path.getmtime(DATA_FILE)
        # 日本標準時タイムゾーンで変換
        dt = datetime.fromtimestamp(mtime, tz=ZoneInfo("Asia/Tokyo"))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return '-'

def save_data(data: dict) -> None:
    """
    ユーザデータを JSON ファイルに保存します。
    """
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(user_id: str) -> bool:
    """
    新規ユーザを登録します。
    すでに存在する場合は False を返します。
    """
    data = load_data()
    if user_id in data:
        return False
    data[user_id] = 0
    save_data(data)
    return True

def get_points(user_id: str) -> int | None:
    """
    ユーザの現在ポイントを取得します。
    未登録の場合は None を返します。
    """
    data = load_data()
    return data.get(user_id)

def update_points(user_id: str, delta: int) -> None:
    """
    ユーザのポイントを増減します。
    """
    data = load_data()
    if user_id in data:
        data[user_id] += delta
        save_data(data)

def set_points(user_id: str, new_points: int) -> None:
    """
    ユーザのポイントを指定値に設定します。
    """
    data = load_data()
    if user_id in data:
        data[user_id] = new_points
        save_data(data)

# ===== 共通描画 =====
def render_table(data: dict):
    """
    ポイントランキングをテーブル形式で表示し、
    同一ポイントは同一順位、1位を黄色、ポイントが0未満の行を赤でハイライトします。
    """
    ranked = sorted(data.items(), key=lambda x: x[1], reverse=True)
    html = '<table style="width:100%; border-collapse: collapse;">'
    html += '<tr style="background-color:#ddd;"><th style="padding:8px; text-align:left;">順位</th><th style="padding:8px; text-align:left;">ユーザID</th><th style="padding:8px; text-align:left;">ポイント</th></tr>'
    prev_pts = None
    rank = 0
    count = 0
    for uid, pts in ranked:
        count += 1
        if pts != prev_pts:
            rank = count
            prev_pts = pts
        if rank == 1:
            row_style = 'background-color:#ffff99;'
        elif pts < 0:
            row_style = 'background-color:#ffcccc;'
        else:
            row_style = ''
        html += f'<tr style="{row_style}">'
        html += f'<td style="padding:8px;">{rank}</td>'
        html += f'<td style="padding:8px;">{uid}</td>'
        html += f'<td style="padding:8px;">{pts}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

# ===== パスワード管理 =====
# 管理者パスワードの SHA-256 ハッシュ値を secrets.toml に設定してください
# [secrets]
# admin_password_hash = "<SHA256ハッシュ>"
ADMIN_PASSWORD_HASH = st.secrets.get("admin_password_hash", "2cef86d059837fc3e32df7a286bfc692012e50e0c1547968b569cc26df47af04")

def verify_password(input_pwd: str) -> bool:
    """
    入力パスワードを SHA-256 ハッシュ化して照合します。
    """
    if not ADMIN_PASSWORD_HASH:
        return False
    hashed = hashlib.sha256(input_pwd.encode('utf-8')).hexdigest()
    return hashed == ADMIN_PASSWORD_HASH

# ===== Streamlit アプリ =====
st.title("ポーカーのポイントトラッカー")
st.markdown(f"**最終更新日時:** {get_last_updated()}")

menu = ["ユーザー", "管理者"]
mode = st.sidebar.selectbox("モードを選択", menu)

data = load_data()

if mode == "ユーザー":
    user_id = st.text_input("ユーザIDを入力してください")
    if st.button("ユーザ登録") and user_id:
        if register_user(user_id):
            st.success(f"ユーザ '{user_id}' を登録しました。")
        else:
            st.error(f"ユーザ '{user_id}' は既に存在します。")
    if user_id:
        pts = get_points(user_id)
        if pts is not None:
            st.info(f"{user_id} さんの現在のポイント: {pts}")
    if data:
        render_table(data)
    # データダウンロード
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    st.download_button(
        label="🔽 データをダウンロード",
        data=json_str,
        file_name=DATA_FILE,
        mime="application/json"
    )

elif mode == "管理者":
    st.header("🔐 管理者モード")
    pwd = st.text_input("管理者パスワード", type="password")
    if pwd and verify_password(pwd):
        st.success("認証に成功しました！")

        col1, col2 = st.columns(2)
        # データアップロード
        with col1:
            uploaded_file = st.file_uploader(
                "📂 データをアップロード",
                type=["json"],
                help="poker_points.json を選択してください"
            )
            if uploaded_file:
                try:
                    new_data = json.load(uploaded_file)
                    if isinstance(new_data, dict):
                        save_data(new_data)
                        data = new_data
                        st.success("データを正常にアップロードしました。")
                    else:
                        st.error("アップロードされたファイルの形式が正しくありません。JSON オブジェクトを期待しています。")
                except Exception as e:
                    st.error(f"アップロード中にエラーが発生しました: {e}")
        with col2:
            # データダウンロード
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                    label="🔽 データをダウンロード",
                    data=json_str,
                    file_name=DATA_FILE,
                    mime="application/json"
            )

        if data:
            render_table(data)
            st.subheader("⚙️ ワンクリック操作")
            target = st.selectbox("対象ユーザIDを選択", list(data.keys()))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("最大引き出す (300)"):
                    update_points(target, -300)
                    st.success(f"{target} から300ポイント引き出しました。")
                    data = load_data(); 
                if st.button("初期設定 (300)"):
                    set_points(target, 300)
                    st.success(f"{target} の残高を300にリセットしました。")
                    data = load_data(); 
                if st.button("ログインボーナス (150)"):
                    update_points(target, 150)
                    st.success(f"{target} に150ポイントを追加しました。")
                    data = load_data(); 
            with col2:
                withdraw_amount = st.number_input("引き出す額を入力", min_value=0, step=1, key="withdraw_input")
                if st.button("引き出す", key="withdraw_btn"):
                    update_points(target, -withdraw_amount)
                    st.success(f"{target} から{withdraw_amount}ポイント引き出しました。")
                    data = load_data(); 
                deposit = st.number_input("預け入れる額を入力", min_value=0, step=1, key="deposit_input")
                if st.button("預け入れる (10%引き)", key="deposit_discount_btn"):
                    bonus = math.floor(deposit * 0.9)
                    update_points(target, bonus)
                    st.success(f"{target} に{bonus}ポイントを預け入れました（元金: {deposit} - 手数料10%）。")
                    data = load_data(); 
                if st.button("預け入れる", key="deposit_btn"):
                    bonus = math.floor(deposit)
                    update_points(target, bonus)
                    st.success(f"{target} に{bonus}ポイントを預け入れました（元金: {deposit}）。")
                    data = load_data(); 
        else:
            st.warning("登録ユーザが存在しません。まずはユーザモードで登録してください。")
    elif pwd:
        st.error("パスワードが間違っています。再度お試しください。")