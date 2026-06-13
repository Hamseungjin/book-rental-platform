from __future__ import annotations

import logging

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from book_rental.admin_data import AdminDataService
from book_rental.config import get_data_dir
from book_rental.errors import BookRentalError
from book_rental.login import attempt_login
from book_rental.service import BookRentalService
from book_rental.sessions import SESSION_MINUTES, SessionService
from book_rental.store import SCHEMAS, CsvStore

st.set_page_config(page_title="BookBridge", page_icon="📚", layout="wide")

LOGGER = logging.getLogger("bookbridge")
LOGGER.setLevel(logging.INFO)
DATA_DIR = get_data_dir()
LOGGER.info("BookBridge data directory: %s", DATA_DIR)
store = CsvStore(DATA_DIR)
service = BookRentalService(store)
admin_data = AdminDataService(store)
sessions = SessionService(store)
COOKIE_NAME = "bookbridge_session"


def run(action, success: str) -> None:
    try:
        action()
        st.success(success)
        st.rerun()
    except BookRentalError as error:
        st.error(str(error))
    except Exception:
        LOGGER.exception("BookBridge action failed")
        st.error("요청 처리 중 오류가 발생했습니다.")


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


def set_browser_cookie(token: str, *, delete: bool = False, reload: bool = True) -> None:
    """Set the HttpOnly-ineligible UI cookie, then reload so Streamlit can read it."""
    max_age = 0 if delete else SESSION_MINUTES * 60
    value = "" if delete else token
    components.html(
        f"""<script>
        document.cookie = {COOKIE_NAME!r} + '=' + encodeURIComponent({value!r})
          + '; path=/; max-age={max_age}; SameSite=Lax';
        if ({str(reload).lower()}) setTimeout(() => window.parent.location.reload(), 150);
        </script>""",
        height=0,
    )


cookie_token = st.session_state.get("session_token", "")
if not cookie_token and "user" not in st.session_state:
    cookie_token = st.context.cookies.get(COOKIE_NAME, "")
if cookie_token:
    try:
        restored_user = sessions.restore(cookie_token)
    except Exception:
        LOGGER.exception("Persistent session restore failed for data_dir=%s sessions_path=%s", DATA_DIR, store.path("sessions"))
        restored_user = None
    if restored_user:
        st.session_state.user = restored_user
        st.session_state.session_token = cookie_token
        try:
            set_browser_cookie(cookie_token, reload=False)
        except Exception:
            LOGGER.exception("Browser cookie refresh failed for user_id=%s", restored_user["id"])
    else:
        st.session_state.pop("user", None)
        st.session_state.pop("session_token", None)
        st.session_state.session_expired = True

if st.session_state.pop("session_expired", False):
    st.warning("로그인 세션이 만료되었습니다. 다시 로그인해주세요.")
    set_browser_cookie("", delete=True)

if flash := st.session_state.pop("flash", None):
    st.toast(flash)
    st.success(flash)

actor = st.session_state.get("user")
role = actor["role"] if actor else None
actor_id = int(actor["id"]) if actor else None

with st.sidebar:
    st.title("📚 BookBridge")
    if actor:
        st.write(f"**현재 사용자: {actor['name']} / 군번: {actor['military_id']}**")
        if st.button("로그아웃", use_container_width=True):
            token = st.session_state.pop("session_token", st.context.cookies.get(COOKIE_NAME, ""))
            try:
                sessions.revoke(token)
            except Exception:
                LOGGER.exception("Persistent session revoke failed for data_dir=%s", DATA_DIR)
            st.session_state.pop("user", None)
            go_to("책 둘러보기")
            set_browser_cookie("", delete=True)
            st.stop()
        menu = ["책 둘러보기"]
        if role == "USER":
            menu += ["내 대여", "책 등록", "내 등록 도서"]
        elif role == "ADMIN":
            menu += ["관리자 대시보드", "도서 승인", "대여 승인", "전체 대출", "사용자 관리", "데이터 관리"]
    else:
        st.info("로그인하거나 회원가입 후 대여·등록 기능을 이용할 수 있습니다.")
        menu = ["책 둘러보기", "로그인", "회원가입"]
    requested_page = st.session_state.get("page", menu[0])
    forbidden_page = requested_page == "데이터 관리" and role != "ADMIN"
    if requested_page not in menu:
        requested_page = menu[0]
    page = st.radio("메뉴", menu, index=menu.index(requested_page), key=f"navigation-{st.session_state.get('nav_version', 0)}")
    st.session_state.page = page

