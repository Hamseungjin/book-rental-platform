let teamNameDuplicateCheckStatus = 'INCOMPLETE'; // INCOMPLETE, INPROGRESS, COMPLETE
let idDuplicateCheckStatus = 'INCOMPLETE';

const duplicateCheckTeamName = () => {
    let userInput = $('#team-name').val();
    const feedbackElem = $('#team-name-duplicate-feedback');

    teamNameDuplicateCheckStatus = 'INPROGRESS';
    feedbackElem.text('중복확인중입니다...');
    feedbackElem.removeClass('valid-feedback').addClass('invalid-feedback');
    $('#team-name').removeClass('is-valid').addClass('is-invalid');
    $.ajax({
        type: 'GET',
        url: `/alr20/application/duplicate-check/teamname?teamname=${userInput}`,
        // beforeSend: function(xhr){
        //     xhr.setRequestHeader(header, token);
        // },
        contentType: 'charset=utf-8',
        cache: false,
        success: (res) => {
            teamNameDuplicateCheckStatus = 'COMPLETE';
            feedbackElem.text('사용가능한 팀명입니다.');
            feedbackElem.removeClass('invalid-feedback').addClass('valid-feedback');
            $('#team-name').removeClass('is-invalid').addClass('is-valid');
            $('#team-name-invalid-feedback').removeClass('d-block').addClass('d-none');
        },
        error: (res) => {
            teamNameDuplicateCheckStatus = 'INCOMPLETE';
            globalIsValid = false;
            feedbackElem.text('이미 사용중인 팀명입니다.');
            feedbackElem.removeClass('valid-feedback').addClass('invalid-feedback');
            $('#team-name').removeClass('is-valid').addClass('is-invalid');
            // $('#team-name-invalid-feedback').removeClass('d-none').addClass('d-block');
        }
    })

}

const duplicateCheckId = () => {
    let userInput = $('#user-id').val();
    const feedbackElem = $('#user-id-duplicate-feedback');

    idDuplicateCheckStatus = 'INPROGRESS';
    feedbackElem.text('중복확인중입니다...');
    feedbackElem.removeClass('valid-feedback').addClass('invalid-feedback');
    $('#user-id').removeClass('is-valid').addClass('is-invalid');
    $.ajax({
        type: 'GET',
        url: `/alr20/application/duplicate-check/id?id=${userInput}`,
        // beforeSend: function(xhr){
        //     xhr.setRequestHeader(header, token);
        // },
        contentType: 'charset=utf-8',
        cache: false,
        success: (res) => {
            idDuplicateCheckStatus = 'COMPLETE';
            feedbackElem.text('사용가능한 ID입니다.');
            feedbackElem.removeClass('invalid-feedback').addClass('valid-feedback');
            $('#user-id').removeClass('is-invalid').addClass('is-valid');
            $('#user-id-invalid-feedback').removeClass('d-block').addClass('d-none');
        },
        error: (res) => {
            idDuplicateCheckStatus = 'INCOMPLETE';
            globalIsValid = false;
            feedbackElem.text('이미 사용중인 ID입니다.');
            feedbackElem.removeClass('valid-feedback').addClass('invalid-feedback');
            $('#user-id').removeClass('is-valid').addClass('is-invalid');
            // $('#user-id-invalid-feedback').removeClass('d-none').addClass('d-block');
        }
    })
}