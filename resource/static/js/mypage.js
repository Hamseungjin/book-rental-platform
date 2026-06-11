const printApplication = async () => {

    const preRes = document.querySelector('body').innerHTML;
    let resultHTML = '';
    await $.ajax({
        type: 'GET',
        url: '/alr20/mypage/application/print',
        success: (res) => {
            resultHTML = res;
            document.querySelector('body').innerHTML = resultHTML;
            $('body').removeClass('h-100').addClass('h-auto');
            $('html').removeClass('h-100').addClass('h-auto');
            window.print();
            document.querySelector('body').innerHTML = preRes;
            $('body').removeClass('h-auto').addClass('h-100');
            $('html').removeClass('h-auto').addClass('h-100');
        },
        error: (res) => {
            alert("출력할 수 없습니다.")
        }
    })
}

const deleteApplication = () => {
    const msg = '지원서를 삭제할 경우, 모든 정보가 삭제되며\n지원서를 새로 접수하셔야 합니다.\n\n삭제하시겠습니까?';

    if(window.confirm(msg)) {
        $('#loading-spinner').removeClass('d-none').addClass('d-block');
        $.ajax({
            type: 'POST',
            url: '/alr20/application/delete',
            success: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                alert(res.message);
                window.location.reload();
            },
            error: (res) => {
                $('#loading-spinner').removeClass('d-block').addClass('d-none');
                const errRes = res.responseJSON;
                alert(errRes.message);
            }
        })
    }
}