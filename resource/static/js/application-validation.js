// To-do
/*
* 1. 중간 공백 처리
* 2. id, 팀명 : 중복확인 버튼 구현
* 3. validateApplication Form이 false 또는 true를 리턴
* 4. 8월 29일까지 application페이지 값 검증과 서버단 validation 어노테이션 활용 검증 구현
* 5. 등록 api 완성하기
* */

let globalIsValid = true;
let validationType = "SETTING";
let invalidInputIdList = [];

const validateApplicationForm = () => {
    globalIsValid = true;
    invalidInputIdList = [];

    // trim 처리
    $('input').each((idx, elem)=> elem.type !== 'file' ? elem.value = $.trim(elem.value) : '');
    $('textarea').each((idx, elem)=> elem.value = $.trim(elem.value));
    validateApplicationInfo();
    validateTeamInfo();
    validateSurveyInfo();
    validateFilesInfo();
    return globalIsValid;
}

const validateEtcDescription = () => {
    const elem = $('#recognition-path-ETC-description');
    const elemVal = elem.val();
    let isBlank = elemVal === null || elemVal === ' ' || elemVal === '';
    const feedbackId = `#recognition-path-ETC-description-invalid-feedback`;
    const pattern = '^.{0,30}$';
    const message = '30자 이내로 입력하시기 바랍니다.';

    if(validationType !== "SETTING") {
        if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
        if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());


        if(isBlank) {
            const etcCheckbox = $('#recognition-path-ETC');
            if($(etcCheckbox).is(':checked')){
                invalidInputIdList.push(elem.attr('id'));
                globalIsValid = false;
            }
            if(elem.val() === '') {
                elem.removeClass('is-valid').removeClass('is-invalid');
                $(feedbackId).removeClass('d-none').removeClass('d-block');
            } else {
                elem.removeClass('is-valid').addClass('is-invalid');
                $(feedbackId).text(message);
                $(feedbackId).removeClass('d-none').addClass('d-block');
            }
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    }

    elem.on('input', (e) => {
        const value = e.target.value;
        let isBlankInput = value === null || value === ' ' || value === '';
        if(pattern) isBlankInput = isBlankInput || !RegExp(pattern).test(value);

        if(isBlankInput) {
            const etcCheckbox = $('#recognition-path-ETC');
            if($(etcCheckbox).is(':checked')){
                invalidInputIdList.push(elem.attr('id'));
                globalIsValid = false;
            }
            if(elem.val() === '') {
                elem.removeClass('is-valid').removeClass('is-invalid');
                $(feedbackId).removeClass('d-none').removeClass('d-block');
            } else {
                elem.removeClass('is-valid').addClass('is-invalid');
                $(feedbackId).text(message);
                $(feedbackId).removeClass('d-none').addClass('d-block');
            }
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    })

}

/*const validateAskContent = () => {
    const elem = $('#ask-content');
    const elemVal = elem.val();
    let isBlank = false;
    const feedbackId = `#ask-content-invalid-feedback`;
    const pattern = '^((\\r\\n|\\r|\\n)|.){0,500}$';
    const message = '500자 이내로 입력하시기 바랍니다.';

    if(validationType !== "SETTING") {
        if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
        if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());

        if(isBlank) {
            invalidInputIdList.push(elem.attr('id'));
            globalIsValid = false;
            if(elem.val() === '') {
                elem.removeClass('is-valid').removeClass('is-invalid');
                $(feedbackId).removeClass('d-none').removeClass('d-block');
            } else {
                elem.removeClass('is-valid').addClass('is-invalid');
                $(feedbackId).text(message);
                $(feedbackId).removeClass('d-none').addClass('d-block');
            }
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    }

    elem.on('input', (e) => {
        const value = e.target.value;
        let isBlankInput = false;
        if(pattern) isBlankInput = isBlankInput || !RegExp(pattern).test(value);

        if(isBlankInput) {
            invalidInputIdList.push(elem.attr('id'));
            globalIsValid = false;
            if(elem.val() === '') {
                elem.removeClass('is-valid').removeClass('is-invalid');
                $(feedbackId).removeClass('d-none').removeClass('d-block');
            } else {
                elem.removeClass('is-valid').addClass('is-invalid');
                $(feedbackId).text(message);
                $(feedbackId).removeClass('d-none').addClass('d-block');
            }
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    })

}*/

// notBlank
const notBlank = (elem, message = "", selectOption = false, pattern = "", passwordCheck = false) => {
    // 초기 입력값 검증
    // 타입에 따라 초기 validation 여부 결정하기 부터 ㄱㄱ
    const elemVal = elem.val();
    let isBlank = elemVal === null || elemVal === ' ' || elemVal === '';
    const feedbackId = `#${elem.attr('id')}-invalid-feedback`;

    if(validationType !== "SETTING") {
        
        if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
        if(selectOption) {
            isBlank = isBlank || (elemVal === 'select');
        }
        if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());
        if(passwordCheck) isBlank = isBlank || ($('#password').val() !== elemVal);
        if(elem.attr('id') === 'password') {
            if(RegExp('(\\w)\\1\\1').test(elem.val())) {
                isBlank = true;
                message = '동일문자를 3회이상 반복사용하지 마세요.';
            } else message = '영문/숫자/특수기호 포함 9자~20자';
        }

        // file 처리
        if(elem.attr('type') === 'file') {
            const ext = getExtension(elem.val())
            if(elem.val() && ext !== '.pdf') {
                isBlank = true;
                message = "pdf파일을 업로드하세요.";
            }
            if(elem.val()) {
                const fileSize = elem[0].files[0].size/(1024*1024);
                const maxSize = 5;
                if(fileSize > maxSize) {
                    isBlank = true;
                    message = "최대 용량은 5MB입니다.";
                }
            }
        }

        if(isBlank) {
            // globalIsValid
            invalidInputIdList.push(elem.attr('id'));
            globalIsValid = false;
            if(elem.attr('id') === 'team-name') $('#team-name-duplicate-feedback').text('');
            else if(elem.attr('id') === 'user-id') $('#user-id-duplicate-feedback').text('');
            elem.removeClass('is-valid').addClass('is-invalid');
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        }
        else {
            // 팀명과 ID중복검사
            if(elem.attr('id') === 'team-name') duplicateCheckTeamName();
            else if(elem.attr('id') === 'user-id') duplicateCheckId();
            else {
                elem.removeClass('is-invalid').addClass('is-valid');
                $(feedbackId).removeClass('d-block').addClass('d-none');
            }
        }

    }
    // 초기 입력값 검증 이후 변화되는 값 검증
    elem.on('input', (e) => {
        const value = e.target.value;
        let isBlankInput = value === null || value === ' ' || value === '';
        if(selectOption) isBlankInput = isBlankInput || (value === 'select');
        if(pattern) isBlankInput = isBlankInput || !RegExp(pattern).test(value);
        if(elem.attr('id'))
            if(passwordCheck) isBlankInput = isBlankInput || ($('#password').val() !== value);
        if(elem.attr('id') === 'password') {
            if(RegExp('(\\w)\\1\\1').test(elem.val())) {
                isBlankInput = true;
                message = '동일문자를 3회이상 반복사용하지 마세요.';
            } else message = '영문/숫자/특수기호 포함 9자~20자';
        }
        if(elem.attr('type') === 'file') {
            const ext = getExtension(elem.val())
            if(ext !== '.pdf') {
                isBlankInput = true;
                message = "pdf파일을 업로드하세요.";
            }
            if(elem.val()) {
                const fileSize = elem[0].files[0].size/(1024*1024);
                const maxSize = 5;
                if(fileSize > maxSize) {
                    isBlank = true;
                    message = "최대 용량은 5MB입니다.";
                }
            }
        }
        if(isBlankInput) {
            invalidInputIdList.push(elem.attr('id'));
            globalIsValid = false;
            if(elem.attr('id') === 'team-name') $('#team-name-duplicate-feedback').text('');
            else if(elem.attr('id') === 'user-id') $('#user-id-duplicate-feedback').text('');
            elem.removeClass('is-valid').addClass('is-invalid');
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        }
        else {
             // 팀명과 ID중복검사
            if(elem.attr('id') === 'team-name') duplicateCheckTeamName();
            else if(elem.attr('id') === 'user-id') duplicateCheckId();
            else {
                elem.removeClass('is-invalid').addClass('is-valid');
                $(feedbackId).removeClass('d-block').addClass('d-none');
            }
        }
    })
}

