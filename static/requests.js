
obj = {
    status:200,
    isSuccess:true,
    msg:'Some message about request. May contain data (later)'
}

const getCookie = (name) =>{
    return document.cookie.split('; ').find(_=>_.startsWith(name)).split('=')[1]
}
function getFormData(object) {
    const formData = new FormData();
    Object.keys(object).forEach(key => formData.append(key, object[key]));
    return formData;
}
const addToCart = async (itemId, quantity, callback)=>{
    data = new FormData()
    data.append('item_id', itemId)
    data.append('quantity', quantity)
    settings = {
        method:'POST',
        mode:'same-origin',
        headers:{
            'X-CSRFToken':getCookie('csrftoken')
        },
        body:data
    }
    resp = await fetch('/api/cart/add', settings)
    respText = await resp.text()
    if(callback)
        callback({status:resp.status, isSuccess:resp.ok, msg:respText})
    //console.log(resp.status)
    //console.log(respText)
}
const removeFromCart = async (itemId, callback)=>{
    data = new FormData()
    data.append('item_id', itemId)
    settings = {
        method:'POST',
        mode:'same-origin',
        headers:{
            'X-CSRFToken':getCookie('csrftoken')
        },
        body:data
    }
    resp = await fetch('/api/cart/remove', settings)
    respText = await resp.text()
    if(callback)
        callback({status:resp.status, isSuccess:resp.ok, msg:respText})
    
    
    //console.log(resp.status)
    //console.log(respText)
}