const getApplicationInfo = () => {
    return {
        contestField: $('#contest-field').val(),
        projectName: $('#project-name').val()
    }
}

const checkMemberInfoRow = (memberInfo) => {
    let seq = memberInfo.sequence;
    /*
    for(const key in memberInfo) {
        if(key === 'sequence') continue;
        else if(key === 'rank'){
            ret = ret || (memberInfo[key] !== 'select');
        }
        else ret = ret || memberInfo[key] !== "";
    }

     */
    return $(`#member-check-i${seq}`).is(':checked');
}

const getMemberInfoList = () => {
    let memberInfoList = [];

    // 팀장은 무조건 추가
    memberInfoList.push({
        sequence: 1,
        rank: $(`#member-rank-${1}`).val(),
        rankName: $(`#member-rank-name-${1}`).val(),
        name: $(`#member-name-${1}`).val(),
        birthday: $(`#member-birthday-${1}`).val(),
        phone: $(`#member-phone-${1}`).val(),
        mail: $(`#member-mail-${1}`).val(),
        mainGroup: $(`#member-main-group-${1}`).val(),
/*        subGroup: $(`#member-sub-group-${1}`).val()*/
    });

    for(let i=2; i<=4; i++) {
        if(!$(`#member-rank-${i}`).val()) continue;
        const memberInfo = {
            sequence: i,
            rank: $(`#member-rank-${i}`).val(),
            rankName: $(`#member-rank-name-${i}`).val(),
            name: $(`#member-name-${i}`).val(),
            birthday: $(`#member-birthday-${i}`).val(),
            phone: $(`#member-phone-${i}`).val(),
            mail: $(`#member-mail-${i}`).val(),
            mainGroup: $(`#member-main-group-${i}`).val(),
/*            subGroup: $(`#member-sub-group-${i}`).val()*/
        };
        // 행 중 한 열이라도 채워져 있으면 검사하고 리스트에 추가
        if(checkMemberInfoRow(memberInfo)) {
            memberInfoList.push(memberInfo);
        }
    }
    return memberInfoList;
}

const getTeamInfo = () => {
    const memberInfoList = getMemberInfoList();
    return {
        teamName: $('#team-name').val(),
        userId: $('#user-id').val(),
        password: 'test1234!',
        passwordCheck: 'test1234!',
        memberInfoList: memberInfoList,
        memberCount: memberInfoList.length
    }
}

const getRecognitionPathList = () => {
    let recognitionPathList = [];
    const recognitionPathElemList = $('[id^=recognition-path]');
    for(let i = 0; i < recognitionPathElemList.length; i++) {
        const recognitionPathElem = recognitionPathElemList[i];
        if(recognitionPathElem.checked) recognitionPathList.push(recognitionPathElem.value);
    }
    return recognitionPathList;
}

const getSurveyInfo = () => {
    return {
        // askContent: $('#ask-content').val().replace(/(?:\r\n|\r|\n)/g, '<br>'),
        // participantMotivation: $('#participant-motivation').val().replace(/(?:\r\n|\r|\n)/g, '<br>'),
/*        askContent: $('#ask-content').val(),*/
/*        participantMotivation: $('#participant-motivation').val(),*/
        recognitionPathList: getRecognitionPathList(),
        etcDescription: $('#recognition-path-ETC-description').val()
    }
}


const getExtension = fileName => {
    var _fileLen = fileName.length;

    var _lastDot = fileName.lastIndexOf('.');

    var _fileExt = fileName.substring(_lastDot, _fileLen).toLowerCase();

    return _fileExt;
}

const setFileInfo = async (selector) => {
    const $target = $(selector);
    const file = $target[0]?.files?.[0];
    if (!file) return;

    const origFileName = file.name;
    const extension = getExtension(origFileName);


    const meta = { origFileName, extension};

    switch (selector) {
        case '#idea-plan-file':   fileMeta.ideaPlanFileInfo    = meta; break;
        case '#idea-summary-file':fileMeta.ideaSummaryFileInfo = meta; break;
        default: break;
    }
}