if forbidden_page:
    st.error("권한이 없습니다.")

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
            if role == "USER":
                available = int(book["available_quantity"])
                quantity = right.number_input("수량", 1, max(1, available), key=f"qty-{book['id']}", disabled=available == 0)
                if right.button("대여 요청", key=f"borrow-{book['id']}", type="primary", disabled=available == 0):
                    run(lambda b=int(book["id"]), q=int(quantity): service.create_borrow_request(actor_id, b, q), "대여 요청이 완료되었습니다.")
                if available == 0:
                    right.warning("대여 가능한 수량이 없습니다.")
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
            attempt = attempt_login(service, sessions, military_id, password, LOGGER)
        except Exception:
            LOGGER.exception(
                "Login authentication failed unexpectedly for military_id=%r data_dir=%s users_path=%s",
                str(military_id).strip(), DATA_DIR, store.path("users"),
            )
            st.error("로그인 처리 중 오류가 발생했습니다.")
        else:
            result = attempt.result
            if result.succeeded:
                st.session_state.user = result.user
                if attempt.token:
                    st.session_state.session_token = attempt.token
                    st.session_state.flash = "로그인되었습니다. 15분 동안 로그인 상태가 유지됩니다."
                    go_to("책 둘러보기")
                    try:
                        set_browser_cookie(attempt.token)
                    except Exception:
                        LOGGER.exception("Login succeeded but browser cookie setup failed for user_id=%s", result.user["id"])
                        st.session_state.flash = "로그인되었습니다. 다만 새로고침 시 다시 로그인해야 할 수 있습니다."
                        st.rerun()
                    st.stop()
                else:
                    st.session_state.flash = "로그인되었습니다. 다만 로그인 유지 기능을 사용할 수 없습니다."
                    go_to("책 둘러보기")
                    st.rerun()
            elif result.status == "ACCOUNT_NOT_FOUND":
                st.toast("존재하지 않는 계정입니다.")
                st.error("존재하지 않는 계정입니다.")
            elif result.status == "INVALID_PASSWORD":
                st.toast("비밀번호가 틀렸습니다.")
                st.error("비밀번호가 틀렸습니다.")
            else:
                st.error("비활성화된 계정입니다. 관리자에게 문의하세요.")

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
            st.toast("회원가입이 완료되었습니다.")
            st.session_state.flash = "회원가입이 완료되었습니다. 로그인해주세요."
            go_to("로그인")
            st.rerun()
        except BookRentalError as error:
            st.error(str(error))
        except Exception:
            LOGGER.exception("Registration failed unexpectedly")
            st.error("회원가입 처리 중 오류가 발생했습니다.")

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
    registration_completed = st.session_state.get("book_registration_completed", False)
    if registration_completed:
        if st.session_state.pop("book_registration_toast_pending", False):
            st.toast("등록 신청이 완료되었습니다.")
        st.success("등록 신청이 완료되었습니다.")
        st.write("관리자 승인 후 대여 가능한 도서 목록에 표시됩니다.")
        if st.button("확인", type="primary", key="book-registration-confirm"):
            st.session_state.pop("book_registration_completed", None)
            go_to("내 등록 도서")
            st.rerun()
    else:
        with st.form("book-form", clear_on_submit=False):
            title = st.text_input("제목")
            author = st.text_input("저자")
            category = st.text_input("카테고리")
            description = st.text_area("설명")
            book_format = st.selectbox("형식", ["PHYSICAL_BOOK", "PDF"], format_func=lambda value: "실물 도서" if value == "PHYSICAL_BOOK" else "PDF")
            total_quantity = st.number_input("총 수량", 1, 100, 1)
            loan_days = st.number_input("기본 대여 기간(일)", 1, 365, 14)
            upload = st.file_uploader("PDF 파일", type=["pdf"])
            st.caption("PDF 형식으로 등록할 때는 PDF 파일을 반드시 첨부해주세요.")
            submitted = st.form_submit_button("승인 요청", type="primary")
        if submitted:
            if book_format == "PDF" and upload is None:
                st.error("PDF 파일을 업로드해주세요.")
            else:
                uploaded = (upload.name, upload.getvalue()) if book_format == "PDF" and upload else None
                try:
                    service.create_book(
                        actor_id, title=title, author=author, category=category, description=description,
                        book_format=book_format, total_quantity=int(total_quantity),
                        default_loan_days=int(loan_days), uploaded_file=uploaded,
                    )
                    st.session_state.book_registration_completed = True
                    st.session_state.book_registration_toast_pending = True
                    st.rerun()
                except BookRentalError as error:
                    st.error(str(error))
                except Exception:
                    LOGGER.exception("Book registration failed unexpectedly")
                    st.error("책 등록 처리 중 오류가 발생했습니다.")

