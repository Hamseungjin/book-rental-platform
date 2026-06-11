const pathArray = window.location.pathname.split('/');
const teamId = pathArray[pathArray.length - 1];
let isValidEvaluationOpinion = true;


const changePage = (e) => {
    const currentPath = window.location.pathname;
    const serachList = window.location.search.split('&');
    const sortInfo = serachList[serachList.length-1];
    const nextPageNum = e.target.text;
    window.location.href = `${currentPath}?page=${nextPageNum}&${sortInfo}`;
}

const changeDirection = (e) => {
    const temp = window.location.search.split(',');
    const currentDirection = temp[temp.length-1];
    const currentPath = window.location.pathname;
    const searchList = window.location.search.split(',');
    const searchInfo = searchList[0];

    if(currentDirection === 'desc') window.location.href = `${currentPath}${searchInfo},asc`;
    else if(currentDirection === 'asc') window.location.href = `${currentPath}${searchInfo},desc`;
    else window.location.href = `${currentPath}?page=1&sort=totalScore,desc`;
}


const setEvaluationIndicators = (domIdList) => {
    for(let i=0; i<domIdList.length; i++) {
        const indicatorElem = document.getElementById(domIdList[i]);
        if(indicatorElem) {
            indicatorElem.checked = true;
        }
    }
}

const setEvaluationTable = () => {
    $.ajax({
        type: 'GET',
        url: `/alr20/judge/evaluation/${teamId}/score`,
        // beforeSend: function(xhr){
        //     xhr.setRequestHeader(header, token);
        // },
        contentType: 'charset=utf-8',
        cache: false,
        success: (res) => {
            setEvaluationIndicators(res.data);
        },
        error: (res) => {

        }
    })
}

const getEvaluationScore = (radioInput) => {
    const score = radioInput.value;
    const idArray = radioInput.id.split('-');

    return {
        evaluationItemId: parseInt(idArray[1]),
        evaluationIndicatorId: parseInt(idArray[2]),
        radioIndex: parseInt(idArray[3]),
        score: parseFloat(score)
    };
}

const getEvaluationScoreInfoList = () => {

    let result = [];

    const inputList = $(`[id^=${teamId}]`);
    for(let i = 0; i<inputList.length; i++) {
        const radioInput = inputList[i];
        if(radioInput.checked) result.push(getEvaluationScore(radioInput));
    }

    return result;
}

const saveScore = async (e) => {
    e.preventDefault();

    isValidEvaluationOpinion = true;
    await validateEvaluationOpinion();

    if(!isValidEvaluationOpinion) {
        alert("평가 의견 : 500자 이내로 입력하세요.");
        return ;
    }

    let data = {
        evaluationOpinion: $('#evaluation-opinion').val().replace(/(?:\r\n|\r|\n)/g, '<br>'),
        evaluationScoreInfoList: getEvaluationScoreInfoList()
    }

    $('#loading-spinner').removeClass('d-none').addClass('d-block');
    $.ajax({
        type: 'POST',
        url: `/alr20/judge/evaluation/${teamId}/score`,
        // beforeSend: function(xhr){
        //     xhr.setRequestHeader(header, token);
        // },
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(data),
        cache: false,
        success: (res) => {
            $('#loading-spinner').removeClass('d-block').addClass('d-none');
            alert("평가표가 저장되었습니다.");
            window.location.reload();
        },
        error: (res) => {
            $('#loading-spinner').removeClass('d-block').addClass('d-none');
            const errRes = res.responseJSON;
            alert(errRes.message);
        }
    })
}

const validateEvaluationOpinion = () => {
    const elem = $('#evaluation-opinion');
    let isBlank = false;
    const feedbackId = `#evaluation-opinion-invalid-feedback`;
    const pattern = '^((\\r\\n|\\r|\\n)|.){0,500}$';
    const message = '500자 이내로 입력하시기 바랍니다.';


    if(elem.attr('type') !== 'file') elem.val($.trim(elem.val()));
    if(pattern) isBlank = isBlank || !RegExp(pattern).test(elem.val());

    if(isBlank) {
        isValidEvaluationOpinion = false;
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
            isValidEvaluationOpinion = false;
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

$(document).ready(()=> {
    setEvaluationTable();
    const temp = window.location.search.split(',');
    const currentDirection = temp[temp.length-1];
    const currentPath = window.location.pathname;
    if(currentDirection === 'desc') $('#direction-asc').remove();
    else if(currentDirection === 'asc') $('#direction-desc').remove();
    else window.location.href = `${currentPath}?page=1&sort=totalScore,desc`;

    validateEvaluationOpinion();
})