const validateApplicationInfo = () => {

    let contestField = $('#contest-field');
    notBlank(contestField, '분야를 선택하세요.',true);

    let projectName = $('#project-name');
    notBlank(projectName, '프로젝트명을 입력하세요.');

}

const validateTeamInfo = () => {

    let teamName = $('#team-name');
    notBlank(teamName, '영문/한글/숫자 1자~20자', false, '^[a-zA-Z가-힣0-9]{1,20}$');

    let userId = $('#user-id');
    notBlank(userId, '영문/숫자 5자~15자',false, '^[A-za-z0-9]{5,15}$');

    let password = $('#password');
    notBlank(password, '영문/숫자/특수기호 포함 9자~20자', false, '^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*\\W)(?=\\S+$).{9,20}$');

    let passwordCheck = $('#password-check');
    notBlank(passwordCheck, '위 비밀번호와 동일하게 입력하세요.',false, '^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*\\W)(?=\\S+$).{9,20}$', true);

    // 유효한 memberInfoList를 받아서 notBlank처리
    let memberInfoList = getMemberInfoList();
    for(let i=0; i<memberInfoList.length; i++) {
        const memberInfo = memberInfoList[i];
        const seq = memberInfo.sequence;
        notBlank($(`#member-rank-${seq}`), '', true);
        notBlank($(`#member-rank-name-${seq}`), '', false, '^[a-zA-Z가-힣]{2,20}$');
        notBlank($(`#member-name-${seq}`), '', false, '^[가-힣]{2,20}$');
        notBlank($(`#member-birthday-${seq}`), '', false, '^(19[0-9][0-9]|20\\d{2})-(0[0-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$');
        notBlank($(`#member-phone-${seq}`), '', false, '^\\d{3}-\\d{3,4}-\\d{4}$');
        notBlank($(`#member-mail-${seq}`), '', false, '^[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}$');
        notBlank($(`#member-main-group-${seq}`), '', false, '^.{1,30}$');
    }
}