const getErrorMessage = () => {
    let msg = '';
    invalidInputIdList.forEach(elem => {
        if(elem.includes('ask-content')) msg +=  '문의사항' + ' : ' + $(`#ask-content-invalid-feedback`).text() + '\n';
        else if(elem.includes('participant-motivation')) msg +=  '참가동기*' + ' : ' + $(`#participant-motivation-invalid-feedback`).text() + '\n';
        else if(elem.includes('recognition-path')) msg +=  '인지경로*' + ' : ' + $(`#recognition-path-invalid-feedback`).text() + '\n';
        else if(elem.includes('member')) msg +=  '팀원정보*' + ' : ' + '팀원정보를 확인하세요.' + '\n';
        else if(elem.includes('personal-ifno-file')) msg +=  '개인정보 동의서: 모든 항목에 동의해주세요.\n';
        else if(elem.includes('copyright-file')) msg +=  '서약서: 모든 항목에 동의해주세요\n';
        else msg += $(`label[for='${elem}']`).text() + ' : ' + $(`#${elem}-invalid-feedback`).text() + '\n';
    })
    return msg;
}
const fileMeta = {
    ideaPlanFileInfo:  null,
    ideaSummaryFileInfo: null
};

const consentMeta={
    copyrightConsentInfo:{agreed:false},
    personalInfoConsentInfo:{agreed:false}
}

function updateConsentMeta(selector, propName){
    const agreed =$(selector).val() == 'AGREED';
    consentMeta[propName].agreed= agreed;
}


const submitApplication = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    const fileSelectors = [
        { selector: '#idea-plan-file',    partName: 'ideaPlanFile' },
        { selector: '#idea-summary-file', partName: 'ideaSummaryFile' }
    ];
    for (const {selector, partName} of fileSelectors) {
        // ① 메타 정보 채우기
        await setFileInfo(selector);

        // ② 실제 파일을 FormData 에 추가
        const file = $(selector)[0]?.files?.[0];
        if (file) {
            formData.append(partName, file);   // 백엔드가 기대하는 key 이름
        }
    }

    const payload = {
        applicationInfo: getApplicationInfo(),
        teamInfo:        getTeamInfo(),
        surveyInfo:      getSurveyInfo()
    };

    const payloadBlob = new Blob(
        [JSON.stringify(payload)],
        { type: 'application/json' }
    );
    formData.append('payload', payloadBlob);   // key 이름은 백엔드가 기대하는 이름과 동일

    // ③ fileMeta Blob 파트
    const fileMetaBlob = new Blob(
        [JSON.stringify(fileMeta)],
        {type: 'application/json'}
    );
    
    formData.append('fileMeta', fileMetaBlob); // 백엔드가 요구하는 키
    updateConsentMeta('#copyright-file', 'copyrightConsentInfo');
    updateConsentMeta('#personal-info-file', 'personalInfoConsentInfo');


    // var header = $("meta[name='_csrf_header']").attr('content');
    // var token = $("meta[name='_csrf']").attr('content');

    const validateCheck = validateApplicationForm();

    if(!validateCheck) {
        e.stopPropagation();

        const errorMessage = await getErrorMessage();
        alert(errorMessage);

        $('html, body').animate({
            scrollTop : $(`#${invalidInputIdList[0]}`).offset().top - 130
        });
    } else {
        $('#loading-spinner').removeClass('d-none').addClass('d-block');
        $.ajax({
            type: 'POST',
            url: '/alr20/application/edit',
            // beforeSend: function(xhr){
            //     xhr.setRequestHeader(header, token);
            // },
            data: formData,
            processData: false,
            contentType: false,
            cache: false,
            success: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                alert(res.message);
                window.location.href = "/alr20/";
            },
            error: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                const errRes = res.responseJSON;
                if(errRes.status === 'BAD_REQUEST') alert(errRes.message);
                if(errRes.status === 'UNAUTHORIZED') alert(errRes.message);
                if(errRes.status === 'FORBIDDEN') {
                    alert(errRes.message);
                    $('#changePasswordButton').click();
                }
                else alert('입력란을 확인하세요.');
            }
        })
    }
}

// To-do
/*
* 1. 중간 공백 처리
* 2. id, 팀명 : 중복확인 버튼 구현
* 3. validateApplication Form이 false 또는 true를 리턴
* 4. 8월 29일까지 application페이지 값 검증과 서버단 validation 어노테이션 활용 검증 구현
* 5. 등록 api 완성하기
* */

let globalIsValid = true;
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
/*    validateAskContent();*/
    validateEtcDescription();
    return globalIsValid;
}

