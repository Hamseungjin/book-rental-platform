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
        password: $('#password').val(),
        passwordCheck: $('#password-check').val(),
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
/*        askContent: $('#ask-content').val(),
        participantMotivation: $('#participant-motivation').val(),*/
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
    ideaPlanFileInfo:    null,
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


    // 각 파일 input 에 대해 메타 정보를 먼저 채우고, 파일 자체를 FormData 에 넣는다.
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
     /* ② JSON 파트 ------------------------------------------------- */
    // makePayload() 로 메타데이터를 포함한 전체 JSON 객체 생성
    const payload ={
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
    const consentMetaBlob = new Blob([JSON.stringify(consentMeta)],
        {type: 'application/json'});
    formData.append('consentMeta', consentMetaBlob);


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
            url: '/alr20/application/register',
            // beforeSend: function(xhr){
            //     xhr.setRequestHeader(header, token);
            // },
            data: formData,
            processData: false,
            contentType: false,
            success: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                alert(res.message);
                window.location.href = "/alr20/";
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

