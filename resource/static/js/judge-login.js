const judgeLogin = (e) => {
    e.preventDefault();

    let data = $('#judge-login-form').serialize();
    $('#loading-spinner').removeClass('d-none').addClass('d-block');
    $.ajax({
        type: 'POST',
        url: '/alr20/judge/login',
        // beforeSend: function(xhr){
        //     xhr.setRequestHeader(header, token);
        // },
        dataType: "json",
        contentType: 'application/x-www-form-urlencoded; charset=utf-8',
        data: data,
        cache: false,
        success: (res) => {
            $('#loading-spinner').removeClass('d-block').addClass('d-none');
            window.location.href = "/alr20/judge/confirm";
        },
        error: (res) => {
            $('#loading-spinner').removeClass('d-block').addClass('d-none');
            const errRes = res.responseJSON;
            console.log(errRes);
            alert(errRes.message);
        }
    })
}