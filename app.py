from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from book_rental.errors import BookRentalError
from book_rental.service import BookRentalService
from book_rental.store import CsvStore

st.set_page_config(page_title="BookBridge", page_icon="📚", layout="wide")

DATA_DIR = Path(os.environ.get("BOOKBRIDGE_DATA_DIR", "data"))
service = BookRentalService(CsvStore(DATA_DIR))


def run(action, success: str) -> None:
    try:
        action()
        st.success(success)
        st.rerun()
    except BookRentalError as error:
        st.error(str(error))


def show_table(rows: list[dict[str, str]], columns: list[str] | None = None) -> None:
    if not rows:
        st.info("표시할 데이터가 없습니다.")
        return
    frame = pd.DataFrame(rows)
    if columns:
        frame = frame[[column for column in columns if column in frame.columns]]
    st.dataframe(frame, use_container_width=True, hide_index=True)


def go_to(page: str) -> None:
    st.session_state.page = page
    st.session_state.nav_version = st.session_state.get("nav_version", 0) + 1


if flash := st.session_state.pop("flash", None):
    st.success(flash)

actor = st.session_state.get("user")
role = actor["role"] if actor else None
actor_id = int(actor["id"]) if actor else None

with st.sidebar:
    st.title("📚 BookBridge")
    if actor:
        st.write(f"**현재 사용자: {actor['name']} / 군번: {actor['military_id']}**")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.pop("user", None)
            go_to("책 둘러보기")
            st.rerun()
        menu = ["책 둘러보기"]
        if role == "USER":
            menu += ["내 대여", "책 등록", "내 등록 도서"]
        elif role == "ADMIN":
            menu += ["관리자 대시보드", "도서 승인", "대여 승인", "전체 대출", "사용자 관리"]
    else:
        st.info("로그인하거나 회원가입 후 대여·등록 기능을 이용할 수 있습니다.")
        menu = ["책 둘러보기", "로그인", "회원가입"]
    requested_page = st.session_state.get("page", menu[0])
    if requested_page not in menu:
        requested_page = menu[0]
    page = st.radio("메뉴", menu, index=menu.index(requested_page), key=f"navigation-{st.session_state.get('nav_version', 0)}")
    st.session_state.page = page

if page == "책 둘러보기":
    st.title("📚 BookBridge")
    st.caption("함께 나누는 책, 더 넓어지는 지식")
    if not actor:
        signup, login = st.columns(2)
        if signup.button("회원가입", type="primary", use_container_width=True):
            go_to("회원가입")
            st.rerun()
        if login.button("로그인", use_container_width=True):
            go_to("로그인")
            st.rerun()
    st.subheader("등록·승인된 책")
    books = service.approved_books()
    search = st.text_input("제목·저자·카테고리 검색")
    if search:
        keyword = search.casefold()
        books = [row for row in books if keyword in " ".join((row["title"], row["author"], row["category"])).casefold()]
    if not books:
        st.info("현재 등록·승인된 책이 없습니다.")
    for book in books:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(book["title"])
            left.write(f"**저자** {book['author']} · **카테고리** {book['category']}")
            left.write(book["description"] or "설명이 없습니다.")
            left.caption(f"형식: {'PDF' if book['format'] == 'PDF' else '실물 도서'} · 등록자: {book['lender_name']}")
            right.metric("대여 가능 수량", f"{book['available_quantity']} / {book['total_quantity']}")
            if role == "USER" and int(book["available_quantity"]) > 0:
                quantity = right.number_input("수량", 1, int(book["available_quantity"]), key=f"qty-{book['id']}")
                if right.button("대여 요청", key=f"borrow-{book['id']}", type="primary"):
                    run(lambda b=int(book["id"]), q=int(quantity): service.create_borrow_request(actor_id, b, q), "대여 요청을 등록했습니다.")
            elif not actor:
                right.caption("로그인 후 대여할 수 있습니다.")

elif page == "로그인":
    st.title("로그인")
    with st.form("login-form"):
        military_id = st.text_input("아이디(군번)")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", type="primary")
    if submitted:
        try:
            st.session_state.user = service.authenticate(military_id, password)
            st.session_state.flash = "로그인했습니다."
            go_to("책 둘러보기")
            st.rerun()
        except BookRentalError as error:
            st.error(str(error))

elif page == "회원가입":
    st.title("회원가입")
    with st.form("signup-form"):
        name = st.text_input("이름")
        military_id = st.text_input("군번")
        password = st.text_input("비밀번호", type="password")
        password_confirmation = st.text_input("비밀번호 확인", type="password")
        submitted = st.form_submit_button("회원가입", type="primary")
    if submitted:
        try:
            service.register_user(name, military_id, password, password_confirmation)
            st.session_state.flash = "회원가입이 완료되었습니다. 로그인해 주세요."
            go_to("로그인")
            st.rerun()
        except BookRentalError as error:
            st.error(str(error))

elif not actor:
    st.warning("로그인 후 이용할 수 있는 메뉴입니다.")

elif page == "내 대여":
    st.title("내 대여")
    st.subheader("대여 요청")
    show_table(service.borrower_requests(actor_id), ["id", "book_title", "quantity", "status", "requested_at", "rejection_memo"])
    st.subheader("대출 현황")
    loans = service.loans(actor_id)
    show_table(loans, ["id", "book_title", "book_format", "quantity", "loaned_at", "due_at", "returned_at", "status"])
    downloadable = [loan for loan in loans if loan["book_format"] == "PDF" and loan["status"] in {"LOANED", "OVERDUE"}]
    if downloadable:
        st.subheader("대여 중인 PDF")
        for loan in downloadable:
            try:
                file_name, content = service.pdf_download(actor_id, int(loan["id"]))
                st.download_button(
                    f"{loan['book_title']} PDF 다운로드", data=content, file_name=file_name,
                    mime="application/pdf", key=f"pdf-{loan['id']}",
                )
            except BookRentalError as error:
                st.warning(f"{loan['book_title']}: {error}")
    active = [loan for loan in loans if loan["status"] in {"LOANED", "OVERDUE"}]
    if active:
        selected = st.selectbox("반납할 대출", active, format_func=lambda row: f"#{row['id']} {row['book_title']}")
        if st.button("반납 처리", type="primary"):
            run(lambda: service.return_book(actor_id, int(selected["id"])), "반납 처리했습니다.")

