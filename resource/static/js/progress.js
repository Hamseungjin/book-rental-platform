const changePage = (e) => {
    const currentPath = window.location.pathname;
    const searchList = window.location.search.split('&');
    const nextPageNum = e.target.text;
    const nextUrl = `${currentPath}?page=${nextPageNum}&${searchList[1]}&${searchList[2]}`;
    window.location.href = nextUrl;
}

const changeProgressStatusDirection = (e) => {
    const currentPath = window.location.pathname;
    const sortInfoList = window.location.search.split('&');
    const pageInfo = sortInfoList[0];
    const progressStatusDirection = sortInfoList[1].split(',')[1];
    const totalScoreDirection = sortInfoList[2].split(',')[1];

    const nextURL = `${currentPath}${pageInfo}&sort=progressStatus,${progressStatusDirection === 'desc' ? 'asc' : 'desc'}&sort=totalScore,${totalScoreDirection}`;
    window.location.href = nextURL;
}

const changeTotalScoreDirection = (e) => {
    const currentPath = window.location.pathname;
    const sortInfoList = window.location.search.split('&');
    const pageInfo = sortInfoList[0];
    const progressStatusDirection = sortInfoList[1].split(',')[1];
    const totalScoreDirection = sortInfoList[2].split(',')[1];

    const nextURL = `${currentPath}${pageInfo}&sort=progressStatus,${progressStatusDirection}&sort=totalScore,${totalScoreDirection === 'desc' ? 'asc' : 'desc'}`;
    window.location.href = nextURL;
}

const searchHandler = () => {
    const keyword = $('#keyword').val();
    const searchInfo = window.location.search;

    window.location.href = `/alr20/judge/progress/${keyword}${searchInfo}`;
}

const downloadExcel = () => {
    const userId = document.querySelector("#userId").value;

    window.location = '/alr20/judge/excelDownload/' + userId;
}

$(document).ready(() => {
    const sortInfoList = window.location.search.split('&');
    const progressStatusDirection = sortInfoList[1].split(',')[1];
    const totalScoreDirection = sortInfoList[2].split(',')[1];

    if(progressStatusDirection === 'desc') $('#progressStatus-direction-asc').remove();
    else if(progressStatusDirection === 'asc') $('#progressStatus-direction-desc').remove();
    else window.location.href = '/alr20/judge/progress?page=1&sort=progressStatus,asc&sort=totalScore,desc';

    if(totalScoreDirection === 'desc') $('#totalScore-direction-asc').remove();
    else if(totalScoreDirection === 'asc') $('#totalScore-direction-desc').remove();
    else window.location.href = '/alr20/judge/progress?page=1&sort=progressStatus,asc&sort=totalScore,desc';

    const currentPath = window.location.pathname;
    let keyword;
    if(currentPath !== '/alr20/judge/progress') {
        keyword = currentPath.replace('/alr20/judge/progress/', '');
        $('#keyword').val(keyword);
    }

})