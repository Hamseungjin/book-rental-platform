const cancelHandler = () => {
    if(confirm("취소하시겠습니까?")) window.location.href='/alr20/main';
}

const goPreviousPage = () => {
    const currentPath = window.location.pathname;
    const searchList = window.location.search.split('&');
    const pageInfo = searchList[0];
    let pageNum = parseInt(pageInfo.substr(-1));

    if(pageNum === 1) window.location.reload();
    else if(pageNum >= 2) {
        let nextURL = '';
        const previousPage = pageNum - 1;
        if(searchList[2]) nextURL = `${currentPath}?page=${previousPage}&${searchList[1]}${searchList[2] && `&${searchList[2]}`}`;
        else nextURL = `${currentPath}?page=${previousPage}&${searchList[1]}`;
        window.location.href = nextURL;
    } else window.location.reload();

}

const goNextPage = () => {
    const currentPath = window.location.pathname;
    const searchList = window.location.search.split('&');
    const pageInfo = searchList[0];
    let pageNum = parseInt(pageInfo.substr(-1));
    const lastPage = parseInt($('.page-check').last().text());

    if(pageNum === lastPage) window.location.reload();
    else if(pageNum < lastPage) {
        let nextURL = '';
        const nextPage = pageNum + 1;
        if(searchList[2]) nextURL = `${currentPath}?page=${nextPage}&${searchList[1]}${searchList[2] && `&${searchList[2]}`}`;
        else nextURL = `${currentPath}?page=${nextPage}&${searchList[1]}`;
        window.location.href = nextURL;
    } else window.location.reload();
}

const goFirstPage = () => {
    const currentPath = window.location.pathname;
    const searchList = window.location.search.split('&');

    let nextURL = '';
    if(searchList[2]) nextURL = `${currentPath}?page=1&${searchList[1]}${searchList[2] && `&${searchList[2]}`}`;
    else nextURL = `${currentPath}?page=1&${searchList[1]}`;

    window.location.href = nextURL;
}

const goLastPage = () => {
    const currentPath = window.location.pathname;
    const searchList = window.location.search.split('&');
    const lastPage = parseInt($('.page-check').last().text());

    let nextURL = '';
    if(searchList[2]) nextURL = `${currentPath}?page=${lastPage}&${searchList[1]}${searchList[2] && `&${searchList[2]}`}`;
    else nextURL = `${currentPath}?page=${lastPage}&${searchList[1]}`;


    window.location.href = nextURL;
}


const addAutoHyphen = (e) => {
    let value = e.target.value;
    value = value.replace(/[^0-9]/g, "");

    let result = [];
    let restNumber = "";

    result.push(value.substr(0, 3));
    restNumber = value.substring(3);

    if (restNumber.length === 7) {
        // 7자리만 남았을 때는 xxx-yyyy
        result.push(restNumber.substring(0, 3));
        result.push(restNumber.substring(3));
    } else {
        result.push(restNumber.substring(0, 4));
        result.push(restNumber.substring(4));
    }

    e.target.value = result.filter((val) => val).join("-");
}