elif page == "책 등록":
    st.title("책 등록")
    with st.form("book-form"):
        title = st.text_input("제목")
        author = st.text_input("저자")
        category = st.text_input("카테고리")
        description = st.text_area("설명")
        book_format = st.selectbox("형식", ["PHYSICAL_BOOK", "PDF"], format_func=lambda value: "실물 도서" if value == "PHYSICAL_BOOK" else "PDF")
        total_quantity = st.number_input("총 수량", 1, 100, 1)
        loan_days = st.number_input("기본 대여 기간(일)", 1, 365, 14)
        upload = st.file_uploader("PDF 파일", type=["pdf"], disabled=book_format != "PDF")
        submitted = st.form_submit_button("승인 요청", type="primary")
    if submitted:
        uploaded = (upload.name, upload.getvalue()) if upload else None
        run(lambda: service.create_book(
            actor_id, title=title, author=author, category=category, description=description,
            book_format=book_format, total_quantity=int(total_quantity),
            default_loan_days=int(loan_days), uploaded_file=uploaded,
        ), "책을 등록했습니다. 관리자 승인을 기다려 주세요.")

elif page == "내 등록 도서":
    st.title("내 등록 도서")
    show_table(service.lender_books(actor_id), ["id", "title", "author", "format", "available_quantity", "total_quantity", "status", "rejection_memo", "created_at"])

elif page == "관리자 대시보드":
    st.title("관리자 대시보드")
    metrics = service.dashboard(actor_id)
    for start in range(0, len(metrics), 3):
        columns = st.columns(3)
        for column, (label, value) in zip(columns, list(metrics.items())[start:start + 3]):
            column.metric(label, value)

elif page == "도서 승인":
    st.title("도서 승인")
    pending = service.pending_books(actor_id)
    show_table(pending, ["id", "title", "author", "lender_name", "format", "total_quantity", "created_at"])
    if pending:
        selected = st.selectbox("처리할 책", pending, format_func=lambda row: f"#{row['id']} {row['title']}")
        memo = st.text_input("거절 사유")
        approve, reject = st.columns(2)
        if approve.button("승인", type="primary", use_container_width=True):
            run(lambda: service.approve_book(actor_id, int(selected["id"])), "도서를 승인했습니다.")
        if reject.button("거절", use_container_width=True):
            run(lambda: service.reject_book(actor_id, int(selected["id"]), memo), "도서를 거절했습니다.")

elif page == "대여 승인":
    st.title("대여 승인")
    requests = service.all_requests(actor_id)
    show_table(requests, ["id", "book_title", "borrower_name", "quantity", "status", "requested_at", "rejection_memo"])
    pending = [row for row in requests if row["status"] == "REQUESTED"]
    if pending:
        selected = st.selectbox("처리할 요청", pending, format_func=lambda row: f"#{row['id']} {row['book_title']} / {row['borrower_name']}")
        memo = st.text_input("거절 사유")
        approve, reject = st.columns(2)
        if approve.button("승인", type="primary", use_container_width=True):
            run(lambda: service.approve_request(actor_id, int(selected["id"])), "대여 요청을 승인했습니다.")
        if reject.button("거절", use_container_width=True):
            run(lambda: service.reject_request(actor_id, int(selected["id"]), memo), "대여 요청을 거절했습니다.")

elif page == "전체 대출":
    st.title("전체 대출")
    loans = service.loans(actor_id, admin=True)
    show_table(loans, ["id", "book_title", "borrower_name", "lender_name", "book_format", "quantity", "loaned_at", "due_at", "returned_at", "status"])
    for loan in [row for row in loans if row["book_format"] == "PDF" and row["status"] in {"LOANED", "OVERDUE"}]:
        try:
            file_name, content = service.pdf_download(actor_id, int(loan["id"]))
            st.download_button(f"#{loan['id']} {loan['book_title']} PDF 확인", content, file_name, "application/pdf", key=f"admin-pdf-{loan['id']}")
        except BookRentalError as error:
            st.warning(f"{loan['book_title']}: {error}")
    active = [loan for loan in loans if loan["status"] in {"LOANED", "OVERDUE"}]
    if active:
        selected = st.selectbox("관리자 반납 처리", active, format_func=lambda row: f"#{row['id']} {row['book_title']} / {row['borrower_name']}")
        if st.button("반납 처리"):
            run(lambda: service.return_book(actor_id, int(selected["id"])), "반납 처리했습니다.")

elif page == "사용자 관리":
    st.title("사용자 관리")
    show_table(service.users(actor_id), ["id", "name", "military_id", "role", "active", "created_at"])
    st.subheader("일반 사용자 추가")
    with st.form("admin-user-form"):
        name = st.text_input("이름")
        military_id = st.text_input("군번")
        password = st.text_input("임시 비밀번호", type="password")
        password_confirmation = st.text_input("임시 비밀번호 확인", type="password")
        submitted = st.form_submit_button("사용자 추가", type="primary")
    if submitted:
        run(lambda: service.admin_create_user(actor_id, name, military_id, password, password_confirmation), "일반 사용자를 추가했습니다.")