const validateEtcDescription = () => {
    const elem = $('#recognition-path-ETC-description');
    const elemVal = elem.val();
    let isBlank = elemVal === null || elemVal === ' ' || elemVal === '';
    const feedbackId = `#recognition-path-ETC-description-invalid-feedback`;
    const pattern = '^.{0,30}$';
    const message = '30자 이내로 입력하시기 바랍니다.';


    if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
    if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());


    if(isBlank) {
        const etcCheckbox = $('#recognition-path-ETC');
        if($(etcCheckbox).is(':checked')) {
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


    elem.on('input', (e) => {
        const value = e.target.value;
        let isBlankInput = value === null || value === ' ' || value === '';
        if(pattern) isBlankInput = isBlankInput || !RegExp(pattern).test(value);

        if(isBlankInput) {
            const etcCheckbox = $('#recognition-path-ETC');
            if($(etcCheckbox).is(':checked')) {
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
/*

const validateAskContent = () => {
    const elem = $('#ask-content');
    const elemVal = elem.val();
    let isBlank = false;
    const feedbackId = `#ask-content-invalid-feedback`;
    const pattern = '^((\\r\\n|\\r|\\n)|.){0,500}$';
    const message = '500자 이내로 입력하시기 바랍니다.';

    if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
    if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());


    if(isBlank) {
        console.log('ask-content');
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

}
*/

// notBlank
const notBlank = (elem, message = "", selectOption = false, pattern = "", passwordCheck = false) => {
    // 초기 입력값 검증
    if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
    const elemVal = elem.val();
    let isBlank = elemVal === null || elemVal === ' ' || elemVal === '';
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

    const feedbackId = `#${elem.attr('id')}-invalid-feedback`;

    if(isBlank) {
        // globalIsValid
        invalidInputIdList.push(elem.attr('id'));
        globalIsValid = false;
        if(elem.attr('id') == 'team-name') $('#team-name-duplicate-feedback').text('');
        else if(elem.attr('id') == 'user-id') $('#user-id-duplicate-feedback').text('');
        elem.removeClass('is-valid').addClass('is-invalid');
        $(feedbackId).text(message);
        $(feedbackId).removeClass('d-none').addClass('d-block');
    }
    else {
        elem.removeClass('is-invalid').addClass('is-valid');
        $(feedbackId).removeClass('d-block').addClass('d-none');
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
            if(elem.attr('id') == 'team-name') $('#team-name-duplicate-feedback').text('');
            else if(elem.attr('id') == 'user-id') $('#user-id-duplicate-feedback').text('');
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

    // let password = $('#password');
    // notBlank(password, '영문/숫자/특수기호 포함 9자이상', false, '^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*\\W)(?=\\S+$).{9,20}$');
    //
    // let passwordCheck = $('#password-check');
    // notBlank(passwordCheck, '위 비밀번호와 동일하게 입력하세요.',false, '^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*\\W)(?=\\S+$).{9,20}$', true);

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

    // 인지경로 예외처리..
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

    if(!getRecognitionPathList().length) {
        invalidInputIdList.push('recognition-path-SNS');
        globalIsValid = false;
        $(feedbackId).text(message);
        $(feedbackId).removeClass('d-none').addClass('d-block');
    } else {
        $(feedbackId).removeClass('d-block').addClass('d-none');
    }
    recognitionPathElemList.on('click', (elem) => {
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

const notBlankFile = (elem, message) => {
    const feedbackId = `#${elem.attr('id')}-invalid-feedback`;
    elem.on('input', (e) => {
        const value = e.target.value;
        let isBlankInput = value === null || value === ' ' || value === '';
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
            elem.removeClass('is-valid').addClass('is-invalid');
            $(feedbackId).text(message);
            $(feedbackId).removeClass('d-none').addClass('d-block');
        }
        else {
            elem.removeClass('is-invalid').addClass('is-valid');
            $(feedbackId).removeClass('d-block').addClass('d-none');
        }
    });
}

const validateFilesInfo = () => {
    let copyrightFile = $('#copyright-file');
    notBlankFile(copyrightFile, "저작권 동의서 파일을 선택하세요.");

    let ideaPlanFile = $('#idea-plan-file');
    notBlankFile(ideaPlanFile, "아이디어 기획서 파일을 선택하세요.");

    let ideaSummaryFile = $('#idea-summary-file');
    notBlankFile(ideaSummaryFile, "아이디어 요약서 파일을 선택하세요.");

    let personalInfoFile = $('#personal-info-file');
    notBlankFile(personalInfoFile, "개인정보제공 동의서를 선택하세요.");

    // 파일 용량 제한 처리 : notblank File
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


$(document).ready(()=> validateApplicationForm())
