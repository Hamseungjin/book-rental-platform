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


users = service.users()
with st.sidebar:
    st.title("📚 BookBridge")
    actor_labels = {f"{user['name']} · {user['roles']} (#{user['id']})": user for user in users}
    actor_label = st.selectbox("현재 사용자", actor_labels)
    actor = actor_labels[actor_label]
    actor_id = int(actor["id"])
    roles = set(actor["roles"].split("|"))
    st.caption("CSV 파일을 데이터베이스로 사용하는 로컬 데모입니다.")
    menu = ["책 둘러보기", "내 대여"]
    if "LENDER" in roles:
        menu += ["책 등록", "내 등록 도서"]
    if "ADMIN" in roles:
        menu += ["관리자 대시보드", "도서 승인", "대여 승인", "전체 대출"]
    menu += ["사용자 추가"]
    page = st.radio("메뉴", menu)

st.title(page)

if page == "책 둘러보기":
    books = service.approved_books()
    search = st.text_input("제목·저자·카테고리 검색")
    if search:
        keyword = search.casefold()
        books = [row for row in books if keyword in " ".join((row["title"], row["author"], row["category"])).casefold()]
    if not books:
        st.info("현재 대여 가능한 책이 없습니다.")
    for book in books:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(book["title"])
            left.write(f"**저자** {book['author']} · **카테고리** {book['category']} · **등록자** {book['lender_name']}")
            left.write(book["description"] or "설명이 없습니다.")
            left.caption(f"형식: {book['format']} · 기본 대여 {book['default_loan_days']}일")
            right.metric("대여 가능", f"{book['available_quantity']} / {book['total_quantity']}")
            if "BORROWER" in roles and int(book["available_quantity"]) > 0:
                quantity = right.number_input("수량", 1, int(book["available_quantity"]), key=f"qty-{book['id']}")
                if right.button("대여 요청", key=f"borrow-{book['id']}", type="primary"):
                    run(lambda b=int(book["id"]), q=int(quantity): service.create_borrow_request(actor_id, b, q), "대여 요청을 등록했습니다.")

elif page == "내 대여":
    if "BORROWER" not in roles:
        st.warning("BORROWER 역할이 필요합니다.")
    else:
        st.subheader("대여 요청")
        show_table(service.borrower_requests(actor_id), ["id", "book_title", "quantity", "status", "requested_at", "rejection_memo"])
        st.subheader("대출 현황")
        loans = service.loans(actor_id)
        show_table(loans, ["id", "book_title", "quantity", "loaned_at", "due_at", "returned_at", "status"])
        active = [loan for loan in loans if loan["status"] in {"LOANED", "OVERDUE"}]
        if active:
            selected = st.selectbox("반납할 대출", active, format_func=lambda row: f"#{row['id']} {row['book_title']}")
            if st.button("반납 처리", type="primary"):
                run(lambda: service.return_book(actor_id, int(selected["id"])), "반납 처리했습니다.")

elif page == "책 등록":
    with st.form("book-form"):
        title = st.text_input("제목")
        author = st.text_input("저자")
        category = st.text_input("카테고리")
        description = st.text_area("설명")
        book_format = st.selectbox("형식", ["PHYSICAL_BOOK", "PDF"])
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
    show_table(service.lender_books(actor_id), ["id", "title", "author", "format", "available_quantity", "total_quantity", "status", "rejection_memo", "created_at"])

elif page == "관리자 대시보드":
    metrics = service.dashboard(actor_id)
    for start in range(0, len(metrics), 3):
        columns = st.columns(3)
        for column, (label, value) in zip(columns, list(metrics.items())[start:start + 3]):
            column.metric(label, value)

elif page == "도서 승인":
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
    loans = service.loans(actor_id, admin=True)
    show_table(loans, ["id", "book_title", "borrower_name", "lender_name", "quantity", "loaned_at", "due_at", "returned_at", "status"])
    active = [loan for loan in loans if loan["status"] in {"LOANED", "OVERDUE"}]
    if active:
        selected = st.selectbox("관리자 반납 처리", active, format_func=lambda row: f"#{row['id']} {row['book_title']} / {row['borrower_name']}")
        if st.button("반납 처리"):
            run(lambda: service.return_book(actor_id, int(selected["id"])), "반납 처리했습니다.")

elif page == "사용자 추가":
    with st.form("user-form"):
        name = st.text_input("이름")
        email = st.text_input("이메일")
        selected_roles = st.multiselect("역할", ["BORROWER", "LENDER", "ADMIN"], default=["BORROWER"])
        submitted = st.form_submit_button("사용자 추가", type="primary")
    if submitted:
        run(lambda: service.create_user(name, email, selected_roles), "사용자를 추가했습니다.")
