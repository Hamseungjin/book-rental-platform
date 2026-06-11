let changePasswordIsValid = true;
let changePasswordValidationType = 'SETTING';

const validateChangePasswordForm = () => {
    changePasswordIsValid = true;

    let changePassword = $('#change-password');
    notBlankChangePassword(changePassword, '영문/숫자/특수기호 포함 9자~20자', false, '^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*\\W)(?=\\S+$).{9,20}$');

    let changePasswordCheck = $('#change-password-check');
    notBlankChangePassword(changePasswordCheck, '위 비밀번호와 동일하게 입력하세요.',false, '^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*\\W)(?=\\S+$).{9,20}$', true);

    return changePasswordIsValid;
}

// notBlank
const notBlankChangePassword = (elem, message = "", selectOption = false, pattern = "", passwordCheck = false) => {
    const elemVal = elem.val();
    let isBlank = elemVal === null || elemVal === ' ' || elemVal === '';
    const feedbackId = `#${elem.attr('id')}-invalid-feedback`;

    if(changePasswordValidationType !== 'SETTING') {
        if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());
        if(passwordCheck) isBlank = isBlank || ($('#change-password').val() !== elemVal);
        if(elem.attr('id') === 'change-password') {
            if(RegExp('(\\w)\\1\\1').test(elem.val())) {
                isBlank = true;
                message = '동일문자를 3회이상 반복사용하지 마세요.';
            } else message = '영문/숫자/특수기호 포함 9자~20자';
        }

        if(isBlank) {
            changePasswordIsValid = false;
            elem.removeClass('is-valid').addClass('is-invalid');
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    }


    // 초기 입력값 검증 이후 변화되는 값 검증
    elem.on('input', (e) => {
        const value = e.target.value;
        let isBlankInput = value === null || value === ' ' || value === '';
        if(pattern) isBlankInput = isBlankInput || !RegExp(pattern).test(value);
        if(elem.attr('id'))
            if(passwordCheck) isBlankInput = isBlankInput || ($('#change-password').val() !== value);
        if(elem.attr('id') === 'change-password') {
            if(RegExp('(\\w)\\1\\1').test(elem.val())) {
                isBlankInput = true;
                message = '동일문자를 3회이상 반복사용하지 마세요.';
            } else message = '영문/숫자/특수기호 포함 9자~20자';
        }

        if(isBlankInput) {
            changePasswordIsValid = false;
            elem.removeClass('is-valid').addClass('is-invalid');
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    })
}

const changePasswordHandler = (e) => {
    e.preventDefault();

    const validateCheck = validateChangePasswordForm();

    if(!validateCheck) {
        e.stopPropagation();
        alert("입력란을 확인하세요.");
    } else {
        let data = {
            changePassword: $('#change-password').val(),
            changePasswordCheck: $('#change-password-check').val()
        };

        const apiUrl = window.location.pathname === '/alr20/judge/confirm' ? '/alr20/judge/change/password' : '/alr20/mypage/change/password';

        $('#loading-spinner').removeClass('d-none').addClass('d-block');
        $.ajax({
            type: 'POST',
            url: apiUrl,
            // beforeSend: function(xhr){
            //     xhr.setRequestHeader(header, token);
            // },
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(data),
            cache: false,
            success: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                alert(res.message);
                window.location.reload();
            },
            error: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                const errRes = res.responseJSON;
                if(errRes.status === 'BAD_REQUEST') alert(errRes.message);
                else alert('입력란을 확인하세요.');
            }
        })
    }

}

$(document).ready(async () => {

    await validateChangePasswordForm();
    changePasswordValidationType = "SUBMIT";

    const initPasswordCheck = $('#initPasswordCheck').val();

    if(initPasswordCheck) {
        alert(initPasswordCheck);
        $('#changePasswordButton').click();
    }
})