const validateSurveyInfo = () => {
/*
    let participantMotivation = $('#participant-motivation');
    notBlank(participantMotivation, '참가동기를 500자 이내로 기입하시기 바랍니다.', false, '^((\\r\\n|\\r|\\n)|.){1,500}$');
*/

    // 인지경로 예외처리
    const recognitionPathElemList = $('[id^=recognition-path]');
    const feedbackId = '#recognition-path-invalid-feedback';
    const message = "적어도 하나를 선택하세요."

    // 기타 input 활성화/비활성화
    const etcCheckbox = $('#recognition-path-ETC');
    const etcInput = $('#recognition-path-ETC-description');
    etcCheckbox.on('input', () => {
        if($(etcCheckbox).is(':checked')) etcInput.attr('disabled', false);
        else {
            etcInput.val('');
            etcInput.attr('disabled', true);
            etcInput.removeClass('is-valid').removeClass('is-invalid');
            const feedbackId = `#recognition-path-ETC-description-invalid-feedback`;
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    })

    if(validationType !== "SETTING") {
        if (!getRecognitionPathList().length) {
            invalidInputIdList.push('recognition-path-SNS');
            globalIsValid = false;
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        } else {
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    }
    recognitionPathElemList.on('click', () => {
        if(!getRecognitionPathList().length) {
            invalidInputIdList.push('recognition-path-SNS');
            globalIsValid = false;
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        } else {
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    })
}

const validateFilesInfo = () => {
    let copyrightFile = $('#copyright-file');
    notBlank(copyrightFile, "저작권 동의서 파일을 선택하세요.");

    let ideaPlanFile = $('#idea-plan-file');
    notBlank(ideaPlanFile, "아이디어 기획서 파일을 선택하세요.");

    let ideaSummaryFile = $('#idea-summary-file');
    notBlank(ideaSummaryFile, "아이디어 요약서 파일을 선택하세요.");

    let personalInfoFile = $('#personal-info-file');
    notBlank(personalInfoFile, "개인정보제공 동의서를 선택하세요.");

    // 파일 용량 제한 처리 : notblank 안에서 switch case로 예외처리
}

const switchMemberInfoRow = (e) => {
    const seq = e.target.value;
    if(!(2 <= seq && seq <= 4)) return ;

    const checked = e.target.checked;
    const memberInputSelector = `input[id^='member-'][id$='-${seq}'`;
    const memberSelectBoxSelector = `select[id^='member-'][id$='-${seq}'`;

    const memberRowInputList = $(memberInputSelector);
    const memberRowSelectBox = $(memberSelectBoxSelector);

    if(checked) {
        memberRowSelectBox.attr('disabled', false);
        memberRowSelectBox.attr('readonly', false);
        memberRowInputList.attr('disabled', false);
        memberRowInputList.attr('readonly', false);
    } else {
        memberRowSelectBox.attr('disabled', true);
        memberRowSelectBox.attr('readonly', true);
        memberRowInputList.attr('disabled', true);
        memberRowInputList.attr('readonly', true);
    }

}

const initMemberInfoRow = () => {
    const memberCheckBoxSelector = `input[id^='member-check-']`;
    const memberCheckBoxList = $(memberCheckBoxSelector);

    memberCheckBoxList.click();
}

$(document).ready(async () => {
    await initMemberInfoRow();
    await validateApplicationForm();
    validationType = "SUBMIT";
})