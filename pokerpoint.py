import streamlit as st
import json
import os
import hashlib

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

# ===== パスワード管理 =====
# 管理者パスワードのハッシュ値を secrets.toml に設定してください
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
st.title("Poker Points Tracker (JSON版)")
menu = ["一般ユーザ", "特権ユーザ"]
mode = st.sidebar.selectbox("モードを選択", menu)

data = load_data()

if mode == "一般ユーザ":
    st.header("💡 一般ユーザモード")
    user_id = st.text_input("ユーザIDを入力してください")
    if user_id:
        if st.button("ユーザ登録"):
            if register_user(user_id):
                st.success(f"ユーザ '{user_id}' を登録しました。")
            else:
                st.error(f"ユーザ '{user_id}' は既に存在します。")

        pts = get_points(user_id)
        if pts is not None:
            st.info(f"{user_id} さんの現在のポイント: {pts}")

    # 全ユーザとポイント一覧を表示
    if data:
        st.subheader("📋 登録ユーザ一覧とポイント")
        table = [{"ユーザID": uid, "ポイント": pts} for uid, pts in data.items()]
        st.table(table)

elif mode == "特権ユーザ":
    st.header("🔐 特権ユーザモード")
    pwd = st.text_input("管理者パスワード", type="password")
    if pwd:
        if verify_password(pwd):
            st.success("認証に成功しました！")
            # 全ユーザとポイント一覧を表示
            if data:
                st.subheader("📋 登録ユーザ一覧とポイント")
                table = [{"ユーザID": uid, "ポイント": pts} for uid, pts in data.items()]
                st.table(table)
            else:
                st.warning("登録ユーザが存在しません。まずは一般ユーザモードで登録してください。")

            # ポイント更新用のUI
            if data:
                target = st.selectbox("対象ユーザIDを選択", list(data.keys()))
                delta = st.number_input("増減ポイント数 (マイナス可)", value=0, step=1)
                if st.button("ポイント更新"):
                    update_points(target, delta)
                    new_pts = get_points(target)
                    st.success(f"{target} のポイントを {delta} 更新しました。現在: {new_pts} ポイント")
        else:
            st.error("パスワードが間違っています。再度お試しください。")
