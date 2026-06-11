const login = (e) => {
    e.preventDefault();

    let data = $('#login-form').serialize();

    $('#loading-spinner').removeClass('d-none').addClass('d-block');
    $.ajax({
        type: 'POST',
        url: '/alr20/login',
        // beforeSend: function(xhr){
        //     xhr.setRequestHeader(header, token);
        // },
        dataType: "json",
        contentType: 'application/x-www-form-urlencoded; charset=utf-8',
        data: data,
        cache: false,
        success: (res) => {
            $('#loading-spinner').removeClass('d-block').addClass('d-none');
            window.location.href = "/alr20/mypage/application";
        },
        error: (res) => {
            $('#loading-spinner').removeClass('d-block').addClass('d-none');
            const errRes = res.responseJSON;
            alert(errRes.message);
        }
    })
}