elif page == "내 등록 도서":
    st.title("내 등록 도서")
    show_table(service.lender_books(actor_id), ["id", "title", "author", "format", "available_quantity", "total_quantity", "status", "rejection_memo", "created_at"])

elif page == "관리자 대시보드":
    st.title("관리자 대시보드")
    st.caption(f"현재 데이터 디렉터리: {DATA_DIR}")
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

elif page == "데이터 관리":
    if role != "ADMIN":
        st.error("권한이 없습니다.")
    else:
        st.title("데이터 관리")
        st.caption(f"현재 데이터 디렉터리: {DATA_DIR}")
        labels = {
            "사용자 관리": "users", "도서 관리": "books", "대여 요청 관리": "borrow_requests",
            "대출 관리": "loans", "관리자 로그 보기": "admin_logs",
        }
        section = st.radio("관리 대상", list(labels), horizontal=True, key="data-management-section")
        table = labels[section]
        try:
            rows = admin_data.read_table(actor, table)
            frame = pd.DataFrame(rows, columns=SCHEMAS[table])
            if table == "admin_logs":
                st.info("관리자 로그는 데이터 무결성을 위해 조회 전용입니다.")
                st.dataframe(frame, use_container_width=True, hide_index=True)
            else:
                st.caption("행을 추가·수정하거나 왼쪽 행 메뉴로 삭제한 뒤 미리보기와 저장을 진행하세요.")
                disabled = ["password_hash"] if table == "users" else []
                edited = st.data_editor(frame, num_rows="fixed" if table == "users" else "dynamic", disabled=disabled, use_container_width=True, hide_index=True, key=f"editor-{table}")
                before_ids = set(frame.get("id", pd.Series(dtype=str)).astype(str))
                after_ids = set(edited.get("id", pd.Series(dtype=str)).astype(str))
                deleted = before_ids - after_ids
                if deleted:
                    st.warning(f"삭제 예정 ID: {', '.join(sorted(deleted))}")
                    confirmed = st.checkbox("정말 삭제하시겠습니까?", key=f"delete-confirm-{table}")
                else:
                    confirmed = True
                preview, save, refresh = st.columns(3)
                if preview.button("저장 전 미리보기", use_container_width=True):
                    st.session_state[f"preview-{table}"] = edited.to_dict("records")
                if save.button("저장", type="primary", use_container_width=True):
                    if not confirmed:
                        st.error("삭제하려면 확인 절차를 완료해주세요.")
                    else:
                        try:
                            backup = admin_data.save_table(actor, table, edited.to_dict("records"))
                            st.session_state.flash = f"저장되었습니다. 백업: {backup.name}"
                            st.rerun()
                        except BookRentalError as error:
                            st.error(str(error))
                if refresh.button("변경 취소 / 새로고침", use_container_width=True):
                    st.session_state.pop(f"preview-{table}", None)
                    st.rerun()
                if preview_rows := st.session_state.get(f"preview-{table}"):
                    st.subheader("저장 전 미리보기")
                    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)
                if table == "users":
                    st.divider()
                    st.subheader("새 사용자 추가")
                    with st.form("data-user-create"):
                        create_name = st.text_input("이름")
                        create_military_id = st.text_input("군번")
                        create_role = st.selectbox("역할", ["USER", "ADMIN"])
                        create_password = st.text_input("초기 비밀번호", type="password")
                        create_password_confirmation = st.text_input("초기 비밀번호 확인", type="password")
                        create_submitted = st.form_submit_button("사용자 추가", type="primary")
                    if create_submitted:
                        if create_password != create_password_confirmation:
                            st.error("비밀번호가 일치하지 않습니다.")
                        else:
                            try:
                                admin_data.create_user(actor, create_name, create_military_id, create_password, create_role)
                                st.session_state.flash = "사용자가 추가되었습니다."
                                st.rerun()
                            except BookRentalError as error:
                                st.error(str(error))
                    st.divider()
                    st.subheader("비밀번호 재설정")
                    user_id = st.number_input("사용자 ID", min_value=1, step=1)
                    new_password = st.text_input("새 비밀번호", type="password")
                    confirm_password = st.text_input("새 비밀번호 확인", type="password")
                    if st.button("비밀번호 재설정"):
                        if new_password != confirm_password:
                            st.error("비밀번호가 일치하지 않습니다.")
                        else:
                            try:
                                admin_data.reset_password(actor, int(user_id), new_password)
                                st.success("비밀번호가 안전하게 재설정되었습니다.")
                            except BookRentalError as error:
                                st.error(str(error))
        except BookRentalError as error:
            st.error(str(error))
