const collection = document.getElementsByClassName("slider");
document.documentElement.style.setProperty('--slider-counter', (collection.length + 1).toString());

console.log(document.documentElement.style.getPropertyValue('--slider-counter'))



function square() {
    const batch = parseFloat($("#batch").val());
    const len = parseFloat($("#len").val());
    const pageCount = Math.ceil(len/batch);
    let pageIndexMod = 0;

    var p = 1;
const params = new URLSearchParams(window.location.search);
if(params.has('p')){
    p = params.get('p');
    console.log(p);
}
const pageIndexer = $("#page-indexer");

    if(p > 3)
    {
        if(pageCount - p <= 2)
        {
            pageIndexMod = p - 3 + (pageCount - p) - 2;
            console.log((pageCount - p), '<2', pageIndexMod);
        }
        else
        {
            pageIndexMod = p - 3;
        }
    }

    if(pageCount <= 5)
    {
        for(let i = 1 + pageIndexMod; i <= pageCount; i++)
        {
            const a = document.createElement('a');
            a.innerHTML = i.toString();
            a.setAttribute('href', window.location.href.split('?')[0] + '?p=' + i)
            if(p == i) a.setAttribute('class', 'active');
            pageIndexer.append(a);
        }
    }
    else{
        
        for(let i = 1 + pageIndexMod; i <= 5 + pageIndexMod; i++)
        {
            const a = document.createElement('a');
                a.innerHTML = i.toString();
                a.setAttribute('href', window.location.href.split('?')[0] + '?p=' + i)
                if(p == i) a.setAttribute('class', 'active');
                pageIndexer.append(a);
        }
    }
}
square();
  